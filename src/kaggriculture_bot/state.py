"""Observation parsing into clean data objects. No planner state.

state.py is intentionally a pure view over the engine observation:
- no intents, no plans, no persistent identity across calls
- all derived quantities via properties
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from .constants import BOARD_SIZE, DAYS, EPISODE_STEPS, TURNS_PER_DAY


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
            if animal_raw is not None:
                animal_kind = animal_raw if isinstance(animal_raw, str) else g(animal_raw, "kind")
                animal_yield = int(g(raw, "yield_units", 0))
                animal_unfed = int(g(raw, "consecutive_unfed", 0))
                animal_cared_today = bool(g(raw, "cared_today", False))
                animal_fed_today = bool(g(raw, "fed_today", False))
                fert_avail = bool(g(raw, "fertilizer_available", False))
                
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
