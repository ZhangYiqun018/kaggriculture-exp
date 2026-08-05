"""Hire manager: marginal-value decision for farm hands (repaired in Phase 3R.5).

A hand is a same-day-only worker: spawned next turn, vanishes at end of day,
costs fib(hires_today)*mult.

Repairs:
- Replaced the single heuristic loop with a true sequential sequential-plan
  (`plan_hires`) where each subsequent hand's cost (Fibonacci cost step-up)
  and marginal-value (diminishing return against already-hired hands) are updated.
- Accounts for same-day remaining steps (a hired hand can only act next turn,
  so we exclude the current turn from its capabilities).
"""
from __future__ import annotations

from .constants import TURNS_PER_DAY, FARM_HAND_COST_MULT, BOARD_SIZE
from .state import GameState
from .tasks import Task


def _fib(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def next_hire_cost(hires_today: int, mult: int = FARM_HAND_COST_MULT) -> int:
    return mult * _fib(hires_today)


def _spawn_pos(gs: GameState) -> tuple[int, int]:
    half = BOARD_SIZE // 2
    return (half - 1, half - 1)  # (4,4) NW shed tile adjacent


def _day_completion_value(gs: GameState, tasks: list[Task], start_positions: list[tuple[int, int]],
                          n_existing: int, hours_left_for_hands: int, hours_left_for_current_units: int) -> float:
    """Greedy same-day simulation.

    Different free-hour starting points:
    - current units (farmer + already hired hands) start working CURRENT hour (available_at=0)
    - newly hired hands start working NEXT hour (available_at=1)
    """
    # Exclude mutually exclusive tasks at the same coordinates.
    # We only take the HIGHEST profit task per tile position in the simulation.
    best_on_tile: dict[tuple, Task] = {}
    for t in tasks:
        if t.target is not None:
            pos = t.target
            if pos not in best_on_tile or t.expected_value > best_on_tile[pos].expected_value:
                best_on_tile[pos] = t
    filtered_tasks = list(best_on_tile.values())

    ordered = sorted(filtered_tasks, key=lambda t: (t.priority_tier, -t.expected_value))
    
    # 4. Fix hire_manager new-hand availability:
    # - existing units available_at = 0
    # - every hand planned this turn available_at = 1
    # - actually use availability in finish-time computation.
    available_at = [0] * n_existing + [1] * (len(start_positions) - n_existing)
    free_at = list(available_at)
        
    pos = list(start_positions)
    total = 0.0
    
    # Simple simulator
    for t in ordered:
        if t.target is None:
            continue
        tgt = t.target
        best_i, best_finish = -1, 1_000_000
        for i in range(len(pos)):
            d = abs(pos[i][0] - tgt[0]) + abs(pos[i][1] - tgt[1])
            # Use availability in finish-time computation: max(free_at[i], available_at[i]) is already free_at[i]
            finish = free_at[i] + d + 1
            if finish < best_finish:
                best_i, best_finish = i, finish
                
        if best_i < 0:
            continue
            
        # Limit reachability check based on role
        limit = hours_left_for_hands if best_i >= n_existing else hours_left_for_current_units
        if best_finish <= limit:
            total += t.expected_value
            free_at[best_i] = best_finish
            pos[best_i] = tgt
            
    return total


def plan_hires(gs: GameState, tasks: list[Task], max_hands: int = 6,
               coordination_penalty: float = 10.0, cash_reserve: int = 400) -> int:
    """Return the optimal number of hands to hire THIS TURN via sequential marginal value.

    Simulates the diminishing returns of adding hands step-by-step.
    """
    farm = gs.self_farm
    hour = gs.hour
    hours_left_current = TURNS_PER_DAY - hour
    hours_left_hands = hours_left_current - 1  # new hands act next turn at earliest

    if hours_left_hands < 4:
        return 0  # too late in the day to buy same-day capacity

    planned_hires = 0
    current_money = farm.money
    current_hires_today = farm.hires_today
    current_hands_count = farm.hand_count
    n_existing = 1 + current_hands_count

    # Positions pool for simulation
    unit_positions = [farm.farmer] + list(farm.hands)

    while current_hands_count + planned_hires < max_hands:
        cost = next_hire_cost(current_hires_today + planned_hires)
        if current_money - cost < cash_reserve:
            break

        # Calculate base value with current simulation group
        base_val = _day_completion_value(
            gs, tasks, unit_positions, n_existing,
            hours_left_hands, hours_left_current
        )

        # Append one phantom hand at spawn
        phantom_positions = unit_positions + [_spawn_pos(gs)]
        with_hand_val = _day_completion_value(
            gs, tasks, phantom_positions, n_existing,
            hours_left_hands, hours_left_current
        )

        marginal_value = with_hand_val - base_val
        
        # Diminishing return gate
        if marginal_value > cost + coordination_penalty:
            planned_hires += 1
            current_money -= cost
            unit_positions = phantom_positions  # keep it for the next hand's base
        else:
            break

    return planned_hires


def should_hire(gs: GameState, tasks: list[Task], coordination_penalty: float = 10.0,
                cash_reserve: int = 400) -> bool:
    """True iff sequential simulation recommends hiring at least 1 hand."""
    return plan_hires(gs, tasks, max_hands=1, coordination_penalty=coordination_penalty, cash_reserve=cash_reserve) > 0
