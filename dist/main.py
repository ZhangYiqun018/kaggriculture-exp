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
    return task.target


def _conflict_key(task: Task) -> str | None:
    """Returns a key for exclusive spatial/resource conflict prevention.

    For spatial tasks, the tile coordinate (x,y) is the exclusive key: only
    one unit can work on a tile per turn.
    """
    if task.kind == TASK_DROP:
        return "shed:drop"
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

    # 2) Carrying check for DROP
    if task.kind == TASK_DROP:
        return sum(unit.inventory.values()) > 0

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




MANAGED_TILES = [
    (2, 2), (3, 2), (4, 2), (2, 3), (3, 3), (4, 3),
    (2, 4), (3, 4), (1, 2), (1, 3), (1, 1), (2, 1), (3, 1), (0, 0), (1, 0), (0, 1),
]
TARGET_HANDS_DAY = 6

_EP = {}


def _reset_episode_state():
    global _EP
    _EP = {}


def _seed_demand(gs, tasks) -> dict:
    need: dict = {}
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


def core_agent(obs, config=None):
    gs = parse_state(obs)
    if gs.step == 0:
        _reset_episode_state()

    farm = gs.self_farm
    private = gs.private
    shed = private.shed
    seeds = private.seeds

    tasks = generate_tasks(gs, MANAGED_TILES)
    assignments = greedy_assign(gs, tasks)

    farmer_action = assignments[0].action if assignments else ["PASS"]
    hands_actions = [a.action for a in assignments[1:]]

    market = []
    for item in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                 "EGG", "MILK", "WOOL", "FERTILIZER"):
        n = shed.get(item, 0)
        if n > 0:
            market.append(["SELL", item, n])

    # HIRE: True sequential marginal hiring with diminishing returns (Phase 3R.5).
    # We query plan_hires ONCE to get the globally optimal planned hires for today.
    optimal_hires = plan_hires(gs, tasks, max_hands=TARGET_HANDS_DAY, cash_reserve=400)
    for _ in range(optimal_hires):
        if len(market) >= 10:
            break
        market.append(["HIRE"])

    for crop, n in _seed_demand(gs, tasks).items():
        if len(market) >= 10:
            break
        if n > 0 and farm.money >= CROPS[crop]["seed_cost"] * n:
            market.append(["BUY_SEED", crop, n])
    market = market[:10]

    return safe_action(
        raw_farmer=farmer_action,
        raw_hands=hands_actions,
        raw_market=market,
        observed_hand_count=farm.hand_count,
        seeds=seeds,
    )


agent = make_agent(core_agent, observed_hand_count_fn=hand_count_from_obs)
