"""Tests for the safety layer (src/kaggriculture_bot/safety.py)."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot.safety import safe_action, _seed_budget_plant_check  # noqa: E402


def test_farmer_action_invalid_becomes_pass():
    r = safe_action("NOT A LIST", [], [], 0, {})
    assert r["farmer"] == ["PASS"]


def test_farmer_unknown_op_becomes_pass():
    r = safe_action(["FLY"], [], [], 0, {})
    assert r["farmer"] == ["PASS"]


def test_hands_padded_to_observed_count():
    r = safe_action(["PASS"], [["NORTH"]], [], 3, {})
    assert len(r["hands"]) == 3
    assert r["hands"][0] == ["NORTH"]
    assert r["hands"][1] == ["PASS"]
    assert r["hands"][2] == ["PASS"]


def test_hands_truncated_to_observed_count():
    r = safe_action(["PASS"], [["NORTH"], ["SOUTH"], ["EAST"]], [], 1, {})
    assert len(r["hands"]) == 1
    assert r["hands"][0] == ["NORTH"]


def test_invalid_hand_action_replaced():
    r = safe_action(["PASS"], [["FLY"], [123], []], [], 3, {})
    assert r["hands"] == [["PASS"], ["PASS"], ["PASS"]]


def test_market_capped_at_10():
    orders = [["SELL", "WHEAT", 1]] * 15
    r = safe_action(["PASS"], [], orders, 0, {})
    assert len(r["market"]) == 10


def test_market_invalid_orders_filtered():
    orders = [["SELL", "WHEAT", 1], "bad", ["FLY", "X", 1], ["SELL"], ["SELL", "WHEAT", 0], ["SELL", "WHEAT", -1], ["HIRE"]]
    r = safe_action(["PASS"], [], orders, 0, {})
    # Valid: SELL WHEAT 1, HIRE
    assert len(r["market"]) == 2
    assert r["market"][0] == ["SELL", "WHEAT", 1]
    assert r["market"][1] == ["HIRE"]


def test_plant_atomicity_blocks_all_when_over_seed():
    # 1 seed, farmer + 1 hand both PLANT WHEAT -> both PASS
    farmer, hands = _seed_budget_plant_check(["PLANT", "WHEAT"], [["PLANT", "WHEAT"]], {"WHEAT": 1})
    assert farmer == ["PASS"]
    assert hands == [["PASS"]]


def test_plant_atomicity_allows_when_exact_seed():
    farmer, hands = _seed_budget_plant_check(["PLANT", "WHEAT"], [["PLANT", "WHEAT"]], {"WHEAT": 2})
    assert farmer == ["PLANT", "WHEAT"]
    assert hands == [["PLANT", "WHEAT"]]


def test_plant_atomicity_only_blocks_over_crop():
    # 2 seeds, 3 PLANT requests -> all blocked
    farmer, hands = _seed_budget_plant_check(["PLANT", "WHEAT"], [["PLANT", "WHEAT"], ["PLANT", "WHEAT"]], {"WHEAT": 2})
    assert farmer == ["PASS"]
    assert hands == [["PASS"], ["PASS"]]


def test_plant_different_crops_independent():
    # 1 WHEAT, 1 CARROT; 2 WHEAT plant (blocked) + 1 CARROT (ok)
    farmer, hands = _seed_budget_plant_check(["PLANT", "WHEAT"], [["PLANT", "WHEAT"], ["PLANT", "CARROT"]], {"WHEAT": 1, "CARROT": 1})
    assert farmer == ["PASS"]  # WHEAT blocked
    assert hands[0] == ["PASS"]  # WHEAT blocked
    assert hands[1] == ["PLANT", "CARROT"]  # CARROT ok


def test_exception_fallback():
    # Pass a non-dict for seeds to trigger exception in _seed_budget... no, it handles None.
    # Force exception by passing unhashable weird input.
    class Bad:
        def get(self, k, d=None):
            raise RuntimeError("boom")
    r = safe_action(["PASS"], [], [], 2, Bad())
    assert r["farmer"] == ["PASS"]
    assert r["hands"] == [["PASS"], ["PASS"]]
    assert r["market"] == []


def test_never_returns_empty_farmer():
    # Even with None input, farmer must be a non-empty list.
    r = safe_action(None, None, None, 0, None)
    assert isinstance(r["farmer"], list) and len(r["farmer"]) > 0
