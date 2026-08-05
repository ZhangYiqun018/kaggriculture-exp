"""v020_hands: task-based crop loop with marginal-value hand hiring.

Phase 3R.2: refactored to core_agent + harness.make_agent (fail-loud in tests).
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state
from kaggriculture_bot.economy import crop_ranking
from kaggriculture_bot.constants import CROPS
from kaggriculture_bot.tasks import generate_tasks, TASK_PLANT
from kaggriculture_bot.assignment import greedy_assign
from kaggriculture_bot.hire_manager import should_hire
from kaggriculture_bot.safety import safe_action
from kaggriculture_bot.harness import make_agent, hand_count_from_obs

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
    need: dict = {}
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


def core_agent(obs, config=None):
    gs = parse_state(obs)
    if gs.step == 0:
        _reset_episode_state()

    farm = gs.self_farm
    private = gs.private
    shed = private.shed
    seeds = private.seeds

    tasks = generate_tasks(gs, MANAGED_TILES)
    assignments = greedy_assign(gs, tasks)

    farmer_action = assignments[0].action if assignments else ["PASS"]
    hands_actions = [a.action for a in assignments[1:]]

    market = []
    for item in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                 "EGG", "MILK", "WOOL", "FERTILIZER"):
        n = shed.get(item, 0)
        if n > 0:
            market.append(["SELL", item, n])

    n_planned_hires = len([m for m in market if m and m[0] == "HIRE"])
    while farm.hand_count + n_planned_hires < TARGET_HANDS_DAY:
        if len(market) >= 10:
            break
        if should_hire(gs, tasks, cash_reserve=400):
            market.append(["HIRE"])
            n_planned_hires += 1
        else:
            break

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


agent = make_agent(core_agent, observed_hand_count_fn=hand_count_from_obs)
