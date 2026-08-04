"""Assignment: units -> tasks. Greedy first; forward-compatible with
multi-unit joint search (hands) introduced in Phase 3.4.

Assignment never decides WHAT the farm should do (tasks.py + economy.py) — it
decides WHO does WHICH generated task and emits THIS turn's unit action.
"""
from __future__ import annotations
from dataclasses import dataclass

from .constants import BOARD_SIZE
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
    return task.target


def _feasible(task: Task, gs: GameState, unit: UnitView) -> bool:
    if task.kind == TASK_PLANT:
        return gs.private.seeds.get(task.crop, 0) > 0
    if task.kind == TASK_DROP:
        return sum(unit.inventory.values()) > 0
    return True


def greedy_assign(gs: GameState, tasks: list[Task]) -> list[Assignment]:
    """Process tasks in tier order; for each, closest feasible unassigned unit.
    One unit per task, one task per unit per turn."""
    units = units_from_state(gs)
    assigned_unit: set[int] = set()
    claimed: set[str] = set()
    out: list[Assignment] = []

    ordered = sorted(tasks, key=lambda t: (t.priority_tier, -t.expected_value))
    for task in ordered:
        if task.task_id in claimed:
            continue
        tgt = _task_target_pos(task)
        best: UnitView | None = None
        best_dist = 1_000
        for u in units:
            if u.idx in assigned_unit:
                continue
            if not _feasible(task, gs, u):
                continue
            d = 0 if tgt is None else abs(u.pos[0] - tgt[0]) + abs(u.pos[1] - tgt[1])
            if d < best_dist:
                best, best_dist = u, d
        if best is None:
            continue
        claimed.add(task.task_id)
        assigned_unit.add(best.idx)
        out.append(Assignment(best.idx, task, _action_for(best, task, tgt)))

    for u in units:
        if u.idx not in assigned_unit:
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
            return ["DROP"]
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
