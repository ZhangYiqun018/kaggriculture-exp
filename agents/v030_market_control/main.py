"""v030_market_control: highly optimized crop loop with market-aware allocation,
harvest-age optimization, quantity-aware chunked selling, and terminal liquidation.

Scope (Phase 3.5 / v030):
- layout: promoted nearest_16 compact layout
- task-based allocation with sequential greedy assignment
- market-aware marginal crop allocation (evaluates price pressure from growing crops)
- harvest-age NPV optimization (decides whether early-harvest beats max-yield wait)
- quantity-aware chunked selling with crop-specific price floor holds (withholds supply)
- terminal liquidation override (unconditional cash out at turns >= 718)
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.constants import CROPS  # noqa: E402
from kaggriculture_bot.tasks import generate_tasks  # noqa: E402
from kaggriculture_bot.assignment import greedy_assign  # noqa: E402
from kaggriculture_bot.policy import plan_market_orders  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402
from kaggriculture_bot.harness import make_agent, hand_count_from_obs  # noqa: E402

# Promoted nearest_16 compact layout from layout screen (highest cash, lowest weeds)
MANAGED_TILES = [
    (3, 4), (4, 3), (2, 4), (3, 3), (4, 2), (1, 4), (2, 3), (3, 2),
    (4, 1), (0, 4), (1, 3), (2, 2), (3, 1), (4, 0), (0, 3), (1, 2)
]
TARGET_HANDS_DAY = 6

_EP = {}


def _reset_episode_state():
    global _EP
    _EP = {}


def core_agent(obs, config=None):
    gs = parse_state(obs)
    if gs.step == 0:
        _reset_episode_state()

    farm = gs.self_farm
    private = gs.private
    seeds = private.seeds

    tasks = generate_tasks(gs, MANAGED_TILES)
    assignments = greedy_assign(gs, tasks)

    farmer_action = assignments[0].action if assignments else ["PASS"]
    hands_actions = [a.action for a in assignments[1:]]

    # True sequential hiring + quantity-aware selling + terminal liquidation
    market = plan_market_orders(gs, tasks, max_hands_day=TARGET_HANDS_DAY)

    return safe_action(
        raw_farmer=farmer_action,
        raw_hands=hands_actions,
        raw_market=market,
        observed_hand_count=farm.hand_count,
        seeds=seeds,
    )


agent = make_agent(core_agent, observed_hand_count_fn=hand_count_from_obs)
