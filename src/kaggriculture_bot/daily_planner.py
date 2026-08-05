"""Daily Planner (Stage v040).

Manages lightweight DailyPlan containing active_tiles, crop_plan, target_hands,
land_orders, and cash_reserve.
"""
from __future__ import annotations
from dataclasses import dataclass

from .state import GameState
from .constants import CROPS
from .crop_allocator import get_crop_plan


@dataclass
class DailyPlan:
    active_tiles: list[tuple[int, int]]
    crop_plan: dict[tuple[int, int], str]
    target_hands: int
    land_orders: list[list]
    cash_reserve: int


def compute_daily_plan(gs: GameState, include_strawberry: bool = True, include_land: bool = True) -> DailyPlan:
    day = gs.day
    money = gs.self_farm.money
    unlocked = gs.self_farm.unlocked_quadrants

    # Define layout profiles
    nearest_16 = [
        (3, 4), (4, 3), (2, 4), (3, 3), (4, 2), (1, 4), (2, 3), (3, 2),
        (4, 1), (0, 4), (1, 3), (2, 2), (3, 1), (4, 0), (0, 3), (1, 2)
    ]
    all_nw = [(x, y) for y in range(5) for x in range(5) if (x, y) != (4, 4)]

    # 1. Start from nearest_16, activate all 25 NW tiles when workload allows (day >= 4 and money >= 1200)
    if day >= 4 and money >= 1200:
        active_tiles = all_nw
    else:
        active_tiles = nearest_16

    # If NE is unlocked, we add all 25 plantable tiles in NE quadrant!
    if "NE" in unlocked:
        ne_tiles = [(x, y) for y in range(5) for x in range(5, 10) if (x, y) != (5, 4)]
        active_tiles = active_tiles + ne_tiles

    # 2. Buy land conditionally (to unlock NE)
    land_orders = []
    cash_reserve = 400
    if include_land and "NE" not in unlocked and 10 <= day <= 18:
        # Check safe cash reserve: land cost is $1000.
        # We require at least $2500 so we have at least $1500 remaining for robust seeds and hiring.
        if money >= 2500:
            land_orders.append(["BUY_LAND"])
            cash_reserve = 600  # keep a higher reserve on the turn we buy land

    # 3. Dynamic hand scaling
    # Scale hands dynamically up to 10/12 based on the number of active tiles:
    # - 16 tiles: 6 hands
    # - 25 tiles (NW): 8 hands
    # - 50 tiles (NW+NE): 12 hands
    n_tiles = len(active_tiles)
    if n_tiles <= 16:
        target_hands = 6
    elif n_tiles <= 25:
        target_hands = 8
    else:
        target_hands = 12

    # 4. Generate CropPlan
    farm = gs.self_farm
    empty_tiles = [tile for tile in active_tiles if farm.tile(tile[0], tile[1]).empty]

    crops_pool = ["WHEAT", "CARROT", "MELON"]
    if include_strawberry:
        crops_pool.append("STRAWBERRY")

    crop_plan = get_crop_plan(gs, empty_tiles, crops_pool=crops_pool)

    return DailyPlan(
        active_tiles=active_tiles,
        crop_plan=crop_plan,
        target_hands=target_hands,
        land_orders=land_orders,
        cash_reserve=cash_reserve
    )
