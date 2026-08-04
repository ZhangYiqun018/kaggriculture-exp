"""v010_single_farmer: single-farmer crop-only closed loop.

Scope (Phase 3.1):
- farmer only, NO hands, NO hire, NO animals, NO land
- crops: WHEAT / CARROT / MELON chosen via economy module (horizon-aware)
- simple sell-all market, seed restock, terminal liquidation
Uses state.py + economy.py + safety.py (inlined by package_agent.py).
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.economy import (  # noqa: E402
    crop_ranking, expected_yield, last_plant_day, LAST_GAME_DAY,
)
from kaggriculture_bot.constants import CROPS  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402

# Managed tiles: a fixed 2x3 work block in the NW quadrant around spawn.
MANAGED_TILES = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (3, 4)]

_EP = {}


def _reset_episode_state():
    global _EP
    _EP = {}


def _tile_crop_plan(day: int) -> list:
    """Per-tile crop intent for managed tiles, given day and horizon.

    Slots 0-1 plant MELON early only (single farmer can't service late melons
    and season horizon), then fall back to CARROT/WHEAT. Slots 2-3 favor
    CARROT for liquidity, slots 4-5 WHEAT as terminal fallback.
    """
    plan = [None] * len(MANAGED_TILES)
    melon_ok = day <= min(last_plant_day("MELON"), 8)
    carrot_ok = day <= last_plant_day("CARROT")
    wheat_ok = day <= last_plant_day("WHEAT")
    for i in range(2):
        plan[i] = "MELON" if melon_ok else ("CARROT" if carrot_ok else ("WHEAT" if wheat_ok else None))
    for i in (2, 3):
        plan[i] = "CARROT" if carrot_ok else ("WHEAT" if wheat_ok else None)
    for i in (4, 5):
        plan[i] = "WHEAT" if wheat_ok else None
    return plan


def _manhattan_step(fx: int, fy: int, tx: int, ty: int) -> str:
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    return "NORTH"  # only called when not equal


def _seed_restock(gs, plan) -> list:
    """Market orders to ensure one seed per empty managed tile with a plan."""
    orders = []
    seeds = gs.private.seeds
    day = gs.day
    want = {}
    for i, (x, y) in enumerate(MANAGED_TILES):
        crop = plan[i]
        if crop is None:
            continue
        tile = gs.self_farm.tile(x, y)
        if tile.empty and seeds.get(crop, 0) <= 0 and crop not in want:
            want[crop] = 2
    for crop, n in want.items():
        if gs.self_farm.money >= CROPS[crop]["seed_cost"] * n:
            orders.append(["BUY_SEED", crop, n])
    return orders


def _next_job_tile(gs, plan, fx: int, fy: int):
    """Closest managed tile (manhattan) with a pending job, in fixed tile order."""
    day = gs.day
    seeds = gs.private.seeds
    for i, (x, y) in enumerate(MANAGED_TILES):
        if (x, y) == (fx, fy):
            continue
        tile = gs.self_farm.tile(x, y)
        if tile.kind == "WEED":
            return (x, y)
        if tile.kind == "PLANT":
            cd = CROPS.get(tile.crop, {})
            if tile.yield_units > 0 and tile.age(day) >= cd.get("first_yield_day", 0):
                return (x, y)
            if not tile.watered_today:
                return (x, y)
        elif tile.empty and plan[i] and seeds.get(plan[i], 0) > 0:
            return (x, y)
    return None


def agent(obs, config=None):
    try:
        gs = parse_state(obs)
        if gs.step == 0:
            _reset_episode_state()

        farm = gs.self_farm
        private = gs.private
        seeds = private.seeds
        shed = private.shed
        day = gs.day
        fx, fy = farm.farmer
        tile = farm.tile(fx, fy)

        plan = _tile_crop_plan(day)

        # ---------------- market ----------------
        market = []
        for item in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
            n = shed.get(item, 0)
            if n > 0:
                market.append(["SELL", item, n])
        market.extend(_seed_restock(gs, plan))
        market = market[:10]

        # ---------------- farmer ----------------
        farmer_action = ["PASS"]
        crop = tile.crop if tile.kind == "PLANT" else None
        age = tile.age(day) if tile.kind == "PLANT" else -1
        squeeze = day >= LAST_GAME_DAY - 1  # day 28/29: harvest anything mature

        # 1) HARVEST: full-yield plant, or terminal squeeze of anything mature.
        if crop is not None and tile.yield_units > 0:
            cd = CROPS[crop]
            if age >= cd["max_yield_day"] or squeeze:
                farmer_action = ["HARVEST"]
        # 2) WATER: same-day survival rule (planting day counts as unwatered).
        if farmer_action == ["PASS"] and tile.kind == "PLANT" and not tile.watered_today:
            farmer_action = ["WATER"]
        # 3) PLANT: empty managed tile under farmer with feasible plan + seed.
        if farmer_action == ["PASS"] and tile.empty and (fx, fy) in MANAGED_TILES:
            i = MANAGED_TILES.index((fx, fy))
            c = plan[i]
            if c and seeds.get(c, 0) > 0:
                farmer_action = ["PLANT", c]
        # 4) Move toward the next managed tile with a pending job.
        if farmer_action == ["PASS"]:
            tgt = _next_job_tile(gs, plan, fx, fy)
            if tgt is not None:
                farmer_action = [_manhattan_step(fx, fy, tgt[0], tgt[1])]

        return safe_action(
            raw_farmer=farmer_action,
            raw_hands=[],
            raw_market=market,
            observed_hand_count=farm.hand_count,
            seeds=seeds,
        )
    except Exception:
        try:
            hands = obs.get("farms", [{}])[obs.get("player", 0)].get("hands", []) if isinstance(obs, dict) else []
            n = len(hands) if isinstance(hands, list) else 0
        except Exception:
            n = 0
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
