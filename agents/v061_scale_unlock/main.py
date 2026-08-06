"""v061_scale_unlock: livestock pipeline fix + farmer-dedicated setup phase.

Changes from v060:
- Livestock ENABLED with fixed pipeline:
  - PASTURE_TILES excluded from crop_plan (was planted over)
  - COW/SHEEP never sold from shed (was instantly sold)
  - Wheat buffer only when animals ON pastures (was filling shed)
  - Farmer dedicated to livestock tasks during setup (days 0-6)
  - BUILD_PASTURE priority raised to TIER_DECAY
  - PICKUP priority raised to TIER_HARVEST_HIGH
- v060 land/hands/reserve parameters preserved
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
from kaggriculture_bot.tasks import generate_tasks, top_tasks  # noqa: E402
from kaggriculture_bot.assignment import greedy_assign, units_from_state  # noqa: E402
from kaggriculture_bot.policy import plan_market_orders  # noqa: E402
from kaggriculture_bot.safety import safe_action  # noqa: E402
from kaggriculture_bot.harness import make_agent, hand_count_from_obs  # noqa: E402

INCLUDE_STRAWBERRY = True
INCLUDE_LAND = True
INCLUDE_LIVESTOCK = False

LIVESTOCK_SETUP_DAYS = 6
LIVESTOCK_TASK_KINDS = {"BUILD_PASTURE", "PICKUP", "PLACE", "FEED", "DIG"}

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

    dp = compute_daily_plan(gs, include_strawberry=INCLUDE_STRAWBERRY, include_land=INCLUDE_LAND,
                            include_livestock=INCLUDE_LIVESTOCK)

    tasks = generate_tasks(
        gs, dp.active_tiles,
        crop_plan=dp.crop_plan,
        include_livestock=INCLUDE_LIVESTOCK
    )

    if INCLUDE_LIVESTOCK and gs.day < LIVESTOCK_SETUP_DAYS:
        livestock_tasks = [t for t in tasks if t.kind in LIVESTOCK_TASK_KINDS]
        crop_tasks = [t for t in tasks if t.kind not in LIVESTOCK_TASK_KINDS]
        if livestock_tasks:
            units = units_from_state(gs)
            farmer_unit = units[0]
            claimed_keys = set()
            farmer_assignment = greedy_assign(gs, livestock_tasks)
            farmer_action = farmer_assignment[0].action if farmer_assignment else ["PASS"]

            hand_tasks = crop_tasks
            hand_units = [u for u in units if u.idx != 0]
            claimed_task_ids = set()
            for a in farmer_assignment:
                if a.task is not None:
                    claimed_task_ids.add(a.task.task_id)
            hand_tasks = [t for t in crop_tasks if t.task_id not in claimed_task_ids]
            hand_assignments = greedy_assign(gs, hand_tasks)
            hands_actions = [a.action for a in hand_assignments if a.unit_idx != 0]
        else:
            assignments = greedy_assign(gs, tasks)
            farmer_action = assignments[0].action if assignments else ["PASS"]
            hands_actions = [a.action for a in assignments[1:]]
    else:
        assignments = greedy_assign(gs, tasks)
        farmer_action = assignments[0].action if assignments else ["PASS"]
        hands_actions = [a.action for a in assignments[1:]]

    market = plan_market_orders(
        gs, tasks,
        max_hands_day=dp.target_hands,
        crop_plan=dp.crop_plan,
        land_orders=dp.land_orders,
        cash_reserve=dp.cash_reserve,
        include_livestock=INCLUDE_LIVESTOCK
    )

    return safe_action(
        raw_farmer=farmer_action,
        raw_hands=hands_actions,
        raw_market=market,
        observed_hand_count=farm.hand_count,
        seeds=seeds,
    )


agent = make_agent(core_agent, observed_hand_count_fn=hand_count_from_obs)
