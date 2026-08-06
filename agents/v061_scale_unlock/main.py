"""v061_scale_unlock: livestock farmer-mode + pipeline bug fixes.

Changes from v060:
- Livestock ENABLED with fixed pipeline:
  - PASTURE_TILES excluded from crop_plan (was planted over)
  - COW/SHEEP never sold from shed (was instantly sold)
  - Wheat buffer only when animals ON pastures (was filling shed)
  - Farmer dedicated to livestock setup when animals need placing:
    1. If carrying animal → move to nearest empty pasture → PLACE
    2. If at shed and shed has animal → PICKUP
    3. If PASTURE_TILE is empty/weed → BUILD_PASTURE (or DIG first)
  - BUILD_PASTURE priority raised to TIER_DECAY
  - PICKUP priority raised to TIER_HARVEST_HIGH
- v060 land/hands/reserve parameters preserved
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.constants import CROPS, BOARD_SIZE  # noqa: E402
from kaggriculture_bot.daily_planner import compute_daily_plan, PASTURE_TILES  # noqa: E402
from kaggriculture_bot.tasks import generate_tasks  # noqa: E402
from kaggriculture_bot.assignment import greedy_assign  # noqa: E402
from kaggriculture_bot.policy import plan_market_orders  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402
from kaggriculture_bot.harness import make_agent, hand_count_from_obs  # noqa: E402

INCLUDE_STRAWBERRY = True
INCLUDE_LAND = True
INCLUDE_LIVESTOCK = True

SHED_TILES = [
    (BOARD_SIZE // 2 - 1, BOARD_SIZE // 2 - 1),  # (4,4)
    (BOARD_SIZE // 2, BOARD_SIZE // 2 - 1),      # (5,4)
    (BOARD_SIZE // 2 - 1, BOARD_SIZE // 2),      # (4,5)
    (BOARD_SIZE // 2, BOARD_SIZE // 2),           # (5,5)
]

_EP = {}


def _reset_episode_state():
    global _EP
    _EP = {}


def _move_toward(pos, target):
    fx, fy = pos
    tx, ty = target
    if fx < tx:
        return ["EAST"]
    if fx > tx:
        return ["WEST"]
    if fy < ty:
        return ["SOUTH"]
    if fy > ty:
        return ["NORTH"]
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


def _find_hungry_animal(farm):
    """Find the nearest animal that needs feeding."""
    best, best_d = None, 999
    for px, py in PASTURE_TILES:
        t = farm.tile(px, py)
        if t.animal_kind and not t.animal_fed_today:
            d = 0  # distance computed by caller
            return (px, py)
    return None


def _find_collectable_fertilizer(farm):
    for px, py in PASTURE_TILES:
        t = farm.tile(px, py)
        if t.animal_kind and t.fertilizer_available:
            return (px, py)
    return None


def _farmer_livestock_action(gs):
    """If farmer should be doing livestock work, return the action. Else None."""
    farm = gs.self_farm
    shed = gs.private.shed
    farmer_pos = farm.farmer
    farmer_inv = gs.private.inventories[0] if gs.private.inventories else {}

    carrying_cow = farmer_inv.get("COW", 0) > 0
    carrying_sheep = farmer_inv.get("SHEEP", 0) > 0
    carrying_wheat = farmer_inv.get("WHEAT", 0) > 0
    carrying_fert = farmer_inv.get("FERTILIZER", 0) > 0

    # 0. Carrying wheat → move to hungry animal → FEED
    if carrying_wheat:
        hungry = _find_hungry_animal(farm)
        if hungry is not None:
            if farmer_pos == hungry:
                return ["FEED"]
            return _move_toward(farmer_pos, hungry)

    # 0.5. Carrying fertilizer → move to nearest strawberry → FERTILIZE
    if carrying_fert:
        for y in range(len(farm.tiles)):
            for x in range(len(farm.tiles[y])):
                t = farm.tiles[y][x]
                if t.kind == "PLANT" and t.crop == "STRAWBERRY" and t.fertilized_until_day < gs.day:
                    target = (x, y)
                    if farmer_pos == target:
                        return ["FERTILIZE"]
                    return _move_toward(farmer_pos, target)

    # 1. Carrying animal → move to nearest empty pasture → PLACE
    if carrying_cow or carrying_sheep:
        animal = "COW" if carrying_cow else "SHEEP"
        target = _find_empty_pasture(farm)
        if target is None:
            return ["PASS"]
        if farmer_pos == target:
            return ["PLACE", animal]
        return _move_toward(farmer_pos, target)

    # 1.5. Hungry animals + wheat in shed → go to shed → PICKUP WHEAT
    hungry = _find_hungry_animal(farm)
    if hungry is not None and shed.get("WHEAT", 0) > 0 and not carrying_wheat:
        nearest_shed = _nearest_shed_tile(farmer_pos)
        if farmer_pos == nearest_shed:
            return ["PICKUP", "WHEAT", 1]
        return _move_toward(farmer_pos, nearest_shed)

    # 1.7. Collectable fertilizer → move to animal → COLLECT_FERTILIZER
    fert_tile = _find_collectable_fertilizer(farm)
    if fert_tile is not None:
        if farmer_pos == fert_tile:
            return ["COLLECT_FERTILIZER"]
        return _move_toward(farmer_pos, fert_tile)

    # 2. Animals in shed + empty pastures → go to shed → PICKUP
    shed_cow = shed.get("COW", 0)
    shed_sheep = shed.get("SHEEP", 0)
    empty_pasture = _find_empty_pasture(farm)

    if (shed_cow > 0 or shed_sheep > 0) and empty_pasture is not None:
        animal = "COW" if shed_cow > 0 else "SHEEP"
        nearest_shed = _nearest_shed_tile(farmer_pos)
        if farmer_pos == nearest_shed:
            return ["PICKUP", animal, 1]
        return _move_toward(farmer_pos, nearest_shed)

    # 3. Unbuilt pasture tiles → move there → BUILD_PASTURE (or DIG if weed)
    unbuilt, is_weed = _find_unbuilt_pasture_tile(farm)
    if unbuilt is not None:
        if farmer_pos == unbuilt:
            if is_weed:
                return ["DIG"]
            return ["BUILD_PASTURE"]
        return _move_toward(farmer_pos, unbuilt)

    return None


def _livestock_setup_needed(gs):
    """True if farmer should be dedicated to livestock work."""
    farm = gs.self_farm
    shed = gs.private.shed
    farmer_inv = gs.private.inventories[0] if gs.private.inventories else {}

    if farmer_inv.get("COW", 0) > 0 or farmer_inv.get("SHEEP", 0) > 0:
        return True
    if farmer_inv.get("WHEAT", 0) > 0:
        hungry = _find_hungry_animal(farm)
        if hungry is not None:
            return True
    if farmer_inv.get("FERTILIZER", 0) > 0:
        return True

    # Hungry animals need feeding
    hungry = _find_hungry_animal(farm)
    if hungry is not None and shed.get("WHEAT", 0) > 0:
        return True

    # Collectable fertilizer
    if _find_collectable_fertilizer(farm) is not None:
        return True

    # Animals in shed + empty pastures
    if shed.get("COW", 0) > 0 or shed.get("SHEEP", 0) > 0:
        if _find_empty_pasture(farm) is not None:
            return True

    # Unbuilt pasture tiles
    unbuilt, _ = _find_unbuilt_pasture_tile(farm)
    if unbuilt is not None and (shed.get("COW", 0) > 0 or shed.get("SHEEP", 0) > 0):
        return True
    return False


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

    if INCLUDE_LIVESTOCK and _livestock_setup_needed(gs):
        farmer_action = _farmer_livestock_action(gs)
        if farmer_action is None:
            farmer_action = ["PASS"]
        assignments = greedy_assign(gs, tasks)
        hands_actions = [a.action for a in assignments if a.unit_idx != 0]
    else:
        assignments = greedy_assign(gs, tasks)
        farmer_action = assignments[0].action if assignments else ["PASS"]
        hands_actions = [a.action for a in assignments[1:]]

    market = plan_market_orders(
        gs, tasks,
        max_hands_day=dp.target_hands,
        crop_plan=dp.crop_plan,
        land_orders=dp.land_orders,
        cash_reserve=dp.cash_reserve,
        include_livestock=INCLUDE_LIVESTOCK
    )

    return safe_action(
        raw_farmer=farmer_action,
        raw_hands=hands_actions,
        raw_market=market,
        observed_hand_count=farm.hand_count,
        seeds=seeds,
    )


agent = make_agent(core_agent, observed_hand_count_fn=hand_count_from_obs)
