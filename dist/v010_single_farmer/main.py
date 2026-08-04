"""Auto-generated single-file Kaggressriculture agent. Do not edit by hand."""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
import math


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
                )
            if kind == "WEED":
                return cls(x, y, "WEED")
            return cls(x, y, kind)
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

    # For one-time crops: harvest at max_yield_day (max unfertilized yield).
    # If horizon cuts it short, clamp harvest age to what fits.
    if c["ongoing"]:
        # For ongoing crops, Phase 3 does not use them; report basic first-tick info.
        harvest_age = c["first_yield_day"]
        units = expected_yield(crop, harvest_age)
        cycle_days = max(1, c["first_yield_day"])
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

# ===== AGENT =====




# Managed tiles: a fixed 2x3 work block in the NW quadrant around spawn.
MANAGED_TILES = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (3, 4)]

_EP = {}


def _reset_episode_state():
    global _EP
    _EP = {}


def _tile_crop_plan(day: int) -> list:
    """Per-tile crop intent for managed tiles, given day and horizon.

    Slots 0-1 plant MELON early only (single farmer can't service late melons
    and season horizon), then fall back to CARROT/WHEAT. Slots 2-3 favor
    CARROT for liquidity, slots 4-5 WHEAT as terminal fallback.
    """
    plan = [None] * len(MANAGED_TILES)
    melon_ok = day <= min(last_plant_day("MELON"), 8)
    carrot_ok = day <= last_plant_day("CARROT")
    wheat_ok = day <= last_plant_day("WHEAT")
    for i in range(2):
        plan[i] = "MELON" if melon_ok else ("CARROT" if carrot_ok else ("WHEAT" if wheat_ok else None))
    for i in (2, 3):
        plan[i] = "CARROT" if carrot_ok else ("WHEAT" if wheat_ok else None)
    for i in (4, 5):
        plan[i] = "WHEAT" if wheat_ok else None
    return plan


def _manhattan_step(fx: int, fy: int, tx: int, ty: int) -> str:
    if fx < tx:
        return "EAST"
    if fx > tx:
        return "WEST"
    if fy < ty:
        return "SOUTH"
    return "NORTH"  # only called when not equal


def _seed_restock(gs, plan) -> list:
    """Market orders to ensure one seed per empty managed tile with a plan."""
    orders = []
    seeds = gs.private.seeds
    day = gs.day
    want = {}
    for i, (x, y) in enumerate(MANAGED_TILES):
        crop = plan[i]
        if crop is None:
            continue
        tile = gs.self_farm.tile(x, y)
        if tile.empty and seeds.get(crop, 0) <= 0 and crop not in want:
            want[crop] = 2
    for crop, n in want.items():
        if gs.self_farm.money >= CROPS[crop]["seed_cost"] * n:
            orders.append(["BUY_SEED", crop, n])
    return orders


def _next_job_tile(gs, plan, fx: int, fy: int):
    """Closest managed tile (manhattan) with a pending job, in fixed tile order."""
    day = gs.day
    seeds = gs.private.seeds
    for i, (x, y) in enumerate(MANAGED_TILES):
        if (x, y) == (fx, fy):
            continue
        tile = gs.self_farm.tile(x, y)
        if tile.kind == "WEED":
            return (x, y)
        if tile.kind == "PLANT":
            cd = CROPS.get(tile.crop, {})
            if tile.yield_units > 0 and tile.age(day) >= cd.get("first_yield_day", 0):
                return (x, y)
            if not tile.watered_today:
                return (x, y)
        elif tile.empty and plan[i] and seeds.get(plan[i], 0) > 0:
            return (x, y)
    return None


def agent(obs, config=None):
    try:
        gs = parse_state(obs)
        if gs.step == 0:
            _reset_episode_state()

        farm = gs.self_farm
        private = gs.private
        seeds = private.seeds
        shed = private.shed
        day = gs.day
        fx, fy = farm.farmer
        tile = farm.tile(fx, fy)

        plan = _tile_crop_plan(day)

        # ---------------- market ----------------
        market = []
        for item in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
            n = shed.get(item, 0)
            if n > 0:
                market.append(["SELL", item, n])
        market.extend(_seed_restock(gs, plan))
        market = market[:10]

        # ---------------- farmer ----------------
        farmer_action = ["PASS"]
        crop = tile.crop if tile.kind == "PLANT" else None
        age = tile.age(day) if tile.kind == "PLANT" else -1
        squeeze = day >= LAST_GAME_DAY - 1  # day 28/29: harvest anything mature

        # 1) HARVEST: full-yield plant, or terminal squeeze of anything mature.
        if crop is not None and tile.yield_units > 0:
            cd = CROPS[crop]
            if age >= cd["max_yield_day"] or squeeze:
                farmer_action = ["HARVEST"]
        # 2) WATER: same-day survival rule (planting day counts as unwatered).
        if farmer_action == ["PASS"] and tile.kind == "PLANT" and not tile.watered_today:
            farmer_action = ["WATER"]
        # 3) PLANT: empty managed tile under farmer with feasible plan + seed.
        if farmer_action == ["PASS"] and tile.empty and (fx, fy) in MANAGED_TILES:
            i = MANAGED_TILES.index((fx, fy))
            c = plan[i]
            if c and seeds.get(c, 0) > 0:
                farmer_action = ["PLANT", c]
        # 4) Move toward the next managed tile with a pending job.
        if farmer_action == ["PASS"]:
            tgt = _next_job_tile(gs, plan, fx, fy)
            if tgt is not None:
                farmer_action = [_manhattan_step(fx, fy, tgt[0], tgt[1])]

        return safe_action(
            raw_farmer=farmer_action,
            raw_hands=[],
            raw_market=market,
            observed_hand_count=farm.hand_count,
            seeds=seeds,
        )
    except Exception:
        try:
            hands = obs.get("farms", [{}])[obs.get("player", 0)].get("hands", []) if isinstance(obs, dict) else []
            n = len(hands) if isinstance(hands, list) else 0
        except Exception:
            n = 0
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
