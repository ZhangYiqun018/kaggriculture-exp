"""Task generation: candidate tasks from GameState. Pure functions.

No if/elif rule dispatch — the caller scores tasks and assigns them.

Tier discipline (never flattened into a single score):
  0: dies tonight if skipped (unwatered plant at consecutive_unwatered>=1, i.e.
     planted today or missed water yesterday)
  1: decaying mature crop / terminal liquidation deadline
  2: high-value HARVEST
  3: routine WATER / HARVEST / DIG
  4: positive-NPV PLANT
  5: logistics (DROP to shed)
"""
from __future__ import annotations
from dataclasses import dataclass

from .constants import CROPS, TURNS_PER_DAY, EPISODE_STEPS, MARKET_I0
from .economy import sell_revenue, expected_yield, crop_ranking
from .state import GameState

TIER_DYING = 0
TIER_DECAY = 1
TIER_HARVEST_HIGH = 2
TIER_ROUTINE = 3
TIER_PLANT = 4
TIER_LOGISTICS = 5

TASK_WATER = "WATER"
TASK_HARVEST = "HARVEST"
TASK_PLANT = "PLANT"
TASK_DIG = "DIG"
TASK_DROP = "DROP"
TASK_PASS = "PASS"


@dataclass(frozen=True)
class Task:
    task_id: str
    kind: str
    target: tuple | None
    priority_tier: int
    deadline_step: int
    expected_value: float
    travel_cost: float = 0.0      # filled by assignment (per unit)
    opportunity_cost: float = 0.0  # filled by assignment
    required_item: str | None = None
    crop: str | None = None


def _harvest_value(gs: GameState, crop: str, units: int) -> float:
    inv = gs.market.inventory.get(crop, MARKET_I0)
    return float(sell_revenue(crop, int(units), inv))


def generate_tasks(gs: GameState, managed_tiles: list[tuple]) -> list[Task]:
    """Generate candidate tasks for this turn from the parsed game state.

    managed_tiles: the work block this controller operates on (policy input,
    NOT derived here). Tasks target positions; which unit takes them is the
    assignment layer's problem.
    """
    tasks: list[Task] = []
    day, step = gs.day, gs.step
    last_step_today = (day + 1) * TURNS_PER_DAY - 1
    farm = gs.self_farm
    seeds = gs.private.seeds
    shed_total = sum(gs.private.shed.values())
    unit_inv_total = sum(sum(inv.values()) for inv in gs.private.inventories)

    ranking = crop_ranking(day, market_inventory={k: float(v) for k, v in gs.market.inventory.items()})

    # ---- Tier 4: PLANT empty managed tiles with feasibility + seed budget.
    # NOTE: seeds exchange hands in the *market* phase (after units act), so
    # only seeds already held can be planted this turn (contract §3.8).
    for i, (x, y) in enumerate(managed_tiles):
        tile = farm.tile(x, y)
        if not tile.empty:
            continue
        for crop, a in ranking.items():
            if not a["feasible"] or a["expected_profit"] <= 0:
                continue
            tasks.append(Task(
                task_id=f"plant:{crop}:{x},{y}",
                kind=TASK_PLANT, target=(x, y),
                priority_tier=TIER_PLANT,
                deadline_step=last_step_today,  # new plants must be watered today
                expected_value=float(a["expected_profit"]),
                required_item=f"seed:{crop}",
                crop=crop,
            ))

    # ---- Plant tiles: WATER / HARVEST / decay.
    for y in range(farm.tiles.__len__()):
        for x in range(farm.tiles[y].__len__()):
            tile = farm.tiles[y][x]
            if tile.kind == "WEED" and (x, y) in managed_tiles:
                tasks.append(Task(
                    task_id=f"dig:{x},{y}", kind=TASK_DIG, target=(x, y),
                    priority_tier=TIER_ROUTINE, deadline_step=EPISODE_STEPS,
                    expected_value=1.0,  # enables future planting
                ))
                continue
            if tile.kind != "PLANT":
                continue
            crop = tile.crop
            if crop is None or crop not in CROPS:
                continue
            cd = CROPS[crop]
            age = tile.age(day)

            # WATER task.
            if not tile.watered_today:
                # Dies at end-of-day if consecutive_unwatered reaches 2 and it's missed today.
                dying = tile.consecutive_unwatered >= 1
                # Value of watering = protecting the remaining expected harvest.
                mature_units = expected_yield(crop, min(age, cd["max_yield_day"]))
                units_now = max(tile.yield_units, mature_units)
                value = _harvest_value(gs, crop, units_now)
                tasks.append(Task(
                    task_id=f"water:{x},{y}", kind=TASK_WATER, target=(x, y),
                    priority_tier=TIER_DYING if dying else TIER_ROUTINE,
                    deadline_step=last_step_today,
                    expected_value=value,
                    crop=crop,
                ))

            # HARVEST task.
            if tile.yield_units > 0 and age >= cd["first_yield_day"]:
                value = _harvest_value(gs, crop, tile.yield_units)
                decaying = tile.max_lifespan_step >= 0 and step >= tile.max_lifespan_step
                terminal_squeeze = day >= 28  # last 2 days: take anything harvestable
                tier = TIER_DECAY if (decaying or terminal_squeeze) else (
                    TIER_HARVEST_HIGH if value >= 100 else TIER_ROUTINE)
                tasks.append(Task(
                    task_id=f"harvest:{x},{y}", kind=TASK_HARVEST, target=(x, y),
                    priority_tier=tier, deadline_step=last_step_today,
                    expected_value=value, crop=crop,
                ))

    # ---- Tier 5: DROP if any unit carries items (they vanish to shed at eod;
    # kepping them risks overflow loss). DROP must happen while shed-adjacent.
    if unit_inv_total > 0:
        # Check shed headroom: if the shed is already full, DROP is a no-op and
        # inventory will be LOST at eod — flag as Tier 1 so we prefer selling instead.
        headroom = max(0, 100 - shed_total)
        tier = TIER_DECAY if headroom < unit_inv_total else TIER_LOGISTICS
        tasks.append(Task(
            task_id="drop:shed", kind=TASK_DROP, target=None,
            priority_tier=tier, deadline_step=last_step_today,
            expected_value=float(unit_inv_total),  # rough: units proxied as value
        ))

    return tasks


def top_tasks(tasks: list[Task], n: int = 10) -> list[Task]:
    """Tier-disciplined ordering: tier first, then expected_value desc (no flattening)."""
    return sorted(tasks, key=lambda t: (t.priority_tier, -t.expected_value))[:n]
