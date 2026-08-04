"""Auto-generated single-file Kaggressriculture agent. Do not edit by hand."""
from __future__ import annotations
from typing import Any

# ===== INLINED: kaggriculture_bot/safety.py =====
from typing import Any

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

    Mirrors the engine's atomic PLANT validation (kaggressriculture.py L889-902).
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

# ===== AGENT =====
"""v000_pass: submission-safe skeleton agent.

Always returns PASS for farmer and hands, empty market.
Hands count is matched to observation via the safety layer.
"""


# Allow importing the safety layer when run from source (dev mode).


_EPISODE_STATE = {}


def _reset_episode_state():
    global _EPISODE_STATE
    _EPISODE_STATE = {}


def agent(obs, config=None):
    try:
        step = obs.get("step", 0) if isinstance(obs, dict) else 0
        if step == 0:
            _reset_episode_state()

        player = obs.get("player", 0) if isinstance(obs, dict) else 0
        farms = obs.get("farms", []) if isinstance(obs, dict) else []
        farm = farms[player] if farms and player < len(farms) else {}
        hands = farm.get("hands", []) if isinstance(farm, dict) else []
        private = obs.get("private", {}) if isinstance(obs, dict) else {}
        seeds = private.get("seeds", {}) if isinstance(private, dict) else {}

        observed_hand_count = len(hands) if isinstance(hands, list) else 0
        return safe_action(
            raw_farmer=["PASS"],
            raw_hands=[["PASS"]] * observed_hand_count,
            raw_market=[],
            observed_hand_count=observed_hand_count,
            seeds=seeds,
        )
    except Exception:
        # Absolute last-resort fallback.
        try:
            hands = obs.get("farms", [{}])[0].get("hands", []) if isinstance(obs, dict) else []
            n = len(hands) if isinstance(hands, list) else 0
        except Exception:
            n = 0
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}
