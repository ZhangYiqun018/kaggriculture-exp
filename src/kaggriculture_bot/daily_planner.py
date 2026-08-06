"""Daily Planner (Stage v060).

Manages lightweight DailyPlan containing active_tiles, crop_plan, target_hands,
land_orders, and cash_reserve. Supports multi-quadrant expansion (NE/SW) and max hands (13).
"""
from __future__ import annotations
from dataclasses import dataclass

from .state import GameState
from .constants import CROPS
from .crop_allocator import get_crop_plan

PASTURE_TILES = [(3, 4), (4, 3), (3, 3), (2, 4)]


@dataclass
class DailyPlan:
    active_tiles: list[tuple[int, int]]
    crop_plan: dict[tuple[int, int], str]
    target_hands: int
    land_orders: list[list]
    cash_reserve: int


def compute_daily_plan(gs: GameState, include_strawberry: bool = True, include_land: bool = True,
                       include_livestock: bool = False) -> DailyPlan:
    day = gs.day
    money = gs.self_farm.money
    unlocked = gs.self_farm.unlocked_quadrants

    nearest_16 = [
        (3, 4), (4, 3), (2, 4), (3, 3), (4, 2), (1, 4), (2, 3), (3, 2),
        (4, 1), (0, 4), (1, 3), (2, 2), (3, 1), (4, 0), (0, 3), (1, 2)
    ]
    all_nw = [(x, y) for y in range(5) for x in range(5) if (x, y) != (4, 4)]

    if day >= 4 and money >= 1200:
        active_tiles = list(all_nw)
    else:
        active_tiles = list(nearest_16)

    if "NE" in unlocked:
        ne_tiles = [(x, y) for y in range(5) for x in range(5, 10) if (x, y) != (5, 4)]
        active_tiles = active_tiles + ne_tiles

    if "SW" in unlocked:
        sw_tiles = [(x, y) for y in range(5, 10) for x in range(5) if (x, y) != (4, 5)]
        active_tiles = active_tiles + sw_tiles

    if "SE" in unlocked:
        se_tiles = [(x, y) for y in range(5, 10) for x in range(5, 10) if (x, y) != (5, 5)]
        active_tiles = active_tiles + se_tiles

    land_orders = []
    cash_reserve = 400

    if include_land:
        if "NE" not in unlocked:
            if 11 <= day <= 20 and money >= 2500:
                land_orders.append(["BUY_LAND"])
                cash_reserve = 600
        elif "SW" not in unlocked:
            if 13 <= day <= 20 and money >= 4000:
                land_orders.append(["BUY_LAND"])
                cash_reserve = 800

    n_tiles = len(active_tiles)
    if n_tiles <= 16:
        target_hands = 6
    elif n_tiles <= 25:
        target_hands = 8
    elif n_tiles <= 50:
        target_hands = 11
    else:
        target_hands = 13

    # 4. Generate CropPlan
    farm = gs.self_farm
    empty_tiles = [tile for tile in active_tiles if farm.tile(tile[0], tile[1]).empty]

    if include_livestock:
        empty_tiles = [t for t in empty_tiles if t not in PASTURE_TILES]

    # Full competitive crops pool (WHEAT, CARROT, MELON, TOMATO, STRAWBERRY)
    crops_pool = ["WHEAT", "CARROT", "MELON"]
    if include_strawberry:
        crops_pool.append("STRAWBERRY")
        crops_pool.append("TOMATO")

    crop_plan = get_crop_plan(gs, empty_tiles, crops_pool=crops_pool)

    return DailyPlan(
        active_tiles=active_tiles,
        crop_plan=crop_plan,
        target_hands=target_hands,
        land_orders=land_orders,
        cash_reserve=cash_reserve
    )
