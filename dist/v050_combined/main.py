"""Auto-generated single-file agent. Do not edit by hand."""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
import math
import os
import traceback


# ===== INLINED: kaggriculture_bot/constants.py =====


# --- Crops ---
CROPS = {
    "WHEAT":      {"seed_cost": 10,  "first_yield_day": 2,  "max_yield_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed_cost": 20,  "first_yield_day": 2,  "max_yield_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed_cost": 50,  "first_yield_day": 8,  "max_yield_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed_cost": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed_cost": 80,  "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

# --- Animals ---
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
TOWN_CENTER_PRODUCTS = [p for p in PRODUCTS if p != "FERTILIZER"]

# --- Market ---
MARKET_I0 = 10000
PRICE_FLOOR = 1

MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "I0": MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base":  35, "I0": MARKET_I0, "T": 450, "below_func": "log",    "below_target": 0.20, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base":  60, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base":  50, "I0": MARKET_I0, "T": 332, "below_func": "linear", "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

# --- Movement ---
FARMER_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}

# --- Land ---
LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]

# --- Hiring ---
FARM_HAND_COST_MULT = 1

# --- Town shops ---
SHOPS = {
    "BAKERY": ["EGG", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
TOWN_CENTER_DEMAND_SCHEDULE = [(20, 4), (10, 2), (0, 1)]

# --- Config defaults ---
EPISODE_STEPS = 720
TURNS_PER_DAY = 24
DAYS = 30
STARTING_MONEY = 3000
SHED_CAPACITY = 100
MAX_MARKET_ORDERS = 10
ACT_TIMEOUT = 1
BOARD_SIZE = 10

# Last actionable step: step >= episodeSteps - 2 triggers DONE, so last processed is 718.
LAST_STEP = EPISODE_STEPS - 2  # 718

# --- Crop subsets for Phase 3 (closed-loop baseline) ---
PHASE3_CROPS = ["WHEAT", "CARROT", "MELON"]

# ===== INLINED: kaggriculture_bot/safety.py =====


MAX_MARKET_ORDERS = 10
FARMER_OPS = {"NORTH", "SOUTH", "EAST", "WEST", "PASS", "PICKUP", "PLANT", "WATER",
              "HARVEST", "FERTILIZE", "BUILD_COOP", "BUILD_PASTURE", "DIG",
              "PLACE", "FEED", "COLLECT_FERTILIZER", "CARE"}
MARKET_OPS = {"BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL", "HIRE", "BUY_LAND"}


def _is_list_action(a: Any) -> bool:
    return isinstance(a, list) and len(a) > 0 and isinstance(a[0], str)


def _valid_farmer_action(a: Any) -> list:
    if not _is_list_action(a):
        return ["PASS"]
    op = a[0]
    if op not in FARMER_OPS:
        return ["PASS"]
    return a


def _valid_hand_action(a: Any) -> list:
    if not _is_list_action(a):
        return ["PASS"]
    op = a[0]
    if op not in FARMER_OPS:
        return ["PASS"]
    return a


def _valid_market_order(o: Any) -> bool:
    if not isinstance(o, list) or len(o) == 0:
        return False
    if not isinstance(o[0], str) or o[0] not in MARKET_OPS:
        return False
    if o[0] in ("HIRE", "BUY_LAND"):
        return True
    if len(o) < 3:
        return False
    if not isinstance(o[1], str):
        return False
    try:
        n = int(o[2])
    except (TypeError, ValueError):
        return False
    return n > 0


def _seed_budget_plant_check(farmer_action: list, hands_actions: list[list],
                             seeds: dict) -> tuple[list, list[list]]:
    """If total PLANT requests for a crop exceed seeds, convert ALL that crop's PLANTs to PASS.

    Mirrors the engine's atomic PLANT validation (kaggriculture.py L889-902).
    """
    unit_actions = [farmer_action] + hands_actions
    demand: dict[str, int] = {}
    for a in unit_actions:
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT" and isinstance(a[1], str):
            demand[a[1]] = demand.get(a[1], 0) + 1
    blocked = {crop for crop, n in demand.items() if n > seeds.get(crop, 0)}
    if not blocked:
        return farmer_action, hands_actions

    def _fix(a: list) -> list:
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT" and a[1] in blocked:
            return ["PASS"]
        return a

    return _fix(farmer_action), [_fix(h) for h in hands_actions]


def safe_action(raw_farmer: Any, raw_hands: Any, raw_market: Any,
                observed_hand_count: int, seeds: dict | None = None) -> dict:
    """Build a guaranteed-valid action dict.

    Args:
        raw_farmer: proposed farmer action (any shape; will be validated/repaired)
        raw_hands: proposed hands actions (list of lists)
        raw_market: proposed market orders (list of lists)
        observed_hand_count: number of hands in observation (hands list length)
        seeds: current seed counts dict, for PLANT budget check
    """
    try:
        farmer = _valid_farmer_action(raw_farmer)

        # Hands: validate each, pad/truncate to observed count.
        if not isinstance(raw_hands, list):
            raw_hands = []
        hands = [_valid_hand_action(h) for h in raw_hands[:observed_hand_count]]
        while len(hands) < observed_hand_count:
            hands.append(["PASS"])

        # Market: validate and cap.
        if not isinstance(raw_market, list):
            raw_market = []
        market = [o for o in raw_market if _valid_market_order(o)][:MAX_MARKET_ORDERS]

        # PLANT seed-budget atomic check.
        if seeds is None:
            seeds = {}
        farmer, hands = _seed_budget_plant_check(farmer, hands, seeds)

        return {"farmer": farmer, "hands": hands, "market": market}
    except Exception:
        return {"farmer": ["PASS"], "hands": [["PASS"]] * max(0, observed_hand_count), "market": []}


FALLBACK_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}

# ===== INLINED: kaggriculture_bot/state.py =====




def g(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


@dataclass(frozen=True)
class TileInfo:
    x: int
    y: int
    kind: str  # EMPTY | LOCKED | PLANT | WEED | COOP | PASTURE
    crop: str | None = None
    planted_day: int = 0
    yield_units: int = 0
    watered_today: bool = False
    consecutive_unwatered: int = 0
    fertilized_until_day: int = -1
    max_lifespan_step: int = -1  # -1 for ongoing crops until max production reached
    
    # Animal/structure state (Stage v041)
    animal_kind: str | None = None
    animal_yield: int = 0
    animal_unfed: int = 0
    animal_cared_today: bool = False
    animal_fed_today: bool = False
    fertilizer_available: bool = False

    @property
    def empty(self) -> bool:
        return self.kind == "EMPTY"

    @property
    def locked(self) -> bool:
        return self.kind == "LOCKED"

    @property
    def is_weed(self) -> bool:
        return self.kind == "WEED"

    def age(self, day: int) -> int:
        return -1 if self.kind != "PLANT" else day - self.planted_day

    def fertilized(self, day: int) -> bool:
        return self.fertilized_until_day >= day

    @classmethod
    def from_raw(cls, x: int, y: int, raw: Any, day: int) -> "TileInfo":
        if raw is None:
            return cls(x, y, "EMPTY")
        if raw == "LOCKED":
            return cls(x, y, "LOCKED")
        if isinstance(raw, dict):
            kind = g(raw, "kind", "UNKNOWN")
            if kind == "PLANT":
                return cls(
                    x, y, "PLANT",
                    crop=g(raw, "crop"),
                    planted_day=int(g(raw, "planted_day", 0)),
                    yield_units=int(g(raw, "yield_units", 0)),
                    watered_today=bool(g(raw, "watered_today", False)),
                    consecutive_unwatered=int(g(raw, "consecutive_unwatered", 0)),
                    fertilized_until_day=int(g(raw, "fertilized_until_day", -1)),
                    max_lifespan_step=int(g(raw, "max_lifespan_step", -1)),
                )
            if kind == "WEED":
                return cls(x, y, "WEED")
                
            # Parse animal structure details (Stage v041)
            animal_kind = None
            animal_yield = 0
            animal_unfed = 0
            animal_cared_today = False
            animal_fed_today = False
            fert_avail = False
            
            animal_raw = g(raw, "animal")
            if isinstance(animal_raw, dict):
                animal_kind = g(animal_raw, "kind")
                animal_yield = int(g(animal_raw, "yield_units", 0))
                animal_unfed = int(g(animal_raw, "consecutive_unfed", 0))
                animal_cared_today = bool(g(animal_raw, "cared_today", False))
                animal_fed_today = bool(g(animal_raw, "fed_today", False))
                fert_avail = bool(g(animal_raw, "fertilizer_available", False))
                
            return cls(
                x, y, kind,
                animal_kind=animal_kind,
                animal_yield=animal_yield,
                animal_unfed=animal_unfed,
                animal_cared_today=animal_cared_today,
                animal_fed_today=animal_fed_today,
                fertilizer_available=fert_avail
            )
        return cls(x, y, "UNKNOWN")

    @property
    def shed_adjacent(self) -> bool:
        half = BOARD_SIZE // 2
        return (self.x, self.y) in {
            (half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)
        }


@dataclass(frozen=True)
class FarmState:
    player: int
    money: float
    farmer: tuple[int, int]
    hands: tuple[tuple[int, int], ...]
    unlocked_quadrants: tuple[str, ...]
    hires_today: int
    tiles: tuple[tuple[TileInfo, ...], ...]  # tiles[y][x]

    def tile(self, x: int, y: int) -> TileInfo:
        return self.tiles[y][x]

    @property
    def hand_count(self) -> int:
        return len(self.hands)


@dataclass(frozen=True)
class MarketState:
    inventory: dict[str, int]
    prices: dict[str, int]


@dataclass(frozen=True)
class PrivateState:
    shed: dict[str, int]
    seeds: dict[str, int]
    inventories: tuple[dict[str, int], ...]  # [farmer, hand1, ...]


@dataclass(frozen=True)
class GameState:
    step: int
    day: int
    hour: int
    self_farm: FarmState
    opponent_farm: FarmState
    market: MarketState
    private: PrivateState
    town_shops: tuple[str, ...]
    board_size: int = BOARD_SIZE

    @property
    def remaining_steps(self) -> int:
        return max(0, EPISODE_STEPS - self.step)

    @property
    def remaining_days(self) -> int:
        return max(0, DAYS - self.day)


def parse_state(obs: Any) -> GameState:
    """Parse a raw engine observation (dict or attr-wrapper) into GameState."""
    step = int(g(obs, "step", 0))
    day = int(g(obs, "day", step // TURNS_PER_DAY))
    hour = int(g(obs, "hour", step % TURNS_PER_DAY))
    player = int(g(obs, "player", 0))

    farms_raw = g(obs, "farms", []) or []

    def _parse_farm(idx: int) -> FarmState:
        raw = farms_raw[idx] if idx < len(farms_raw) else {}
        tiles_raw = g(raw, "tiles", []) or []
        tiles = tuple(
            tuple(TileInfo.from_raw(x, y, tiles_raw[y][x] if y < len(tiles_raw) and x < len(tiles_raw[y]) else None, day)
                  for x in range(BOARD_SIZE))
            for y in range(BOARD_SIZE)
        )
        fx, fy = (g(raw, "farmer", [BOARD_SIZE // 2 - 1, BOARD_SIZE // 2 - 1]) or [0, 0])[:2]
        hands_raw = g(raw, "hands", []) or []
        hands = tuple(tuple(h[:2]) for h in hands_raw if isinstance(h, (list, tuple)) and len(h) >= 2)
        return FarmState(
            player=idx,
            money=float(g(raw, "money", 0)),
            farmer=(int(fx), int(fy)),
            hands=hands,
            unlocked_quadrants=tuple(g(raw, "unlocked_quadrants", ["NW"]) or []),
            hires_today=int(g(raw, "hires_today", 0)),
            tiles=tiles,
        )

    self_farm = _parse_farm(player)
    opp_farm = _parse_farm(1 - player) if len(farms_raw) > 1 else self_farm

    mk = g(obs, "market", {}) or {}
    market = MarketState(
        inventory=dict(g(mk, "inventory", {}) or {}),
        prices=dict(g(mk, "prices", {}) or {}),
    )

    pv = g(obs, "private", {}) or {}
    invs_raw = g(pv, "inventories", [{}]) or [{}]
    private = PrivateState(
        shed=dict(g(pv, "shed", {}) or {}),
        seeds=dict(g(pv, "seeds", {}) or {}),
        inventories=tuple(dict(i) for i in invs_raw),
    )

    town = g(obs, "town", {}) or {}

    return GameState(
        step=step, day=day, hour=hour,
        self_farm=self_farm,
        opponent_farm=opp_farm,
        market=market,
        private=private,
        town_shops=tuple(g(town, "unlocked_shops", []) or []),
    )

# ===== INLINED: kaggriculture_bot/economy.py =====



# Step 718 is the last processed; it is day 29 hour 22.
LAST_STEP = EPISODE_STEPS - 2
LAST_GAME_DAY = LAST_STEP // TURNS_PER_DAY  # 29


# ---------------------------------------------------------------- market price
def _shape(func: str, x: float) -> float:
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "log10":
        return math.log10(1.0 + x)
    return x


def market_price(item: str, inventory: float, params: dict | None = None) -> int:
    """Exact replica of engine market_price (kaggriculture.py L177-191)."""
    p = (params or MARKET_PARAMS)[item]
    base, i0, t = p["base"], p["I0"], p["T"]
    if inventory < i0:
        amp = p["below_target"] * base / _shape(p["below_func"], t)
        price = base + amp * _shape(p["below_func"], i0 - inventory)
    else:
        amp = p["above_target"] * base / _shape(p["above_func"], t)
        price = base - amp * _shape(p["above_func"], inventory - i0)
    return max(PRICE_FLOOR, int(round(price)))


def sell_revenue(item: str, quantity: int, starting_inventory: float,
                 params: dict | None = None) -> int:
    """Exact per-unit lockstep revenue for selling `quantity` units.

    Matches engine: each unit priced at current inventory; inventory only
    increases for units sold at price > $1 (L633-635).
    """
    inv = starting_inventory
    revenue = 0
    for _ in range(max(0, quantity)):
        price = market_price(item, inv, params)
        revenue += price
        if price > PRICE_FLOOR:
            inv += 1
    return revenue


# ------------------------------------------------------------------- crops
def water_window(crop: str) -> tuple[int, int]:
    """Bonus watering window ages (inclusive) for one-time crops.

    Engine: window_start = (max_yield_day + 1) // 2; window is [start, max_yield_day].
    """
    c = CROPS[crop]
    start = (c["max_yield_day"] + 1) // 2
    return start, c["max_yield_day"]


def expected_yield(crop: str, harvest_age: int) -> int:
    """Yield at harvest_age assuming daily watering, no fertilizer (one-time crops).

    Engine semantics: yield starts at 1 on plant; watering on a window day adds +1.
    For ongoing crops this returns harvestable units at that production tick.
    """
    c = CROPS[crop]
    if harvest_age < c["first_yield_day"]:
        return 0
    if not c["ongoing"]:
        start, end = water_window(crop)
        bonus_days = max(0, min(harvest_age, end) - start + 1)
        return min(c["max_yield"], 1 + bonus_days)
    # ongoing: cumulative production ticks up to this age
    days_since_first = harvest_age - c["first_yield_day"] if harvest_age >= c["first_yield_day"] else -1
    if days_since_first < 0:
        return 0
    count = days_since_first // c["interval"] + 1
    return min(c["max_yield"], min(c["max_yield"], max(0, count)))


def first_harvest_day(crop: str, plant_day: int) -> int:
    return plant_day + CROPS[crop]["first_yield_day"]


def last_plant_day(crop: str, harvest_buffer: int = 0) -> int:
    """Latest day a crop can be planted such that its FIRST harvest still fits
    within the playable horizon (day 29)."""
    return LAST_GAME_DAY - CROPS[crop]["first_yield_day"] - harvest_buffer


def viable(crop: str, current_day: int, harvest_buffer: int = 0) -> bool:
    return current_day + CROPS[crop]["first_yield_day"] <= LAST_GAME_DAY - harvest_buffer


def crop_analysis(crop: str, current_day: int,
                  market_inventory: float | None = None,
                  params: dict | None = None,
                  harvest_buffer: int = 0) -> dict:
    """Full economics for one crop at one day. Does NOT decide anything."""
    c = CROPS[crop]
    is_feasible = viable(crop, current_day, harvest_buffer)
    harvest_age = 0

    # For one-time crops: harvest at max_yield_day (max unfertilized yield).
    # If horizon cuts it short, clamp harvest age to what fits.
    if c["ongoing"]:
        # 1. Full-horizon ongoing crop economics (Stage v040)
        # first_yield_day is when the first harvest of 1 unit happens.
        # Every interval days after that, another unit is produced, up to max_yield.
        first_harvest = current_day + c["first_yield_day"]
        days_available = LAST_GAME_DAY - harvest_buffer - first_harvest
        if days_available < 0:
            units = 0
            cycle_days = 1
            is_feasible = False
            harvest_age = 0
        else:
            units = min(c["max_yield"], 1 + (days_available // c["interval"]))
            cycle_days = c["first_yield_day"] + (units - 1) * c["interval"]
            harvest_age = cycle_days
    else:
        harvest_age = min(c["max_yield_day"], LAST_GAME_DAY - current_day)
        units = expected_yield(crop, harvest_age)
        cycle_days = max(1, harvest_age)

    inv = MARKET_I0 if market_inventory is None else market_inventory
    unit_price = market_price(crop, inv, params)
    revenue = sell_revenue(crop, units, inv, params)
    profit = revenue - c["seed_cost"]
    p = (params or MARKET_PARAMS)[crop]

    return {
        "crop": crop,
        "day": current_day,
        "feasible": is_feasible,
        "first_harvest_day": first_harvest_day(crop, current_day),
        "harvest_age": harvest_age,
        "expected_yield": units,
        "base_price": p["base"],
        "current_price": unit_price,
        "expected_revenue": revenue,
        "seed_cost": c["seed_cost"],
        "expected_profit": profit,
        "profit_per_day": profit / cycle_days,
        "profit_per_turn": profit / (cycle_days * TURNS_PER_DAY),
        "cycle_days": cycle_days,
        "risk_glut_above_target": p["above_target"],   # fractional crash per T flooded
        "price_if_flooded": market_price(crop, p["I0"] + p["T"], params),  # saturation price
        "last_plant_day": last_plant_day(crop, harvest_buffer),
    }


def crop_ranking(current_day: int,
                 market_inventory: dict[str, float] | None = None,
                 crops: list[str] | None = None,
                 params: dict | None = None) -> dict[str, dict]:
    """Per-crop analysis dict for a set of crops at a day.

    Returns {crop: analysis}. Does NOT choose — the caller decides with policy.
    """
    crops = crops or PHASE3_CROPS
    out = {}
    for crop in crops:
        inv = None if market_inventory is None else market_inventory.get(crop)
        out[crop] = crop_analysis(crop, current_day, inv, params=params)
    return out


def viable_crops(current_day: int, crops: list[str] | None = None,
                 harvest_buffer: int = 0) -> list[str]:
    crops = crops or PHASE3_CROPS
    return [c for c in crops if viable(c, current_day, harvest_buffer)]

# ===== INLINED: kaggriculture_bot/crop_allocator.py =====




def get_crop_plan(gs: GameState, empty_tiles: list[tuple[int, int]], crops_pool: list[str] | None = None) -> dict[tuple[int, int], str]:
    """Builds a single, consistent CropPlan mapping empty tiles -> crop to plant.

    Allocates empty tiles sequentially; after each allocation, updates the projected
    market inventory and recomputes the marginal crop value.
    """
    if crops_pool is None:
        crops_pool = PHASE3_CROPS

    day = gs.day
    # 1. Start with currently growing crops on both fields as our baseline projected market inventory
    proj_inv = {k: float(v) for k, v in gs.market.inventory.items()}
    for farm in (gs.self_farm, gs.opponent_farm):
        for row in farm.tiles:
            for tile in row:
                if tile.kind == "PLANT" and tile.crop in CROPS:
                    c = tile.crop
                    cd = CROPS[c]
                    # Estimate yield at max maturity
                    proj_inv[c] = proj_inv.get(c, 0.0) + expected_yield(c, cd["max_yield_day"])

    plan = {}

    # Sort empty tiles to ensure deterministic allocation order (e.g. sorted by coordinates)
    sorted_tiles = sorted(empty_tiles)

    for tile in sorted_tiles:
        best_crop = None
        best_profit = -99999.0

        for crop in crops_pool:
            if not viable(crop, day):
                continue

            cd = CROPS[crop]
            # Calculate marginal value of planting this crop on this tile today
            # We assume harvest at max maturity
            max_age = cd["max_yield_day"]
            units = expected_yield(crop, max_age)

            # The current projected inventory for this crop
            curr_proj = proj_inv.get(crop, float(MARKET_I0))

            # Expected revenue using exact sell_revenue (which simulates price decay)
            rev = sell_revenue(crop, units, curr_proj)
            profit = rev - cd["seed_cost"]

            if profit > best_profit and profit > 0:
                best_profit = profit
                best_crop = crop

        if best_crop:
            plan[tile] = best_crop
            # Update projected market inventory for subsequent allocations
            cd = CROPS[best_crop]
            units = expected_yield(best_crop, cd["max_yield_day"])
            proj_inv[best_crop] = proj_inv.get(best_crop, 0.0) + units

    return plan

# ===== INLINED: kaggriculture_bot/daily_planner.py =====




@dataclass
class DailyPlan:
    active_tiles: list[tuple[int, int]]
    crop_plan: dict[tuple[int, int], str]
    target_hands: int
    land_orders: list[list]
    cash_reserve: int


def compute_daily_plan(gs: GameState, include_strawberry: bool = True, include_land: bool = True) -> DailyPlan:
    day = gs.day
    money = gs.self_farm.money
    unlocked = gs.self_farm.unlocked_quadrants

    # Define layout profiles
    nearest_16 = [
        (3, 4), (4, 3), (2, 4), (3, 3), (4, 2), (1, 4), (2, 3), (3, 2),
        (4, 1), (0, 4), (1, 3), (2, 2), (3, 1), (4, 0), (0, 3), (1, 2)
    ]
    all_nw = [(x, y) for y in range(5) for x in range(5) if (x, y) != (4, 4)]

    # 1. Start from nearest_16, activate all 25 NW tiles when workload allows (day >= 4 and money >= 1200)
    if day >= 4 and money >= 1200:
        active_tiles = all_nw
    else:
        active_tiles = nearest_16

    # If NE is unlocked, we add all 25 plantable tiles in NE quadrant!
    if "NE" in unlocked:
        ne_tiles = [(x, y) for y in range(5) for x in range(5, 10) if (x, y) != (5, 4)]
        active_tiles = active_tiles + ne_tiles

    # 2. Buy land conditionally (to unlock NE)
    land_orders = []
    cash_reserve = 400
    if include_land and "NE" not in unlocked and 10 <= day <= 18:
        # Check safe cash reserve: land cost is $1000.
        # We require at least $2500 so we have at least $1500 remaining for robust seeds and hiring.
        if money >= 2500:
            land_orders.append(["BUY_LAND"])
            cash_reserve = 600  # keep a higher reserve on the turn we buy land

    # 3. Dynamic hand scaling
    # Scale hands dynamically up to 10/12 based on the number of active tiles:
    # - 16 tiles: 6 hands
    # - 25 tiles (NW): 8 hands
    # - 50 tiles (NW+NE): 12 hands
    n_tiles = len(active_tiles)
    if n_tiles <= 16:
        target_hands = 6
    elif n_tiles <= 25:
        target_hands = 8
    else:
        target_hands = 12

    # 4. Generate CropPlan
    farm = gs.self_farm
    empty_tiles = [tile for tile in active_tiles if farm.tile(tile[0], tile[1]).empty]

    crops_pool = ["WHEAT", "CARROT", "MELON"]
    if include_strawberry:
        crops_pool.append("STRAWBERRY")

    crop_plan = get_crop_plan(gs, empty_tiles, crops_pool=crops_pool)

    return DailyPlan(
        active_tiles=active_tiles,
        crop_plan=crop_plan,
        target_hands=target_hands,
        land_orders=land_orders,
        cash_reserve=cash_reserve
    )

# ===== INLINED: kaggriculture_bot/tasks.py =====



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

# Livestock tasks (Stage v041)
TASK_BUILD_PASTURE = "BUILD_PASTURE"
TASK_PICKUP = "PICKUP"
TASK_PLACE = "PLACE"
TASK_FEED = "FEED"
TASK_CARE = "CARE"
TASK_COLLECT_FERTILIZER = "COLLECT_FERTILIZER"
TASK_FERTILIZE = "FERTILIZE"

SHED_ACCESS_TILES = [(4, 4), (4, 5), (5, 4), (5, 5)]
PASTURE_TILES = [(3, 4), (4, 3), (3, 3), (2, 4)]


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


def generate_tasks(gs: GameState, managed_tiles: list[tuple[int, int]], crop_plan: dict[tuple[int, int], str] | None = None, include_livestock: bool = False) -> list[Task]:
    """Generate candidate tasks for this turn from the parsed game state."""
    tasks: list[Task] = []
    day, step = gs.day, gs.step
    last_step_today = (day + 1) * TURNS_PER_DAY - 1
    farm = gs.self_farm
    shed = gs.private.shed
    shed_total = sum(shed.values())

    # Exclude pasture tiles from crops when livestock is active
    if include_livestock:
        managed_tiles = [t for t in managed_tiles if t not in PASTURE_TILES]

    # Calculate alternative crop profit per day to evaluate opportunity cost of waiting
    ranking = crop_ranking(day, market_inventory={k: float(v) for k, v in gs.market.inventory.items()}, crops=list(CROPS.keys()))
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
                elif include_livestock and tile.kind == "PASTURE" and tile.animal_kind and tile.animal_yield > 0:
                    # Harvest animals at the very end
                    tasks.append(Task(
                        task_id=f"animal_harvest:{x},{y}", kind=TASK_HARVEST, target=(x, y),
                        priority_tier=TIER_DECAY, deadline_step=last_step_today,
                        expected_value=200.0,
                    ))
                    
        # Generate target-specific return/drop tasks per carrying unit
        _generate_unit_drop_tasks(gs, tasks, last_step_today)
        return tasks

    # ---- Tier 4: PLANT empty managed tiles using the shared CropPlan
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

    # ---- Stage v041: Livestock Lifecycle Tasks ----
    if include_livestock:
        _generate_livestock_tasks(gs, tasks, last_step_today)

    return tasks


def _generate_livestock_tasks(gs: GameState, tasks: list[Task], last_step_today: int):
    """Generates all livestock build/buy/pickup/place/feed/care/harvest tasks."""
    farm = gs.self_farm
    shed = gs.private.shed
    seeds = gs.private.seeds
    inventories = gs.private.inventories

    # 1. Check carrying animals
    carrying_cow = any(inv.get("COW", 0) > 0 for inv in inventories)
    carrying_sheep = any(inv.get("SHEEP", 0) > 0 for inv in inventories)

    # 2. Iterate through designated PASTURE_TILES
    for x, y in PASTURE_TILES:
        tile = farm.tile(x, y)
        
        # A) Build PASTURE if empty
        if tile.empty:
            tasks.append(Task(
                task_id=f"build_pasture:{x},{y}", kind=TASK_BUILD_PASTURE, target=(x, y),
                priority_tier=TIER_ROUTINE, deadline_step=last_step_today,
                expected_value=100.0,
            ))
            continue
            
        # B) If tile is PASTURE and has no animal placed
        if tile.kind == "PASTURE" and not tile.animal_kind:
            # If we are carrying an animal, place it!
            if carrying_cow:
                tasks.append(Task(
                    task_id=f"place_cow:{x},{y}", kind=TASK_PLACE, target=(x, y),
                    priority_tier=TIER_DECAY, deadline_step=last_step_today,
                    expected_value=400.0, crop="COW",
                ))
            elif carrying_sheep:
                tasks.append(Task(
                    task_id=f"place_sheep:{x},{y}", kind=TASK_PLACE, target=(x, y),
                    priority_tier=TIER_DECAY, deadline_step=last_step_today,
                    expected_value=500.0, crop="SHEEP",
                ))
            # Else if we have bought animals waiting in shed, generate a PICKUP task!
            elif shed.get("COW", 0) > 0:
                tasks.append(Task(
                    task_id=f"pickup_cow:{x},{y}", kind=TASK_PICKUP, target=None, # picked up from nearest shed tile
                    priority_tier=TIER_LOGISTICS, deadline_step=last_step_today,
                    expected_value=400.0, required_item="COW",
                ))
            elif shed.get("SHEEP", 0) > 0:
                tasks.append(Task(
                    task_id=f"pickup_sheep:{x},{y}", kind=TASK_PICKUP, target=None,
                    priority_tier=TIER_LOGISTICS, deadline_step=last_step_today,
                    expected_value=500.0, required_item="SHEEP",
                ))
            continue

        # C) If tile has an animal, handle Feed, Care, and Harvest lifecycle
        if tile.kind == "PASTURE" and tile.animal_kind:
            ak = tile.animal_kind
            
            # Feed animal (Wheat required). Zero escape requirement: feed highly urgently if unfed >= 1.
            if not tile.animal_fed_today:
                dying = tile.animal_unfed >= 1
                tasks.append(Task(
                    task_id=f"feed:{ak}:{x},{y}", kind=TASK_FEED, target=(x, y),
                    priority_tier=TIER_DYING if dying else TIER_ROUTINE,
                    deadline_step=last_step_today,
                    expected_value=200.0 if dying else 50.0,
                    required_item="WHEAT",
                ))
                
            # Care animal
            if not tile.animal_cared_today:
                tasks.append(Task(
                    task_id=f"care:{ak}:{x},{y}", kind=TASK_CARE, target=(x, y),
                    priority_tier=TIER_ROUTINE, deadline_step=last_step_today,
                    expected_value=30.0,
                ))
                
            # Harvest animal yield
            if tile.animal_yield > 0:
                tasks.append(Task(
                    task_id=f"animal_harvest:{ak}:{x},{y}", kind=TASK_HARVEST, target=(x, y),
                    priority_tier=TIER_HARVEST_HIGH, deadline_step=last_step_today,
                    expected_value=250.0 if ak == "COW" else 300.0,
                ))
                
            # Collect fertilizer
            if tile.fertilizer_available:
                tasks.append(Task(
                    task_id=f"collect_fert:{x},{y}", kind=TASK_COLLECT_FERTILIZER, target=(x, y),
                    priority_tier=TIER_LOGISTICS, deadline_step=last_step_today,
                    expected_value=100.0,
                ))

    # 3. Route fertilizer to STRAWBERRY plants
    # Only if we have FERTILIZER in shed, and we have growing STRAWBERRY that is not yet fertilized today.
    # Marginal value of strawberry fertilized is +1 strawberry (~$120) which exceeds fertilizer sale value (~$100).
    if shed.get("FERTILIZER", 0) > 0:
        for y in range(farm.tiles.__len__()):
            for x in range(farm.tiles[y].__len__()):
                tile = farm.tiles[y][x]
                if tile.kind == "PLANT" and tile.crop == "STRAWBERRY" and tile.fertilized_until_day <= gs.day:
                    tasks.append(Task(
                        task_id=f"fertilize_strawberry:{x},{y}", kind=TASK_FERTILIZE, target=(x, y),
                        priority_tier=TIER_LOGISTICS, deadline_step=last_step_today,
                        expected_value=120.0, required_item="FERTILIZER",
                    ))


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
        
        # In Stage v041, we do NOT want to drop COW or SHEEP to the shed (they must be placed on pasture).
        # We also do NOT want to drop FERTILIZER if we plan to use it to fertilize, but dropping is safe.
        # To be safe, we only drop product items (WHEAT, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, FERTILIZER).
        # We explicitly exclude animals "COW" or "SHEEP" from the sum.
        carrying_items = {k: v for k, v in inv.items() if k not in ("COW", "SHEEP")}
        qty = sum(carrying_items.values())
        
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

# ===== INLINED: kaggriculture_bot/assignment.py =====



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

# ===== INLINED: kaggriculture_bot/hire_manager.py =====




def _fib(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def next_hire_cost(hires_today: int, mult: int = FARM_HAND_COST_MULT) -> int:
    return mult * _fib(hires_today)


def _spawn_pos(gs: GameState) -> tuple[int, int]:
    half = BOARD_SIZE // 2
    return (half - 1, half - 1)  # (4,4) NW shed tile adjacent


def _day_completion_value(gs: GameState, tasks: list[Task], start_positions: list[tuple[int, int]],
                          n_existing: int, hours_left_for_hands: int, hours_left_for_current_units: int) -> float:
    """Greedy same-day simulation.

    Different free-hour starting points:
    - current units (farmer + already hired hands) start working CURRENT hour (available_at=0)
    - newly hired hands start working NEXT hour (available_at=1)
    """
    # Exclude mutually exclusive tasks at the same coordinates.
    # We only take the HIGHEST profit task per tile position in the simulation.
    best_on_tile: dict[tuple, Task] = {}
    for t in tasks:
        if t.target is not None:
            pos = t.target
            if pos not in best_on_tile or t.expected_value > best_on_tile[pos].expected_value:
                best_on_tile[pos] = t
    filtered_tasks = list(best_on_tile.values())

    ordered = sorted(filtered_tasks, key=lambda t: (t.priority_tier, -t.expected_value))
    
    # 4. Fix hire_manager new-hand availability:
    # - existing units available_at = 0
    # - every hand planned this turn available_at = 1
    # - actually use availability in finish-time computation.
    available_at = [0] * n_existing + [1] * (len(start_positions) - n_existing)
    free_at = list(available_at)
        
    pos = list(start_positions)
    total = 0.0
    
    # Simple simulator
    for t in ordered:
        if t.target is None:
            continue
        tgt = t.target
        best_i, best_finish = -1, 1_000_000
        for i in range(len(pos)):
            d = abs(pos[i][0] - tgt[0]) + abs(pos[i][1] - tgt[1])
            # Use availability in finish-time computation: max(free_at[i], available_at[i]) is already free_at[i]
            finish = free_at[i] + d + 1
            if finish < best_finish:
                best_i, best_finish = i, finish
                
        if best_i < 0:
            continue
            
        # Limit reachability check based on role
        limit = hours_left_for_hands if best_i >= n_existing else hours_left_for_current_units
        if best_finish <= limit:
            total += t.expected_value
            free_at[best_i] = best_finish
            pos[best_i] = tgt
            
    return total


def plan_hires(gs: GameState, tasks: list[Task], max_hands: int = 6,
               coordination_penalty: float = 10.0, cash_reserve: int = 400) -> int:
    """Return the optimal number of hands to hire THIS TURN via sequential marginal value.

    Simulates the diminishing returns of adding hands step-by-step.
    """
    farm = gs.self_farm
    hour = gs.hour
    hours_left_current = TURNS_PER_DAY - hour
    hours_left_hands = hours_left_current - 1  # new hands act next turn at earliest

    if hours_left_hands < 4:
        return 0  # too late in the day to buy same-day capacity

    planned_hires = 0
    current_money = farm.money
    current_hires_today = farm.hires_today
    current_hands_count = farm.hand_count
    n_existing = 1 + current_hands_count

    # Positions pool for simulation
    unit_positions = [farm.farmer] + list(farm.hands)

    while current_hands_count + planned_hires < max_hands:
        cost = next_hire_cost(current_hires_today + planned_hires)
        if current_money - cost < cash_reserve:
            break

        # Calculate base value with current simulation group
        base_val = _day_completion_value(
            gs, tasks, unit_positions, n_existing,
            hours_left_hands, hours_left_current
        )

        # Append one phantom hand at spawn
        phantom_positions = unit_positions + [_spawn_pos(gs)]
        with_hand_val = _day_completion_value(
            gs, tasks, phantom_positions, n_existing,
            hours_left_hands, hours_left_current
        )

        marginal_value = with_hand_val - base_val
        
        # Diminishing return gate
        if marginal_value > cost + coordination_penalty:
            planned_hires += 1
            current_money -= cost
            unit_positions = phantom_positions  # keep it for the next hand's base
        else:
            break

    return planned_hires


def should_hire(gs: GameState, tasks: list[Task], coordination_penalty: float = 10.0,
                cash_reserve: int = 400) -> bool:
    """True iff sequential simulation recommends hiring at least 1 hand."""
    return plan_hires(gs, tasks, max_hands=1, coordination_penalty=coordination_penalty, cash_reserve=cash_reserve) > 0

# ===== INLINED: kaggriculture_bot/policy.py =====



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
        
        # Support 2 cows + 2 sheep only (Stage v041 / v050)
        # Limit purchases to day <= 14 and require robust cash reserve so we don't starve crops.
        if 2 <= gs.day <= 14:
            if total_cows + pending_cows < 2 and money >= cash_reserve + 1000:
                market_orders.append(["BUY_ANIMAL", "COW", 1])
                money -= 400.0
            if total_sheep + pending_sheep < 2 and money >= cash_reserve + 1200:
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

# ===== INLINED: kaggriculture_bot/harness.py =====

import traceback

# Global counter per loaded module instance. The eval harness reads it to count
# silent fallbacks (should hard-fail for the champion in test contexts).
FALLBACK_COUNT = {"n": 0, "traces": []}

DEBUG_RAISE_ENV = "KAGGRI_DEBUG_RAISE"


def make_agent(core_fn, observed_hand_count_fn=None, hands_fallback_min: int = 0):
    """Return an agent function that wraps a pure core_fn.

    core_fn(obs, config=None) -> dict action. If it raises:
      - KAGGRI_DEBUG_RAISE=1   -> re-raise (loud; for tests and local league)
      - otherwise              -> increment FALLBACK_COUNT and return safe PASS
    """
    def agent(obs, config=None):
        try:
            return core_fn(obs, config)
        except Exception:
            if os.environ.get(DEBUG_RAISE_ENV, "") == "1":
                raise
            FALLBACK_COUNT["n"] += 1
            FALLBACK_COUNT["traces"].append(traceback.format_exc())
            # Try to size hands correctly for fallback.
            n = observed_hand_count_fn(obs) if observed_hand_count_fn else hands_fallback_min
            return {"farmer": ["PASS"], "hands": [["PASS"]] * max(0, n), "market": []}

    # Keep a back-pointer so a debugger can find the core.
    agent.__name__ = "agent"
    agent._core = core_fn
    return agent


def hand_count_from_obs(obs) -> int:
    try:
        farms = obs.get("farms", []) if isinstance(obs, dict) else getattr(obs, "farms", [])
        player = obs.get("player", 0) if isinstance(obs, dict) else getattr(obs, "player", 0)
        hands = farms[player].get("hands", []) if farms and player < len(farms) else []
        return len(hands) if isinstance(hands, list) else 0
    except Exception:
        return 0

# ===== AGENT =====




# Master Ablation Flags (patchable by evaluation suite)
INCLUDE_STRAWBERRY = True
INCLUDE_LAND = True
INCLUDE_LIVESTOCK = False

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

    # 1. Compute DailyPlan incorporating land, strawberry and livestock
    dp = compute_daily_plan(gs, include_strawberry=INCLUDE_STRAWBERRY, include_land=INCLUDE_LAND)

    # 2. Generate tasks (watering, digging, planting, harvesting, livestock lifecycle, fertilizing)
    tasks = generate_tasks(
        gs, dp.active_tiles,
        crop_plan=dp.crop_plan,
        include_livestock=INCLUDE_LIVESTOCK
    )
    assignments = greedy_assign(gs, tasks)

    farmer_action = assignments[0].action if assignments else ["PASS"]
    hands_actions = [a.action for a in assignments[1:]]

    # 3. Market orders incorporating sequential hiring, wheat feed buffers, and animal purchases
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
