"""Hire manager: marginal-value decision for farm hands.

A hand is a same-day-only worker: spawned next turn, vanishes at end of day,
costs fib(hires_today)*mult. The decision is just marginal NPV:

    value_of_tasks_a_new_hand_can_complete_today
        - next_hire_cost
        - coordination_penalty

> 0 -> HIRE.
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
    """Engine spawns hands on the least-occupied NW shed-access tile. Whatever
    it picks, the hand starts adjacent to the shed; use (4,4) as a close-enough
    start point for the marginal simulation."""
    half = BOARD_SIZE // 2
    return (half - 1, half - 1)


def _day_completion_value(gs: GameState, tasks: list[Task], start_positions: list[tuple[int, int]],
                          hours_left: int) -> float:
    """Greedy same-day simulation: each hour, every free unit takes the nearest
    unclaimed task; task completes after travel + 1 hour of work. Returns total
    expected_value of tasks that complete today. Deterministic."""
    ordered = sorted([t for t in tasks if t.target is not None],
                     key=lambda t: (t.priority_tier, -t.expected_value))
    claimed: dict[str, int] = {}  # task_id -> finish hour
    # unit free-hour timeline
    free_at = [0] * len(start_positions)
    pos = list(start_positions)
    total = 0.0
    for t in ordered:
        best_i, best_finish = -1, 1_000_000
        for i in range(len(pos)):
            d = abs(pos[i][0] - t.target[0]) + abs(pos[i][1] - t.target[1])
            finish = free_at[i] + d + 1
            if finish < best_finish:
                best_i, best_finish = i, finish
        if best_i < 0:
            continue
        if best_finish <= hours_left:
            claimed[t.task_id] = best_finish
            total += t.expected_value
            free_at[best_i] = best_finish
            pos[best_i] = t.target
    return total


def should_hire(gs: GameState, tasks: list[Task],
                coordination_penalty: float = 0.0,
                cash_reserve: int = 200) -> bool:
    """True iff hiring one more hand is profitable today."""
    farm = gs.self_farm
    hour = gs.hour
    hours_left = TURNS_PER_DAY - hour  # hours remaining INCLUDING current turn
    if hours_left <= 1:
        return False  # last hour: hand has no future action value
    if hours_left < 5:
        return False  # too little day left to amortize anything

    n_units = 1 + farm.hand_count
    cost = next_hire_cost(farm.hires_today)
    if farm.money - cost < cash_reserve:
        return False

    unit_positions = [farm.farmer] + list(farm.hands)
    base_value = _day_completion_value(gs, tasks, unit_positions, hours_left)
    phantom = unit_positions + [_spawn_pos(gs)]
    with_hand_value = _day_completion_value(gs, tasks, phantom, hours_left)
    marginal = with_hand_value - base_value
    return marginal > cost + coordination_penalty
