"""Phase 3.2: task system tests."""
from __future__ import annotations
import sys
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot import tasks as T  # noqa: E402

MANAGED = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (3, 4)]


def _gs_after(agent_fn, steps, seed=1):
    env = make("kaggriculture", configuration={"episodeSteps": steps + 2, "seed": seed}, debug=True)
    env.run([agent_fn, "pass"])
    return parse_state(env.state[0].observation)


def _pass_agent(obs, config=None):
    return {"farmer": ["PASS"], "hands": [], "market": []}


def _planter(obs, config=None):
    """Buy 1 WHEAT, plant it on (4,4) on step 1, then pass."""
    step = obs.get("step", 0)
    if step == 0:
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
    if step == 1:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
    return _pass_agent(obs)


def test_empty_farm_generates_plant_tasks():
    gs = _gs_after(_pass_agent, 3)
    ts = T.generate_tasks(gs, MANAGED)
    plants = [t for t in ts if t.kind == T.TASK_PLANT]
    assert len(plants) == len(MANAGED) * 3  # 3 crops (WHEAT/CARROT/MELON) per tile at day 0
    assert all(t.priority_tier == T.TIER_PLANT for t in plants)
    assert all(t.deadline_step == 23 for t in plants)  # end of day 0


def test_day25_no_melon_plant():
    env = make("kaggriculture", configuration={"episodeSteps": 25 * 24 + 3, "seed": 1}, debug=True)
    env.run([_pass_agent, _pass_agent])
    gs = parse_state(env.state[0].observation)
    gs_day = gs.day
    assert gs_day >= 25
    ts = T.generate_tasks(gs, MANAGED)
    plants = [t for t in ts if t.kind == T.TASK_PLANT]
    crops = {t.crop for t in plants}
    assert "MELON" not in crops
    assert "WHEAT" in crops


def test_planted_tile_generates_water():
    gs = _gs_after(_planter, 4)
    ts = T.generate_tasks(gs, MANAGED)
    waters = [t for t in ts if t.kind == T.TASK_WATER]
    # (4,4) is not in MANAGED but water tasks are generated for ALL plants.
    assert len(waters) >= 1
    w = waters[0]
    assert w.target == (4, 4)
    # consecutive_unwatered = 1 (planting day counts) -> dying this turn if unwatered.
    assert w.priority_tier == T.TIER_DYING


def test_watered_today_no_water_task():
    def waterer(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        if step == 1:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
        if step == 2:
            return {"farmer": ["WATER"], "hands": [], "market": []}
        return _pass_agent(obs)

    gs = _gs_after(waterer, 5)
    ts = T.generate_tasks(gs, MANAGED)
    # After watering at step 2 (still day 0), no water task for the (4,4) plant.
    waters = [t for t in ts if t.kind == T.TASK_WATER and t.target == (4, 4)]
    assert len(waters) == 0


def test_harvest_task_when_mature():
    def harvester(obs, config=None):
        step = obs.get("step", 0)
        day = obs.get("day", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        if step == 1:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
        return {"farmer": ["WATER"], "hands": [], "market": []}

    # WHEAT first_yield_day=2; by day 2 (step 48+) it should be harvestable.
    gs = _gs_after(harvester, 2 * 24 + 5)
    ts = T.generate_tasks(gs, MANAGED)
    harvests = [t for t in ts if t.kind == T.TASK_HARVEST]
    assert len(harvests) >= 1
    h = harvests[0]
    assert h.crop == "WHEAT"
    assert h.expected_value > 0


def test_drop_task_when_carrying():
    # Weed: dig it to get a carrying-free state; simpler: use starter-like wheat carry.
    # Instead directly build obs where farmer is mid-harvest carry: harvest then check.
    def hc(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        if step == 1:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
        if 2 <= step <= 49:
            return {"farmer": ["WATER"], "hands": [], "market": []}
        if step == 50:  # day 2: harvest
            return {"farmer": ["HARVEST"], "hands": [], "market": []}
        return _pass_agent(obs)

    gs = _gs_after(hc, 52)
    # After harvesting at step 50, farmer carries WHEAT until eod drop.
    unit_inv_total = sum(sum(inv.values()) for inv in gs.private.inventories)
    ts = T.generate_tasks(gs, MANAGED)
    drops = [t for t in ts if t.kind == T.TASK_DROP]
    if unit_inv_total > 0:
        assert len(drops) == 1
    else:
        assert len(drops) == 0


def test_top_tasks_tier_ordering():
    gs = _gs_after(_planter, 4)
    ts = T.generate_tasks(gs, MANAGED)
    top = T.top_tasks(ts, n=5)
    tiers = [t.priority_tier for t in top]
    assert tiers == sorted(tiers)
    # dying WATER (tier 0) should lead the list when present.
    if any(t.priority_tier == T.TIER_DYING for t in ts):
        assert top[0].priority_tier == T.TIER_DYING


def test_task_ids_unique():
    gs = _gs_after(_planter, 4)
    ts = T.generate_tasks(gs, MANAGED)
    ids = [t.task_id for t in ts]
    assert len(ids) == len(set(ids))
