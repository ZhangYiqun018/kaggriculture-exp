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
    "FERTILIZER": {"hold_threshold": 999, "chunk_size": 1},
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
    """Compile optimal market orders, respecting the 10-order limit.

    Order priority (cash-flow-aware):
    1. SELL shed surplus (generate cash first)
    2. Critical HIRE
    3. Emergency feed purchase (BUY_PRODUCT WHEAT)
    4. BUY_LAND (exact cost)
    5. BUY_ANIMAL
    6. BUY_SEED
    7. Optional extra HIRE
    """
    market_orders: list[list] = []
    step = gs.step
    farm = gs.self_farm
    shed = gs.private.shed
    money = farm.money
    LAND_COSTS = [1000, 2000, 4000]

    if step >= LAST_STEP:
        for item, qty in sorted(shed.items()):
            if qty > 0:
                market_orders.append(["SELL", item, qty])
        return market_orders[:MAX_MARKET_ORDERS]

    NEVER_SELL = {"COW", "SHEEP"}

    # 1. SELL first — generate cash for subsequent purchases
    sell_orders: list[list] = []
    for item in sorted(shed.keys()):
        if item in NEVER_SELL:
            continue
        qty = shed[item]
        if qty <= 0:
            continue
        policy = CROP_POLICIES.get(item, {"hold_threshold": 1, "chunk_size": 100})
        curr_price = gs.market.prices.get(item, 1)
        if curr_price < policy["hold_threshold"]:
            continue
        chunk = min(qty, policy["chunk_size"])
        if chunk > 0:
            sell_orders.append(["SELL", item, chunk])
            money += curr_price * chunk
    market_orders.extend(sell_orders)

    # 2. Critical HIRE (at least 1 if we have none and it's early)
    optimal_hires = plan_hires(gs, tasks, max_hands=max_hands_day, cash_reserve=cash_reserve)
    critical_hires = min(optimal_hires, 2)
    for _ in range(critical_hires):
        market_orders.append(["HIRE"])

    # 3. Emergency feed purchase
    if include_livestock:
        animals_on_board = sum(1 for row in farm.tiles for t in row if t.animal_kind)
        if animals_on_board > 0:
            total_wheat = shed.get("WHEAT", 0) + sum(
                inv.get("WHEAT", 0) for inv in gs.private.inventories
            )
            wheat_buffer = min(10, 3 * animals_on_board)
            if total_wheat < wheat_buffer and money >= cash_reserve + 25:
                buy_qty = min(int(wheat_buffer - total_wheat), 4)
                if buy_qty > 0:
                    market_orders.append(["BUY_PRODUCT", "WHEAT", buy_qty])
                    money -= 25.0 * buy_qty

    # 4. BUY_LAND with exact cost
    if land_orders:
        n_unlocked = len(farm.unlocked_quadrants) - 1
        for order in land_orders:
            if n_unlocked < len(LAND_COSTS):
                cost = LAND_COSTS[n_unlocked]
                if money - cost >= cash_reserve:
                    market_orders.append(order)
                    money -= cost
                    n_unlocked += 1

    # 5. BUY_ANIMAL (capped at 2C2S for v062)
    if include_livestock:
        cows_on_board = sum(1 for row in farm.tiles for t in row if t.animal_kind == "COW")
        sheep_on_board = sum(1 for row in farm.tiles for t in row if t.animal_kind == "SHEEP")
        cows_carrying = sum(inv.get("COW", 0) for inv in gs.private.inventories)
        sheep_carrying = sum(inv.get("SHEEP", 0) for inv in gs.private.inventories)
        cows_in_shed = shed.get("COW", 0)
        sheep_in_shed = shed.get("SHEEP", 0)

        target_cows, target_sheep = 2, 2

        if 4 <= gs.day <= 18 and farm.hand_count >= 3:
            empty_pastures = sum(1 for row in farm.tiles for t in row
                                 if t.kind == "PASTURE" and not t.animal_kind)
            total_cows = cows_on_board + cows_carrying + cows_in_shed
            total_sheep = sheep_on_board + sheep_carrying + sheep_in_shed

            if (total_cows < target_cows and money >= cash_reserve + 400
                    and empty_pastures > 0):
                market_orders.append(["BUY_ANIMAL", "COW", 1])
                money -= 400.0
            if (total_sheep < target_sheep and money >= cash_reserve + 500
                    and empty_pastures > total_cows):
                market_orders.append(["BUY_ANIMAL", "SHEEP", 1])
                money -= 500.0

    # 6. BUY_SEED
    for crop, n in _seed_demand(gs, tasks, crop_plan).items():
        if n > 0 and money >= CROPS[crop]["seed_cost"] * n:
            market_orders.append(["BUY_SEED", crop, n])
            money -= CROPS[crop]["seed_cost"] * n

    # 7. Optional extra HIRE
    extra_hires = optimal_hires - critical_hires
    for _ in range(extra_hires):
        market_orders.append(["HIRE"])

    return market_orders[:MAX_MARKET_ORDERS]
