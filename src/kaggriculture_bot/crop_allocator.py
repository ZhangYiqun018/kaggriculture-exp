"""Crop Plan Allocator (v031).

Generates a single, consistent CropPlan shared by task generation and seed purchasing.
Allocates empty tiles sequentially; after each allocation, updates the projected
market inventory and recomputes the marginal crop value.
"""
from __future__ import annotations

from .constants import CROPS, MARKET_I0, PHASE3_CROPS
from .state import GameState
from .economy import expected_yield, sell_revenue, viable


def get_crop_plan(gs: GameState, empty_tiles: list[tuple[int, int]], crops_pool: list[str] | None = None) -> dict[tuple[int, int], str]:
    """Builds a single, consistent CropPlan mapping empty tiles -> crop to plant.

    Allocates empty tiles sequentially; after each allocation, updates the projected
    market inventory and recomputes the marginal crop value.
    """
    if crops_pool is None:
        crops_pool = PHASE3_CROPS

    day = gs.day
    # 1. Start with currently growing crops on both fields as our baseline projected market inventory
    proj_inv = {k: float(v) for k, v in gs.market.inventory.items()}
    for farm in (gs.self_farm, gs.opponent_farm):
        for row in farm.tiles:
            for tile in row:
                if tile.kind == "PLANT" and tile.crop in CROPS:
                    c = tile.crop
                    cd = CROPS[c]
                    # Estimate yield at max maturity
                    proj_inv[c] = proj_inv.get(c, 0.0) + expected_yield(c, cd["max_yield_day"])

    plan = {}

    # Sort empty tiles to ensure deterministic allocation order (e.g. sorted by coordinates)
    sorted_tiles = sorted(empty_tiles)

    for tile in sorted_tiles:
        best_crop = None
        best_profit = -99999.0

        for crop in crops_pool:
            if not viable(crop, day):
                continue

            cd = CROPS[crop]
            # Calculate marginal value of planting this crop on this tile today
            # We assume harvest at max maturity
            max_age = cd["max_yield_day"]
            units = expected_yield(crop, max_age)

            # The current projected inventory for this crop
            curr_proj = proj_inv.get(crop, float(MARKET_I0))

            # Expected revenue using exact sell_revenue (which simulates price decay)
            rev = sell_revenue(crop, units, curr_proj)
            profit = rev - cd["seed_cost"]

            if profit > best_profit and profit > 0:
                best_profit = profit
                best_crop = crop

        if best_crop:
            plan[tile] = best_crop
            # Update projected market inventory for subsequent allocations
            cd = CROPS[best_crop]
            units = expected_yield(best_crop, cd["max_yield_day"])
            proj_inv[best_crop] = proj_inv.get(best_crop, 0.0) + units

    return plan
