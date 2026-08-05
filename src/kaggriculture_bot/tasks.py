"""Task generation: candidate tasks from GameState. Pure functions.

Decisions are tier-disciplined.

Tiers:
  0: dies tonight if skipped
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
from .crop_allocator import get_crop_plan

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

SHED_ACCESS_TILES = [(4, 4), (4, 5), (5, 4), (5, 5)]


@dataclass(frozen=True)
class Task:
    task_id: str
    kind: str
    target: tuple[int, int] | None
    priority_tier: int
    deadline_step: int
    expected_value: float
    travel_cost: float = 0.0      # filled by assignment
    opportunity_cost: float = 0.0  # filled by assignment
    required_item: str | None = None
    crop: str | None = None


def _harvest_value(gs: GameState, crop: str, units: int) -> float:
    inv = gs.market.inventory.get(crop, MARKET_I0)
    return float(sell_revenue(crop, int(units), inv))


def generate_tasks(gs: GameState, managed_tiles: list[tuple[int, int]], crop_plan: dict[tuple[int, int], str] | None = None) -> list[Task]:
    """Generate candidate tasks for this turn from the parsed game state."""
    tasks: list[Task] = []
    day, step = gs.day, gs.step
    last_step_today = (day + 1) * TURNS_PER_DAY - 1
    farm = gs.self_farm
    shed_total = sum(gs.private.shed.values())

    # Calculate alternative crop profit per day to evaluate opportunity cost of waiting
    ranking = crop_ranking(day, market_inventory={k: float(v) for k, v in gs.market.inventory.items()})
    max_alt_profit_per_day = 0.0
    for cname, a in ranking.items():
        if a["feasible"] and a["profit_per_day"] > max_alt_profit_per_day:
            max_alt_profit_per_day = a["profit_per_day"]
    if max_alt_profit_per_day <= 0:
        max_alt_profit_per_day = 25.0  # standard baseline profit per day

    # --- Day 29 Terminal Mode (step >= 696)
    # Stop planting, watering, and digging entirely. Only harvest and drop carried goods.
    if day >= 29:
        # Generate HARVEST tasks for any crops with yield
        for y in range(farm.tiles.__len__()):
            for x in range(farm.tiles[y].__len__()):
                tile = farm.tiles[y][x]
                if tile.kind == "PLANT" and tile.yield_units > 0:
                    crop = tile.crop
                    if crop is None or crop not in CROPS:
                        continue
                    value_now = _harvest_value(gs, crop, tile.yield_units)
                    tasks.append(Task(
                        task_id=f"harvest:{x},{y}", kind=TASK_HARVEST, target=(x, y),
                        priority_tier=TIER_DECAY, deadline_step=last_step_today,
                        expected_value=value_now, crop=crop,
                    ))
                    
        # Generate target-specific return/drop tasks per carrying unit
        _generate_unit_drop_tasks(gs, tasks, last_step_today)
        return tasks

    # ---- Tier 4: PLANT empty managed tiles using the shared CropPlan
    # We generate empty tiles list
    empty_tiles = []
    for x, y in managed_tiles:
        if farm.tile(x, y).empty:
            empty_tiles.append((x, y))

    if crop_plan is None:
        crop_plan = get_crop_plan(gs, empty_tiles)

    # Emit exactly one PLANT intent per tile
    for (x, y), crop in crop_plan.items():
        cd = CROPS[crop]
        tasks.append(Task(
            task_id=f"plant:{crop}:{x},{y}",
            kind=TASK_PLANT, target=(x, y),
            priority_tier=TIER_PLANT,
            deadline_step=last_step_today,
            expected_value=float(ranking[crop]["expected_profit"]),
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
                value_now = _harvest_value(gs, crop, tile.yield_units)
                
                # 6. Replace sunk-cost average NPV with incremental harvest-now vs wait value.
                max_age = cd["max_yield_day"]
                max_yield = expected_yield(crop, max_age)
                value_max = _harvest_value(gs, crop, max_yield)
                
                extra_days_to_wait = max(1, max_age - age)
                opportunity_cost = max_alt_profit_per_day * extra_days_to_wait
                
                decaying = tile.max_lifespan_step >= 0 and step >= tile.max_lifespan_step
                terminal_squeeze = day >= 28
                
                # If value of harvesting now + alternative profit > waiting for max yield, we harvest now.
                should_harvest = (age >= max_age) or decaying or terminal_squeeze or (value_now + opportunity_cost >= value_max)
                
                # 5. Do not emit HARVEST tasks when should_harvest is false.
                if should_harvest:
                    tier = TIER_DECAY if (decaying or terminal_squeeze) else (
                        TIER_HARVEST_HIGH if value_now >= 100 else TIER_ROUTINE)
                    tasks.append(Task(
                        task_id=f"harvest:{x},{y}", kind=TASK_HARVEST, target=(x, y),
                        priority_tier=tier, deadline_step=last_step_today,
                        expected_value=value_now, crop=crop,
                    ))

    # ---- Tier 5: DROP target-specific return/drop tasks per carrying unit
    _generate_unit_drop_tasks(gs, tasks, last_step_today)

    return tasks


def _generate_unit_drop_tasks(gs: GameState, tasks: list[Task], last_step_today: int):
    """Generates one return/drop task per carrying unit and distributes them
    among all four shed-access tiles.
    """
    farm = gs.self_farm
    unit_positions = [farm.farmer] + list(farm.hands)
    unit_inventories = gs.private.inventories

    for i in range(len(unit_positions)):
        if i >= len(unit_inventories):
            continue
        inv = unit_inventories[i]
        qty = sum(inv.values())
        if qty > 0:
            pos = unit_positions[i]
            # Find the closest of the 4 shed-access tiles
            best_tile = (4, 4)
            best_dist = 1000
            for sx, sy in SHED_ACCESS_TILES:
                d = abs(pos[0] - sx) + abs(pos[1] - sy)
                if d < best_dist:
                    best_dist = d
                    best_tile = (sx, sy)
            
            # Create a target-specific DROP task for this unit
            tasks.append(Task(
                task_id=f"drop:unit:{i}", kind=TASK_DROP, target=best_tile,
                priority_tier=TIER_DECAY if gs.day >= 29 else TIER_LOGISTICS,
                deadline_step=last_step_today,
                expected_value=float(qty),
            ))


def top_tasks(tasks: list[Task], n: int = 10) -> list[Task]:
    """Tier-disciplined ordering: tier first, then expected_value desc (no flattening)."""
    return sorted(tasks, key=lambda t: (t.priority_tier, -t.expected_value))[:n]
