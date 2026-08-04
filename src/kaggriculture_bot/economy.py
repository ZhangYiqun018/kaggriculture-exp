"""Crop economy model. Pure functions only — no state, no decisions.

Answers: "at this day, what is each crop worth over the remaining horizon?"
Does NOT decide what to plant (that is the task/policy layer).
"""
from __future__ import annotations
import math

from .constants import (
    CROPS, MARKET_PARAMS, PRICE_FLOOR, MARKET_I0,
    EPISODE_STEPS, TURNS_PER_DAY, PHASE3_CROPS,
)

# Step 718 is the last processed; it is day 29 hour 22.
LAST_STEP = EPISODE_STEPS - 2
LAST_GAME_DAY = LAST_STEP // TURNS_PER_DAY  # 29


# ---------------------------------------------------------------- market price
def _shape(func: str, x: float) -> float:
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "log10":
        return math.log10(1.0 + x)
    return x


def market_price(item: str, inventory: float, params: dict | None = None) -> int:
    """Exact replica of engine market_price (kaggressriculture.py L177-191)."""
    p = (params or MARKET_PARAMS)[item]
    base, i0, t = p["base"], p["I0"], p["T"]
    if inventory < i0:
        amp = p["below_target"] * base / _shape(p["below_func"], t)
        price = base + amp * _shape(p["below_func"], i0 - inventory)
    else:
        amp = p["above_target"] * base / _shape(p["above_func"], t)
        price = base - amp * _shape(p["above_func"], inventory - i0)
    return max(PRICE_FLOOR, int(round(price)))


def sell_revenue(item: str, quantity: int, starting_inventory: float,
                 params: dict | None = None) -> int:
    """Exact per-unit lockstep revenue for selling `quantity` units.

    Matches engine: each unit priced at current inventory; inventory only
    increases for units sold at price > $1 (L633-635).
    """
    inv = starting_inventory
    revenue = 0
    for _ in range(max(0, quantity)):
        price = market_price(item, inv, params)
        revenue += price
        if price > PRICE_FLOOR:
            inv += 1
    return revenue


# ------------------------------------------------------------------- crops
def water_window(crop: str) -> tuple[int, int]:
    """Bonus watering window ages (inclusive) for one-time crops.

    Engine: window_start = (max_yield_day + 1) // 2; window is [start, max_yield_day].
    """
    c = CROPS[crop]
    start = (c["max_yield_day"] + 1) // 2
    return start, c["max_yield_day"]


def expected_yield(crop: str, harvest_age: int) -> int:
    """Yield at harvest_age assuming daily watering, no fertilizer (one-time crops).

    Engine semantics: yield starts at 1 on plant; watering on a window day adds +1.
    For ongoing crops this returns harvestable units at that production tick.
    """
    c = CROPS[crop]
    if harvest_age < c["first_yield_day"]:
        return 0
    if not c["ongoing"]:
        start, end = water_window(crop)
        bonus_days = max(0, min(harvest_age, end) - start + 1)
        return min(c["max_yield"], 1 + bonus_days)
    # ongoing: cumulative production ticks up to this age
    days_since_first = harvest_age - c["first_yield_day"] if harvest_age >= c["first_yield_day"] else -1
    if days_since_first < 0:
        return 0
    count = days_since_first // c["interval"] + 1
    return min(c["max_yield"], min(c["max_yield"], max(0, count)))


def first_harvest_day(crop: str, plant_day: int) -> int:
    return plant_day + CROPS[crop]["first_yield_day"]


def last_plant_day(crop: str, harvest_buffer: int = 0) -> int:
    """Latest day a crop can be planted such that its FIRST harvest still fits
    within the playable horizon (day 29)."""
    return LAST_GAME_DAY - CROPS[crop]["first_yield_day"] - harvest_buffer


def viable(crop: str, current_day: int, harvest_buffer: int = 0) -> bool:
    return current_day + CROPS[crop]["first_yield_day"] <= LAST_GAME_DAY - harvest_buffer


def crop_analysis(crop: str, current_day: int,
                  market_inventory: float | None = None,
                  params: dict | None = None,
                  harvest_buffer: int = 0) -> dict:
    """Full economics for one crop at one day. Does NOT decide anything."""
    c = CROPS[crop]
    is_feasible = viable(crop, current_day, harvest_buffer)

    # For one-time crops: harvest at max_yield_day (max unfertilized yield).
    # If horizon cuts it short, clamp harvest age to what fits.
    if c["ongoing"]:
        # For ongoing crops, Phase 3 does not use them; report basic first-tick info.
        harvest_age = c["first_yield_day"]
        units = expected_yield(crop, harvest_age)
        cycle_days = max(1, c["first_yield_day"])
    else:
        harvest_age = min(c["max_yield_day"], LAST_GAME_DAY - current_day)
        units = expected_yield(crop, harvest_age)
        cycle_days = max(1, harvest_age)

    inv = MARKET_I0 if market_inventory is None else market_inventory
    unit_price = market_price(crop, inv, params)
    revenue = sell_revenue(crop, units, inv, params)
    profit = revenue - c["seed_cost"]
    p = (params or MARKET_PARAMS)[crop]

    return {
        "crop": crop,
        "day": current_day,
        "feasible": is_feasible,
        "first_harvest_day": first_harvest_day(crop, current_day),
        "harvest_age": harvest_age,
        "expected_yield": units,
        "base_price": p["base"],
        "current_price": unit_price,
        "expected_revenue": revenue,
        "seed_cost": c["seed_cost"],
        "expected_profit": profit,
        "profit_per_day": profit / cycle_days,
        "profit_per_turn": profit / (cycle_days * TURNS_PER_DAY),
        "cycle_days": cycle_days,
        "risk_glut_above_target": p["above_target"],   # fractional crash per T flooded
        "price_if_flooded": market_price(crop, p["I0"] + p["T"], params),  # saturation price
        "last_plant_day": last_plant_day(crop, harvest_buffer),
    }


def crop_ranking(current_day: int,
                 market_inventory: dict[str, float] | None = None,
                 crops: list[str] | None = None,
                 params: dict | None = None) -> dict[str, dict]:
    """Per-crop analysis dict for a set of crops at a day.

    Returns {crop: analysis}. Does NOT choose — the caller decides with policy.
    """
    crops = crops or PHASE3_CROPS
    out = {}
    for crop in crops:
        inv = None if market_inventory is None else market_inventory.get(crop)
        out[crop] = crop_analysis(crop, current_day, inv, params=params)
    return out


def viable_crops(current_day: int, crops: list[str] | None = None,
                 harvest_buffer: int = 0) -> list[str]:
    crops = crops or PHASE3_CROPS
    return [c for c in crops if viable(c, current_day, harvest_buffer)]
