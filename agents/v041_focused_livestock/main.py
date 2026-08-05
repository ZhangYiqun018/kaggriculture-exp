"""v041_focused_livestock: advanced crop loop with focused COW and SHEEP livestock integration.

Scope (Stage v041):
- layout: promoted nearest_16 compact layout, with a designated pasture zone [(3, 4), (4, 3), (3, 3), (2, 4)] near the shed
- support exactly 2 cows + 2 sheep only
- build/buy/pickup/place/feed/care/harvest/fertilizer lifecycle
- maintain WHEAT feed buffer through BUY_PRODUCT
- route FERTILIZER to STRAWBERRY only when marginal value exceeds sale value
- zero escapes and zero stranded animals
"""
from __future__ import annotations
import sys
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.constants import CROPS  # noqa: E402
from kaggriculture_bot.daily_planner import compute_daily_plan  # noqa: E402
from kaggriculture_bot.tasks import generate_tasks  # noqa: E402
from kaggriculture_bot.assignment import greedy_assign  # noqa: E402
from kaggriculture_bot.policy import plan_market_orders  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402
from kaggriculture_bot.harness import make_agent, hand_count_from_obs  # noqa: E402

# Standard Stage v040 flags
INCLUDE_STRAWBERRY = True
INCLUDE_LAND = True

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

    # 1. Compute DailyPlan
    dp = compute_daily_plan(gs, include_strawberry=INCLUDE_STRAWBERRY, include_land=INCLUDE_LAND)

    # 2. Generate Tasks with include_livestock=True
    tasks = generate_tasks(gs, dp.active_tiles, crop_plan=dp.crop_plan, include_livestock=True)
    assignments = greedy_assign(gs, tasks)

    farmer_action = assignments[0].action if assignments else ["PASS"]
    hands_actions = [a.action for a in assignments[1:]]

    # 3. Market orders with include_livestock=True and dynamic cash reserves
    market = plan_market_orders(
        gs, tasks,
        max_hands_day=dp.target_hands,
        crop_plan=dp.crop_plan,
        land_orders=dp.land_orders,
        cash_reserve=dp.cash_reserve,
        include_livestock=True
    )

    return safe_action(
        raw_farmer=farmer_action,
        raw_hands=hands_actions,
        raw_market=market,
        observed_hand_count=farm.hand_count,
        seeds=seeds,
    )


agent = make_agent(core_agent, observed_hand_count_fn=hand_count_from_obs)
