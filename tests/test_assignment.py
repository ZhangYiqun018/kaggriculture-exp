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
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 6], ["BUY_SEED", "CARROT", 2]]}
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
