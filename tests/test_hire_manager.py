"""Phase 3R.5: Hire manager correctness and sequential simulation tests."""
from __future__ import annotations
import sys
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot.state import parse_state, GameState, FarmState, PrivateState  # noqa: E402
from kaggriculture_bot import hire_manager as H  # noqa: E402
from kaggriculture_bot import tasks as T  # noqa: E402


def test_fibonacci_hire_costs():
    """Assert Fibonacci cost step-up: 1, 1, 2, 3, 5, 8... scaled by mult."""
    costs = [H.next_hire_cost(i, mult=1) for i in range(7)]
    assert costs == [1, 1, 2, 3, 5, 8, 13]
    
    # default mult is 1 verified
    assert H.next_hire_cost(5) == 8


def test_sequential_diminishing_returns():
    """Asserts that as we simulate more hands, marginal utility decreases

    (diminishing returns) and sequential planning successfully halts.
    """
    env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
    env.run(["pass", "pass"])
    gs = parse_state(env.state[0].observation)

    # Put farmer at (2,2); 0 hands on-disk.
    # Hand cost: hires_today=0 -> cost=1, then 1, 2, 3, 5, 8...
    # Give enough money so cash gate doesn't fail ($1000, reserve=400).
    custom_self = FarmState(
        player=0, money=1000.0, farmer=(2, 2), hands=(),
        unlocked_quadrants=("NW",), hires_today=0, tiles=gs.self_farm.tiles
    )
    custom_gs = GameState(
        step=3, day=0, hour=3, self_farm=custom_self, opponent_farm=gs.opponent_farm,
        market=gs.market, private=gs.private, town_shops=()
    )

    # We give exactly 4 hours left for hands (hour = 19; current hours_left = 5).
    # Farmer at (2,2), starts at hour 19.
    custom_self = FarmState(
        player=0, money=1000.0, farmer=(2, 2), hands=(),
        unlocked_quadrants=("NW",), hires_today=0, tiles=gs.self_farm.tiles
    )
    custom_gs = GameState(
        step=19, day=0, hour=19, self_farm=custom_self, opponent_farm=gs.opponent_farm,
        market=gs.market, private=gs.private, town_shops=()
    )

    # task1 at (1,1) (dist 2) -> farmer can reach & complete in 3 steps (finished by hour 22).
    # task2 at (3,3) (dist 2 from spawn (4,4)) -> hand starts at (4,4), reaches in 2 steps, finishes in 3 steps (finished by hour 23).
    # Farmer alone: starts at (2,2), goes to (1,1) (3 steps, hour 22).
    # If he then tries to go to (3,3): dist is 4 steps, requires 5 steps total -> finished at hour 27 (impossible, day ends at 23).
    # So Farmer alone value = 500.0.
    # With 1 hand (at 4,4): hand completes task2 (400.0) within 3 steps. Total value = 900.0.
    # Marginal = +400.0 > cost (fib(0)=1 + penalty=10 = 11) -> 1 Hire approved.
    # Second hand starts at (4,4) but there are NO MORE tasks -> marginal = 0.0 -> Hires halt.
    task1 = T.Task("t1", T.TASK_HARVEST, (1, 1), T.TIER_HARVEST_HIGH, 23, 500.0)
    task2 = T.Task("t2", T.TASK_HARVEST, (3, 3), T.TIER_HARVEST_HIGH, 23, 400.0)
    
    planned_hires = H.plan_hires(custom_gs, [task1, task2], max_hands=6, coordination_penalty=10.0, cash_reserve=400)
    
    assert planned_hires == 1, f"expected exactly 1 planned hire, got {planned_hires}"


def test_too_late_in_day_no_hires():
    """Assert no hands hired during late hours of the day (no amortization time)."""
    env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
    env.run(["pass", "pass"])
    gs = parse_state(env.state[0].observation)

    # Late hour: hour 21 (only 3 hours left in day: 21, 22, 23)
    late_self = FarmState(
        player=0, money=1000.0, farmer=(2, 2), hands=(),
        unlocked_quadrants=("NW",), hires_today=0, tiles=gs.self_farm.tiles
    )
    late_gs = GameState(
        step=21, day=0, hour=21, self_farm=late_self, opponent_farm=gs.opponent_farm,
        market=gs.market, private=gs.private, town_shops=()
    )

    task1 = T.Task("t1", T.TASK_HARVEST, (2, 3), T.TIER_HARVEST_HIGH, 23, 500.0)
    planned = H.plan_hires(late_gs, [task1], max_hands=6)
    assert planned == 0, f"expected 0 hires planned late in the day, got {planned}"
