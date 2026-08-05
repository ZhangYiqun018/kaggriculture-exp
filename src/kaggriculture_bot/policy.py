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


def plan_market_orders(gs: GameState, tasks: list[Task], max_hands_day: int = 6,
                       crop_plan: dict[tuple[int, int], str] | None = None,
                       land_orders: list[list] | None = None,
                       cash_reserve: int = 400,
                       include_livestock: bool = False) -> list[list]:
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

    # 1.5. Process land orders first (Stage v040)
    if land_orders:
        for order in land_orders:
            market_orders.append(order)
            money -= 1000.0  # NE cost is 1000

    # 1.6. Livestock purchase and Wheat buffer management (Stage v041)
    if include_livestock:
        # Count existing and planned animals to support 2 cows + 2 sheep only
        cows_on_board = 0
        sheep_on_board = 0
        for row in farm.tiles:
            for tile in row:
                if tile.kind == "PASTURE" and tile.animal_kind:
                    if tile.animal_kind == "COW":
                        cows_on_board += 1
                    elif tile.animal_kind == "SHEEP":
                        sheep_on_board += 1
                        
        cows_carrying = sum(inv.get("COW", 0) for inv in gs.private.inventories)
        sheep_carrying = sum(inv.get("SHEEP", 0) for inv in gs.private.inventories)
        
        cows_in_shed = shed.get("COW", 0)
        sheep_in_shed = shed.get("SHEEP", 0)
        
        total_cows = cows_on_board + cows_carrying + cows_in_shed
        total_sheep = sheep_on_board + sheep_carrying + sheep_in_shed
        
        # We also count any pending BUY_ANIMAL orders we are submitting this turn
        pending_cows = len([o for o in market_orders if o[0] == "BUY_ANIMAL" and o[1] == "COW"])
        pending_sheep = len([o for o in market_orders if o[0] == "BUY_ANIMAL" and o[1] == "SHEEP"])
        
        # Support 2 cows + 2 sheep only
        # Require safe money reserves
        if total_cows + pending_cows < 2 and money >= cash_reserve + 400:
            market_orders.append(["BUY_ANIMAL", "COW", 1])
            money -= 400.0
        if total_sheep + pending_sheep < 2 and money >= cash_reserve + 500:
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])
            money -= 500.0
            
        # Maintain WHEAT feed buffer
        total_animals = total_cows + total_sheep
        if total_animals > 0:
            wheat_buffer = max(10, 5 * total_animals)
            current_wheat = shed.get("WHEAT", 0)
            if current_wheat < wheat_buffer and money >= cash_reserve + 25:
                buy_qty = int(wheat_buffer - current_wheat)
                market_orders.append(["BUY_PRODUCT", "WHEAT", buy_qty])
                # approximate cost of WHEAT product: base is 25
                money -= 25.0 * buy_qty

    # 2. Compile HIRE orders via sequential marginal hiring using dynamic cash_reserve
    optimal_hires = plan_hires(gs, tasks, max_hands=max_hands_day, cash_reserve=cash_reserve)
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
