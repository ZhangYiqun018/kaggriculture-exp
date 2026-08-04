"""v011_task_based: crop closed loop expressed through task + assignment layers.

Same behavioral scope as v010 (farmer only, no hire, no animals, no land,
WHEAT/CARROT/MELON, sell-all market), but decisions are made via:
  state -> tasks -> assignment -> safety
instead of hardcoded if/elif dispatch. This proves the task architecture
before hands/multi-unit arrive in Phase 3.4.
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.economy import crop_ranking, viable_crops  # noqa: E402
from kaggriculture_bot.constants import CROPS  # noqa: E402
from kaggriculture_bot.tasks import generate_tasks, TASK_PLANT  # noqa: E402
from kaggriculture_bot.assignment import greedy_assign  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402

MANAGED_TILES = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (3, 4)]

_EP = {}


def _reset_episode_state():
    global _EP
    _EP = {}


def _seed_demand(gs, tasks) -> dict:
    """Seeds to buy derived from PLANT tasks: one per empty managed tile using
    that tile's highest-profit feasible crop, minus seeds already held."""
    need: dict[str, int] = {}
    empty_tiles: list[tuple] = []
    plant_crops = {t.target for t in tasks if t.kind == TASK_PLANT}
    ranking = crop_ranking(gs.day, market_inventory={k: float(v) for k, v in gs.market.inventory.items()})
    for tile_pos in plant_crops:
        empty_tiles.append(tile_pos)
    for tile_pos in empty_tiles:
        # best feasible crop for this tile by profit
        best_crop, best_profit = None, 0.0
        for crop, a in ranking.items():
            if a["feasible"] and a["expected_profit"] > best_profit:
                best_crop, best_profit = crop, a["expected_profit"]
        if best_crop:
            need[best_crop] = need.get(best_crop, 0) + 1
    held = gs.private.seeds
    return {c: max(0, n - held.get(c, 0)) for c, n in need.items()}


def agent(obs, config=None):
    try:
        gs = parse_state(obs)
        if gs.step == 0:
            _reset_episode_state()

        farm = gs.self_farm
        private = gs.private
        shed = private.shed

        tasks = generate_tasks(gs, MANAGED_TILES)
        assignments = greedy_assign(gs, tasks)

        farmer_action = assignments[0].action if assignments else ["PASS"]
        hands_actions = [a.action for a in assignments[1:]]

        # ---------------- market ----------------
        market: list = []
        for item in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
            n = shed.get(item, 0)
            if n > 0:
                market.append(["SELL", item, n])
        for crop, n in _seed_demand(gs, tasks).items():
            if n > 0 and farm.money >= CROPS[crop]["seed_cost"] * n:
                market.append(["BUY_SEED", crop, n])
        market = market[:10]

        return safe_action(
            raw_farmer=farmer_action,
            raw_hands=hands_actions,
            raw_market=market,
            observed_hand_count=farm.hand_count,
            seeds=private.seeds,
        )
    except Exception:
        try:
            n = len(obs.get("farms", [{}])[obs.get("player", 0)].get("hands", []))
        except Exception:
            n = 0
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
