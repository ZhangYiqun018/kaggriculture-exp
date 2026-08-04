"""v020_hands: task-based crop loop with marginal-value hand hiring.

Same scope as v011 (farmer + crops WHEAT/CARROT/MELON, no animals/land,
sell-all market) PLUS day-local hand hiring driven by hire_manager.should_hire.

Architecture:
  state -> tasks -> (hire decision) -> assignment -> safety
Hands join the day's assignment pool as extra units (they act next turn).
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.economy import crop_ranking  # noqa: E402
from kaggriculture_bot.constants import CROPS  # noqa: E402
from kaggriculture_bot.tasks import generate_tasks, TASK_PLANT  # noqa: E402
from kaggriculture_bot.assignment import greedy_assign  # noqa: E402
from kaggriculture_bot.hire_manager import should_hire  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402

# Larger work block once hands can be hired: NW quadrant plantable block.
MANAGED_TILES = [
    (2, 2), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3),
    (2, 4), (3, 4), (1, 2), (1, 3), (1, 1), (2, 1), (3, 1), (0, 0), (1, 0), (0, 1),
]
TARGET_HANDS_DAY = 6

_EP = {}


def _reset_episode_state():
    global _EP
    _EP = {}


def _seed_demand(gs, tasks) -> dict:
    need: dict[str, int] = {}
    ranking = crop_ranking(gs.day, market_inventory={k: float(v) for k, v in gs.market.inventory.items()})
    tiles_needing = {t.target for t in tasks if t.kind == TASK_PLANT}
    for tp in tiles_needing:
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
        seeds = private.seeds
        day = gs.day

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

        # HIRE: marginal-value decision, capped per day. HIRE executes after
        # unit actions; new hand is in next turn's assignment pool.
        hires_today = farm.hires_today
        if farm.hand_count + 1 <= TARGET_HANDS_DAY:
            while farm.hand_count + len([m for m in market if m and m[0] == "HIRE"]) < TARGET_HANDS_DAY:
                if should_hire(gs, tasks, cash_reserve=400):
                    if len(market) < 10:
                        market.append(["HIRE"])
                    else:
                        break
                else:
                    break
        else:
            pass

        for crop, n in _seed_demand(gs, tasks).items():
            if len(market) >= 10:
                break
            if n > 0 and farm.money >= CROPS[crop]["seed_cost"] * n:
                market.append(["BUY_SEED", crop, n])
        market = market[:10]

        return safe_action(
            raw_farmer=farmer_action,
            raw_hands=hands_actions,
            raw_market=market,
            observed_hand_count=farm.hand_count,
            seeds=seeds,
        )
    except Exception:
        try:
            n = len(obs.get("farms", [{}])[obs.get("player", 0)].get("hands", []))
        except Exception:
            n = 0
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
