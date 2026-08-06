"""v062_livestock_os: stable 2C2S livestock operating system.

Fixes from v061:
- greedy_assign supports allowed_unit_ids: hands-only assignment when farmer in livestock mode
- Terminal mode (day >= 29) overrides livestock mode: no FEED/CARE/FERTILIZE/BUILD
- Feed-hand: one designated hand picks up 4 WHEAT, feeds by consecutive_unfed priority
- Animal-care hand: CARE + HARVEST MILK/WOOL + COLLECT_FERTILIZER
- Total-accessible-wheat accounting (shed + all unit inventories)
- Market order sequence: SELL → critical HIRE → emergency feed → BUY_LAND → BUY_ANIMAL → BUY_SEED → extra HIRE
- Exact land costs (1000/2000/4000)
- Livestock capped at 2C2S
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.constants import CROPS, BOARD_SIZE, TURNS_PER_DAY  # noqa: E402
from kaggriculture_bot.daily_planner import compute_daily_plan, PASTURE_TILES  # noqa: E402
from kaggriculture_bot.tasks import generate_tasks  # noqa: E402
from kaggriculture_bot.assignment import greedy_assign, units_from_state  # noqa: E402
from kaggriculture_bot.policy import plan_market_orders  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402
from kaggriculture_bot.harness import make_agent, hand_count_from_obs  # noqa: E402

INCLUDE_STRAWBERRY = True
INCLUDE_LAND = True
INCLUDE_LIVESTOCK = True

SHED_TILES = [
    (BOARD_SIZE // 2 - 1, BOARD_SIZE // 2 - 1),
    (BOARD_SIZE // 2, BOARD_SIZE // 2 - 1),
    (BOARD_SIZE // 2 - 1, BOARD_SIZE // 2),
    (BOARD_SIZE // 2, BOARD_SIZE // 2),
]

LIVESTOCK_TASK_KINDS = {"BUILD_PASTURE", "PICKUP", "PLACE", "FEED", "DIG",
                        "CARE", "COLLECT_FERTILIZER", "FERTILIZE"}
FEED_KINDS = {"FEED"}
CARE_KINDS = {"CARE", "COLLECT_FERTILIZER"}

_EP = {}


def _reset_episode_state():
    global _EP
    _EP = {}


def _move_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    if fx < tx: return ["EAST"]
    if fx > tx: return ["WEST"]
    if fy < ty: return ["SOUTH"]
    if fy > ty: return ["NORTH"]
    return ["PASS"]


def _nearest_shed_tile(pos):
    best, best_d = SHED_TILES[0], 999
    for st in SHED_TILES:
        d = abs(pos[0] - st[0]) + abs(pos[1] - st[1])
        if d < best_d:
            best, best_d = st, d
    return best


def _find_empty_pasture(farm):
    for px, py in PASTURE_TILES:
        t = farm.tile(px, py)
        if t.kind == "PASTURE" and not t.animal_kind:
            return (px, py)
    return None


def _find_unbuilt_pasture_tile(farm):
    for px, py in PASTURE_TILES:
        t = farm.tile(px, py)
        if t.empty or t.is_weed:
            return (px, py), t.is_weed
    return None, False


def _find_hungry_animals(farm):
    result = []
    for px, py in PASTURE_TILES:
        t = farm.tile(px, py)
        if t.animal_kind and not t.animal_fed_today:
            result.append((px, py, t.animal_unfed, t.animal_kind))
    result.sort(key=lambda r: (-r[2], r[0], r[1]))
    return result


def _find_collectable_fertilizer(farm):
    for px, py in PASTURE_TILES:
        t = farm.tile(px, py)
        if t.animal_kind and t.fertilizer_available:
            return (px, py)
    return None


def _find_harvestable_animals(farm):
    result = []
    for px, py in PASTURE_TILES:
        t = farm.tile(px, py)
        if t.animal_kind and t.animal_yield > 0:
            result.append((px, py))
    return result


def _find_uncared_animals(farm):
    result = []
    for px, py in PASTURE_TILES:
        t = farm.tile(px, py)
        if t.animal_kind and not t.animal_cared_today:
            result.append((px, py))
    return result


def _farmer_livestock_action(gs):
    farm = gs.self_farm
    shed = gs.private.shed
    farmer_pos = farm.farmer
    farmer_inv = gs.private.inventories[0] if gs.private.inventories else {}

    carrying_cow = farmer_inv.get("COW", 0) > 0
    carrying_sheep = farmer_inv.get("SHEEP", 0) > 0
    carrying_wheat = farmer_inv.get("WHEAT", 0) > 0
    carrying_fert = farmer_inv.get("FERTILIZER", 0) > 0

    # 0. Carrying fertilizer → fertilize nearest strawberry
    if carrying_fert:
        for y in range(len(farm.tiles)):
            for x in range(len(farm.tiles[y])):
                t = farm.tiles[y][x]
                if t.kind == "PLANT" and t.crop == "STRAWBERRY" and t.fertilized_until_day < gs.day:
                    target = (x, y)
                    if farmer_pos == target:
                        return ["FERTILIZE"]
                    return _move_toward(farmer_pos, target)

    # 1. Carrying animal → place on nearest empty pasture
    if carrying_cow or carrying_sheep:
        animal = "COW" if carrying_cow else "SHEEP"
        target = _find_empty_pasture(farm)
        if target is None:
            return ["PASS"]
        if farmer_pos == target:
            return ["PLACE", animal]
        return _move_toward(farmer_pos, target)

    # 2. Collectable fertilizer → collect
    fert_tile = _find_collectable_fertilizer(farm)
    if fert_tile is not None:
        if farmer_pos == fert_tile:
            return ["COLLECT_FERTILIZER"]
        return _move_toward(farmer_pos, fert_tile)

    # 3. Animals in shed + empty pastures → pickup and place
    shed_cow = shed.get("COW", 0)
    shed_sheep = shed.get("SHEEP", 0)
    empty_pasture = _find_empty_pasture(farm)

    if (shed_cow > 0 or shed_sheep > 0) and empty_pasture is not None:
        animal = "COW" if shed_cow > 0 else "SHEEP"
        nearest_shed = _nearest_shed_tile(farmer_pos)
        if farmer_pos == nearest_shed:
            return ["PICKUP", animal, 1]
        return _move_toward(farmer_pos, nearest_shed)

    # 4. Unbuilt pasture tiles → build
    unbuilt, is_weed = _find_unbuilt_pasture_tile(farm)
    if unbuilt is not None:
        if farmer_pos == unbuilt:
            if is_weed:
                return ["DIG"]
            return ["BUILD_PASTURE"]
        return _move_toward(farmer_pos, unbuilt)

    return None


def _livestock_farmer_needed(gs):
    farm = gs.self_farm
    shed = gs.private.shed
    farmer_inv = gs.private.inventories[0] if gs.private.inventories else {}

    if farmer_inv.get("COW", 0) > 0 or farmer_inv.get("SHEEP", 0) > 0:
        return True
    if farmer_inv.get("FERTILIZER", 0) > 0:
        return True

    if _find_collectable_fertilizer(farm) is not None:
        return True

    if shed.get("COW", 0) > 0 or shed.get("SHEEP", 0) > 0:
        if _find_empty_pasture(farm) is not None:
            return True

    unbuilt, _ = _find_unbuilt_pasture_tile(farm)
    if unbuilt is not None and (shed.get("COW", 0) > 0 or shed.get("SHEEP", 0) > 0):
        return True
    return False


def _feed_hand_action(gs, hand_idx):
    """Feed-hand state machine: PICKUP 4 WHEAT → FEED by priority."""
    farm = gs.self_farm
    shed = gs.private.shed
    units = units_from_state(gs)
    if hand_idx >= len(units):
        return ["PASS"]
    unit = units[hand_idx]
    pos = unit.pos
    inv = unit.inventory

    carrying_wheat = inv.get("WHEAT", 0) > 0

    # If carrying wheat, feed the hungriest reachable animal
    if carrying_wheat:
        hungry = _find_hungry_animals(farm)
        for px, py, unfed, kind in hungry:
            target = (px, py)
            if pos == target:
                return ["FEED"]
            return _move_toward(pos, target)
        # No hungry animals, drop wheat at shed for later
        nearest_shed = _nearest_shed_tile(pos)
        if pos == nearest_shed:
            return ["DROP", "WHEAT", inv.get("WHEAT", 0)]
        return _move_toward(pos, nearest_shed)

    # Not carrying wheat: go to shed and pick up
    hungry = _find_hungry_animals(farm)
    if not hungry:
        return None  # No feeding needed, hand can do other work

    total_wheat = shed.get("WHEAT", 0)
    if total_wheat > 0:
        nearest_shed = _nearest_shed_tile(pos)
        if pos == nearest_shed:
            pickup_qty = min(4, total_wheat)
            return ["PICKUP", "WHEAT", pickup_qty]
        return _move_toward(pos, nearest_shed)

    return None


def _care_hand_action(gs, hand_idx):
    """Animal-care hand: CARE → HARVEST → COLLECT_FERTILIZER."""
    farm = gs.self_farm
    units = units_from_state(gs)
    if hand_idx >= len(units):
        return ["PASS"]
    unit = units[hand_idx]
    pos = unit.pos

    # 1. Harvest animals with yield
    harvestable = _find_harvestable_animals(farm)
    for px, py in harvestable:
        target = (px, py)
        if pos == target:
            return ["HARVEST"]
        return _move_toward(pos, target)

    # 2. CARE for uncared animals
    uncared = _find_uncared_animals(farm)
    for px, py in uncared:
        target = (px, py)
        if pos == target:
            return ["CARE"]
        return _move_toward(pos, target)

    # 3. Collect fertilizer
    fert = _find_collectable_fertilizer(farm)
    if fert is not None:
        if pos == fert:
            return ["COLLECT_FERTILIZER"]
        return _move_toward(pos, fert)

    return None


def core_agent(obs, config=None):
    gs = parse_state(obs)
    if gs.step == 0:
        _reset_episode_state()

    farm = gs.self_farm
    private = gs.private
    seeds = private.seeds

    dp = compute_daily_plan(gs, include_strawberry=INCLUDE_STRAWBERRY, include_land=INCLUDE_LAND,
                            include_livestock=INCLUDE_LIVESTOCK)

    tasks = generate_tasks(
        gs, dp.active_tiles,
        crop_plan=dp.crop_plan,
        include_livestock=INCLUDE_LIVESTOCK
    )

    is_terminal = gs.day >= 29
    farmer_in_livestock = (INCLUDE_LIVESTOCK and not is_terminal and
                           _livestock_farmer_needed(gs))

    if farmer_in_livestock:
        farmer_action = _farmer_livestock_action(gs)
        if farmer_action is None:
            farmer_action = ["PASS"]

        hand_ids = set(range(1, farm.hand_count + 1))
        crop_tasks = [t for t in tasks if t.kind not in LIVESTOCK_TASK_KINDS]

        assignments = greedy_assign(gs, crop_tasks, allowed_unit_ids=hand_ids)

        hands_actions = []
        assigned = {a.unit_idx: a.action for a in assignments}

        feed_hand_idx = 1
        care_hand_idx = 2 if farm.hand_count >= 3 else None

        for idx in range(1, farm.hand_count + 1):
            if idx == feed_hand_idx:
                action = _feed_hand_action(gs, idx)
                if action is not None:
                    hands_actions.append(action)
                    continue
            if care_hand_idx is not None and idx == care_hand_idx:
                action = _care_hand_action(gs, idx)
                if action is not None:
                    hands_actions.append(action)
                    continue
            hands_actions.append(assigned.get(idx, ["PASS"]))
    else:
        assignments = greedy_assign(gs, tasks)
        farmer_action = assignments[0].action if assignments else ["PASS"]
        hands_actions = [a.action for a in assignments if a.unit_idx != 0]

    market = plan_market_orders(
        gs, tasks,
        max_hands_day=dp.target_hands,
        crop_plan=dp.crop_plan,
        land_orders=dp.land_orders,
        cash_reserve=dp.cash_reserve,
        include_livestock=(INCLUDE_LIVESTOCK and not is_terminal)
    )

    return safe_action(
        raw_farmer=farmer_action,
        raw_hands=hands_actions,
        raw_market=market,
        observed_hand_count=farm.hand_count,
        seeds=seeds,
    )


agent = make_agent(core_agent, observed_hand_count_fn=hand_count_from_obs)
