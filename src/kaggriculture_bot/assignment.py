"""Assignment: units -> tasks. Greedy first; forward-compatible with hands (repaired in Phase 3R.4).

Repairs:
- target tile exclusivity (at most one exclusive task per tile per turn via conflict_key)
- global per-crop seed budget reservation during sequential greedy assignment
- deadline reachability gate (manhattan distance to task target must fit in day/step)
- same-day WATER capacity gate (do not PLANT unless same-day water capacity exists)
"""
from __future__ import annotations
from dataclasses import dataclass

from .constants import BOARD_SIZE, TURNS_PER_DAY, EPISODE_STEPS
from .state import GameState
from .tasks import Task, TASK_WATER, TASK_HARVEST, TASK_PLANT, TASK_DIG, TASK_DROP

# NW shed-access tile (engine _shed_access_tiles). DROP must happen here.
_DROP_TARGET = (BOARD_SIZE // 2 - 1, BOARD_SIZE // 2 - 1)  # (4,4)


@dataclass(frozen=True)
class UnitView:
    idx: int                       # 0 = farmer, 1..n = hands (today only)
    pos: tuple[int, int]
    inventory: dict


@dataclass(frozen=True)
class Assignment:
    unit_idx: int
    task: Task | None
    action: list


def units_from_state(gs: GameState) -> list[UnitView]:
    out = [UnitView(0, gs.self_farm.farmer, gs.private.inventories[0] if gs.private.inventories else {})]
    for i, h in enumerate(gs.self_farm.hands):
        inv = gs.private.inventories[i + 1] if i + 1 < len(gs.private.inventories) else {}
        out.append(UnitView(i + 1, h, inv))
    return out


def _task_target_pos(task: Task) -> tuple[int, int] | None:
    if task.kind == TASK_DROP:
        return _DROP_TARGET
    if task.kind == "PICKUP" and task.target is None:
        # return canonical shed tile for pickup
        return (4, 4)
    return task.target


def _conflict_key(task: Task) -> str | None:
    """Returns a key for exclusive spatial/resource conflict prevention.

    For spatial tasks, the tile coordinate (x,y) is the exclusive key: only
    one unit can work on a tile per turn.
    """
    if task.kind == TASK_DROP:
        return f"shed:drop:{task.task_id}" # make it unique per unit
    if task.target is not None:
        return f"tile:{task.target[0]},{task.target[1]}"
    return None


def _feasible(task: Task, gs: GameState, unit: UnitView, seed_ledger: dict[str, int]) -> bool:
    day, hour = gs.day, gs.hour
    hours_left = TURNS_PER_DAY - hour
    steps_left = EPISODE_STEPS - gs.step

    # 1) Seeds budget reservation check
    if task.kind == TASK_PLANT:
        crop = task.crop or ""
        if seed_ledger.get(crop, 0) <= 0:
            return False
            
        # Water service capacity check: do not PLANT if we are in the last hour
        # of the day (hour 23) because the newly planted seed would turn into a
        # WEED immediately at EOD refresh (requires same-day water).
        if hours_left <= 1:
            return False

    # 1.5) Feed / Fertilizer / Pickup / Place feasibility checks (Stage v041)
    if task.kind == "FEED":
        # must have WHEAT in hand inventory to feed!
        return unit.inventory.get("WHEAT", 0) > 0
    if task.kind == "FERTILIZE":
        # must have FERTILIZER in hand inventory to fertilize!
        return unit.inventory.get("FERTILIZER", 0) > 0
    if task.kind == "PLACE":
        # must have the corresponding animal in hand inventory to place!
        return unit.inventory.get(task.crop or "", 0) > 0
    if task.kind == "PICKUP":
        # must NOT already have full hand inventory
        return sum(unit.inventory.values()) < 10

    # 2) Carrying check for DROP
    if task.kind == TASK_DROP:
        # We drop WHEAT, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, FERTILIZER.
        # Exclude animals COW and SHEEP so we don't drop them back.
        carrying_items = {k: v for k, v in unit.inventory.items() if k not in ("COW", "SHEEP")}
        return sum(carrying_items.values()) > 0

    # 3) Reachability checks
    tgt = _task_target_pos(task)
    if tgt is not None:
        dist = abs(unit.pos[0] - tgt[0]) + abs(unit.pos[1] - tgt[1])
        # Can we physically reach the target before the global game ends?
        if dist > steps_left:
            return False
        # Can we reach the target before the task deadline?
        # Task deadline is absolute step. Our target step is gs.step + dist + 1 (action step).
        if gs.step + dist >= task.deadline_step:
            return False

    return True


def greedy_assign(gs: GameState, tasks: list[Task]) -> list[Assignment]:
    """Exhaustive greedy assignment with exclusive spatial locks and seed budget."""
    units = units_from_state(gs)
    assigned_units: set[int] = set()
    claimed_conflict_keys: set[str] = set()
    claimed_task_ids: set[str] = set()
    out: list[Assignment] = []

    # Local seed ledger initialized from available private seeds.
    # Mutates as PLANT tasks get greedily claimed.
    seed_ledger = dict(gs.private.seeds)

    # Sort tasks: highest-priority tier first, then expected_value desc.
    ordered = sorted(tasks, key=lambda t: (t.priority_tier, -t.expected_value))
    
    for task in ordered:
        if task.task_id in claimed_task_ids:
            continue
            
        ck = _conflict_key(task)
        if ck is not None and ck in claimed_conflict_keys:
            continue

        tgt = _task_target_pos(task)
        best: UnitView | None = None
        best_dist = 1_000_000
        
        for u in units:
            if u.idx in assigned_units:
                continue
            if not _feasible(task, gs, u, seed_ledger):
                continue
            d = 0 if tgt is None else abs(u.pos[0] - tgt[0]) + abs(u.pos[1] - tgt[1])
            if d < best_dist:
                best, best_dist = u, d
                
        if best is None:
            continue

        # Claim the assignment
        claimed_task_ids.add(task.task_id)
        assigned_units.add(best.idx)
        if ck is not None:
            claimed_conflict_keys.add(ck)
            
        # Deduct seed budget if planting
        if task.kind == TASK_PLANT:
            crop = task.crop or ""
            if crop in seed_ledger:
                seed_ledger[crop] = max(0, seed_ledger[crop] - 1)

        out.append(Assignment(best.idx, task, _action_for(best, task, tgt)))

    # Ensure unassigned units PASS
    for u in units:
        if u.idx not in assigned_units:
            out.append(Assignment(u.idx, None, ["PASS"]))
            
    out.sort(key=lambda a: a.unit_idx)
    return out


def _action_for(unit: UnitView, task: Task, tgt: tuple[int, int] | None) -> list:
    if tgt is not None and unit.pos == tgt:
        if task.kind == TASK_WATER:
            return ["WATER"]
        if task.kind == TASK_HARVEST:
            return ["HARVEST"]
        if task.kind == TASK_PLANT:
            return ["PLANT", task.crop]
        if task.kind == TASK_DIG:
            return ["DIG"]
        if task.kind == TASK_DROP:
            # We only drop items that are not animals
            carrying_items = {k: v for k, v in unit.inventory.items() if k not in ("COW", "SHEEP")}
            # If the unit has more than one item type, we drop the first one
            for k, v in carrying_items.items():
                if v > 0:
                    return ["DROP", k, v]
            return ["PASS"]
            
        # Livestock actions (Stage v041)
        if task.kind == "BUILD_PASTURE":
            return ["BUILD_PASTURE"]
        if task.kind == "PICKUP":
            return ["PICKUP", task.required_item, 1]
        if task.kind == "PLACE":
            return ["PLACE", task.crop]
        if task.kind == "FEED":
            return ["FEED"]
        if task.kind == "CARE":
            return ["CARE"]
        if task.kind == "COLLECT_FERTILIZER":
            return ["COLLECT_FERTILIZER"]
        if task.kind == "FERTILIZE":
            return ["FERTILIZE"]
            
    if tgt is None:
        return ["PASS"]
    fx, fy = unit.pos
    if fx < tgt[0]:
        return ["EAST"]
    if fx > tgt[0]:
        return ["WEST"]
    if fy < tgt[1]:
        return ["SOUTH"]
    if fy > tgt[1]:
        return ["NORTH"]
    return ["PASS"]
