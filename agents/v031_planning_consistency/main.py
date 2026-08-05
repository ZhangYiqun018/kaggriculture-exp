"""v031_planning_consistency: highly optimized, unified-planning crop loop.

Scope (Stage v031):
- layout: promoted nearest_16 compact layout
- task-based allocation with sequential greedy assignment
- single, consistent CropPlan shared by task generation and seed purchasing (sequential marginal allocation)
- harvest-age NPV optimization (decides early harvest based on opportunity cost of waiting)
- quantity-aware chunked selling with hold thresholds
- terminal runoff, return/harvest/drop, and final unconditional liquidation (turns >= 718)
- generates target-specific return/drop tasks utilizing all four shed-access tiles (4,4), (4,5), (5,4), (5,5)
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.crop_allocator import get_crop_plan  # noqa: E402
from kaggriculture_bot.tasks import generate_tasks  # noqa: E402
from kaggriculture_bot.assignment import greedy_assign  # noqa: E402
from kaggriculture_bot.policy import plan_market_orders  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402
from kaggriculture_bot.harness import make_agent, hand_count_from_obs  # noqa: E402

# Promoted nearest_16 compact layout from layout screen
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

    # 1. Build a single CropPlan shared by task generation and seed purchasing
    empty_tiles = []
    for x, y in MANAGED_TILES:
        if farm.tile(x, y).empty:
            empty_tiles.append((x, y))
    crop_plan = get_crop_plan(gs, empty_tiles)

    # 2. Pass CropPlan to task generation
    tasks = generate_tasks(gs, MANAGED_TILES, crop_plan=crop_plan)
    assignments = greedy_assign(gs, tasks)

    farmer_action = assignments[0].action if assignments else ["PASS"]
    hands_actions = [a.action for a in assignments[1:]]

    # 3. Pass CropPlan to seed purchasing
    market = plan_market_orders(gs, tasks, max_hands_day=TARGET_HANDS_DAY, crop_plan=crop_plan)

    return safe_action(
        raw_farmer=farmer_action,
        raw_hands=hands_actions,
        raw_market=market,
        observed_hand_count=farm.hand_count,
        seeds=seeds,
    )


agent = make_agent(core_agent, observed_hand_count_fn=hand_count_from_obs)
