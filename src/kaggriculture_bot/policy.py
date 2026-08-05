"""Policy module for market planning, quantity-aware selling, and terminal liquidation.

Scope (Phase 3.5 / v030):
- sequential hiring integration
- seed restock demand
- quantity-aware chunked selling with crop-specific hold thresholds
- terminal liquidation override on final turns (turns >= 718)
"""
from __future__ import annotations

from .constants import CROPS, MAX_MARKET_ORDERS, LAST_STEP
from .economy import market_price, crop_ranking
from .state import GameState
from .tasks import Task, TASK_PLANT
from .hire_manager import plan_hires

# Crop-specific hold thresholds under which we withhold supply
# to let the market recover, and chunk sizes to prevent self-glutting.
CROP_POLICIES = {
    "MELON":      {"hold_threshold": 120, "chunk_size": 2},
    "CARROT":     {"hold_threshold": 22,  "chunk_size": 3},
    "WHEAT":      {"hold_threshold": 12,  "chunk_size": 5},
    "TOMATO":     {"hold_threshold": 35,  "chunk_size": 2},
    "STRAWBERRY": {"hold_threshold": 70,  "chunk_size": 2},
}


def _seed_demand(gs: GameState, tasks: list[Task], crop_plan: dict[tuple[int, int], str] | None = None) -> dict[str, int]:
    """Calculate seed demand from generated CropPlan if available, otherwise fallback to tasks."""
    if crop_plan is not None:
        need: dict[str, int] = {}
        for crop in crop_plan.values():
            need[crop] = need.get(crop, 0) + 1
        held = gs.private.seeds
        return {c: max(0, n - held.get(c, 0)) for c, n in need.items()}

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


def plan_market_orders(gs: GameState, tasks: list[Task], max_hands_day: int = 6, crop_plan: dict[tuple[int, int], str] | None = None) -> list[list]:
    """Compile optimal market orders, respecting the 10-order limit."""
    market_orders: list[list] = []
    step = gs.step
    farm = gs.self_farm
    shed = gs.private.shed
    money = farm.money

    # 1. Terminal liquidation check (step >= 718)
    # Sell ALL inventory unconditionally.
    if step >= LAST_STEP:
        for item, qty in sorted(shed.items()):
            if qty > 0:
                market_orders.append(["SELL", item, qty])
        return market_orders[:MAX_MARKET_ORDERS]

    # 2. Compile HIRE orders via sequential marginal hiring
    optimal_hires = plan_hires(gs, tasks, max_hands=max_hands_day, cash_reserve=400)
    for _ in range(optimal_hires):
        market_orders.append(["HIRE"])

    # 3. Quantity-aware chunked selling
    for item in sorted(shed.keys()):
        qty = shed[item]
        if qty <= 0:
            continue
            
        policy = CROP_POLICIES.get(item, {"hold_threshold": 1, "chunk_size": 100})
        curr_price = gs.market.prices.get(item, 1)
        
        # Hold threshold check: keep supply if price is too low
        if curr_price < policy["hold_threshold"]:
            continue
            
        # Sell in small controlled chunks to avoid self-crashing the price
        chunk = min(qty, policy["chunk_size"])
        if chunk > 0:
            market_orders.append(["SELL", item, chunk])

    # 4. Restock seeds
    for crop, n in _seed_demand(gs, tasks, crop_plan).items():
        if n > 0 and money >= CROPS[crop]["seed_cost"] * n:
            market_orders.append(["BUY_SEED", crop, n])
            # approximate remaining money
            money -= CROPS[crop]["seed_cost"] * n

    return market_orders[:MAX_MARKET_ORDERS]
