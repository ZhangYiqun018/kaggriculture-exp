"""Phase 3.3: assignment tests."""
from __future__ import annotations
import sys
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot import tasks as T  # noqa: E402
from kaggriculture_bot import assignment as A  # noqa: E402

MANAGED = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (3, 4)]


def _gs_after(agent_fn, steps, seed=1):
    env = make("kaggriculture", configuration={"episodeSteps": steps + 2, "seed": seed}, debug=True)
    env.run([agent_fn, "pass"])
    return parse_state(env.state[0].observation)


def _buy_seeds_obs(obs, config=None):
    if obs.get("step", 0) == 0:
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 6], ["BUY_SEED", "CARROT", 2], ["BUY_SEED", "MELON", 2]]}
    return {"farmer": ["PASS"], "hands": [], "market": []}


def test_single_unit_assignment_shape():
    gs = _gs_after(_buy_seeds_obs, 3)
    tasks = T.generate_tasks(gs, MANAGED)
    asg = A.greedy_assign(gs, tasks)
    assert len(asg) == 1  # only farmer
    assert asg[0].unit_idx == 0


def test_empty_farm_with_seeds_assigns_plant_forward_move():
    gs = _gs_after(_buy_seeds_obs, 3)
    tasks = T.generate_tasks(gs, MANAGED)
    asg = A.greedy_assign(gs, tasks)
    a = asg[0]
    assert a.action is not None
    # Farmer spawns at (4,4); managed tiles are away. Expect a move or PLANT.
    assert a.action[0] in ("NORTH", "SOUTH", "EAST", "WEST", "PLANT")


def test_no_seeds_no_plant_assignment():
    gs = _gs_after(lambda o, c=None: {"farmer": ["PASS"], "hands": [], "market": []}, 3)
    tasks = T.generate_tasks(gs, MANAGED)
    asg = A.greedy_assign(gs, tasks)
    # No seeds held -> PLANT tasks infeasible -> farmer should PASS (nothing plantable).
    for a in asg:
        if a.task:
            assert a.task.kind != T.TASK_PLANT


def test_dying_plant_water_assigned_first():
    def planter(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        if step == 1:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    gs = _gs_after(planter, 3)
    tasks = T.generate_tasks(gs, MANAGED)
    asg = A.greedy_assign(gs, tasks)
    # Farmer is at (4,4) which has the dying plant; should be assigned WATER.
    a = asg[0]
    assert a.task is not None
    assert a.task.kind == T.TASK_WATER
    assert a.task.priority_tier == T.TIER_DYING
    assert a.action == ["WATER"]


def test_frozen_dataclasses():
    # Assignment and UnitView must be frozen (immutable snapshots, not planner state).
    import pytest
    u = A.UnitView(0, (4, 4), {})
    with pytest.raises(Exception):
        u.idx = 1


def test_multiunit_assignment_exclusivity_and_seed_reservation():
    """Asserts multi-unit correctness on conflicts and budgets (Phase 3R.4)."""
    # Build custom GameState
    env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
    env.run(["pass", "pass"])
    gs = parse_state(env.state[0].observation)

    # 1) Construct multiple units
    # Farmer at (2,2), Hand1 at (2,2)
    from kaggriculture_bot.state import GameState, FarmState, MarketState, PrivateState
    custom_self = FarmState(
        player=0, money=1000.0, farmer=(2, 2), hands=((2, 2),),
        unlocked_quadrants=("NW",), hires_today=0, tiles=gs.self_farm.tiles
    )
    # 2) Put exactly 1 WHEAT seed in private state
    custom_private = PrivateState(
        shed={}, seeds={"WHEAT": 1}, inventories=({}, {})
    )
    custom_gs = GameState(
        step=3, day=0, hour=3, self_farm=custom_self, opponent_farm=gs.opponent_farm,
        market=gs.market, private=custom_private, town_shops=()
    )

    # 3) Generate two PLANT WHEAT tasks targeting the same tile (2,2) or nearby
    task1 = T.Task("t1", T.TASK_PLANT, (2, 2), T.TIER_PLANT, 23, 100.0, crop="WHEAT")
    task2 = T.Task("t2", T.TASK_PLANT, (3, 2), T.TIER_PLANT, 23, 90.0, crop="WHEAT")
    
    # 4) Greedy assign
    asg = A.greedy_assign(custom_gs, [task1, task2])
    
    # Assertions:
    assert len(asg) == 2  # unit 0 (farmer) and unit 1 (hand)
    # Unit 0 should claim task1 (highest profit) and plant
    assert asg[0].unit_idx == 0
    assert asg[0].task == task1
    assert asg[0].action == ["PLANT", "WHEAT"]
    
    # Unit 1 must NOT be assigned task2 because planting task1 consumed our ONLY WHEAT seed.
    # Seed budget reservation must work inside the assignment loop.
    assert asg[1].unit_idx == 1
    assert asg[1].task is None
    assert asg[1].action == ["PASS"]


def test_target_tile_exclusivity():
    """Asserts that at most one unit is assigned to any given tile coordinates."""
    env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
    env.run(["pass", "pass"])
    gs = parse_state(env.state[0].observation)

    from kaggriculture_bot.state import GameState, FarmState, PrivateState
    custom_self = FarmState(
        player=0, money=1000.0, farmer=(2, 2), hands=((2, 2),),
        unlocked_quadrants=("NW",), hires_today=0, tiles=gs.self_farm.tiles
    )
    custom_private = PrivateState(
        shed={}, seeds={"WHEAT": 5, "CARROT": 5}, inventories=({}, {})
    )
    custom_gs = GameState(
        step=3, day=0, hour=3, self_farm=custom_self, opponent_farm=gs.opponent_farm,
        market=gs.market, private=custom_private, town_shops=()
    )

    # Two tasks targeting exactly same tile (2,2) (e.g. PLANT WHEAT and PLANT CARROT)
    task1 = T.Task("t1", T.TASK_PLANT, (2, 2), T.TIER_PLANT, 23, 100.0, crop="WHEAT")
    task2 = T.Task("t2", T.TASK_PLANT, (2, 2), T.TIER_PLANT, 23, 90.0, crop="CARROT")

    asg = A.greedy_assign(custom_gs, [task1, task2])
    
    # Farmer (0) claims task1. Hand (1) cannot claim task2 because (2,2) has a conflict lock.
    assert asg[0].task == task1
    assert asg[1].task is None
    assert asg[1].action == ["PASS"]
