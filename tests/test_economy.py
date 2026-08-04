"""Phase 3.0: economy model tests.

The strongest test here is *parity against the engine itself*: our pure
market_price / sell_revenue replicas are compared cell-by-cell against the
installed kaggriculture.py functions, so the local truth cannot drift
from the real runtime.
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot import economy  # noqa: E402
from kaggriculture_bot.constants import CROPS, MARKET_PARAMS, PRODUCTS  # noqa: E402

ENGINE_PATH = ROOT / ".venv/lib/python3.12/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py"


def _load_engine():
    spec = importlib.util.spec_from_file_location("kagg_engine", str(ENGINE_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ENGINE = _load_engine() if ENGINE_PATH.exists() else None


# ---------------------------------------------------------------- price parity
@pytest.mark.skipif(ENGINE is None, reason="engine source not found")
def test_market_price_parity_all_products_full_grid():
    """Our market_price must match engine market_price for every product over a wide inventory grid."""
    for item in PRODUCTS:
        for inv in range(9900, 10401, 5):
            ours = economy.market_price(item, inv)
            theirs = ENGINE.market_price(item, inv)
            assert ours == theirs, f"{item}@{inv}: ours={ours} engine={theirs}"


def test_market_price_known_values():
    assert economy.market_price("WHEAT", 10000) == 25     # at I0 -> base
    assert economy.market_price("MELON", 10100) == 150    # 100 flooded: 250 -> 150
    assert economy.market_price("MELON", 10300) == 1      # 300 flooded: sq crash to floor


def test_price_floor_respected():
    huge = 10000 + 100_000
    for item in PRODUCTS:
        assert economy.market_price(item, huge) >= 1


# ---------------------------------------------------------------- sell revenue
@pytest.mark.skipif(ENGINE is None, reason="engine source not found")
def test_sell_revenue_parity_with_engine_loop():
    """Sell revenue computed the way the engine's commit loop does it."""
    for item in ["WHEAT", "MELON", "STRAWBERRY"]:
        for qty in (1, 5, 50, 300):
            inv = MARKET_I0 = 10000
            rev_engine = 0
            for _ in range(qty):
                price = ENGINE.market_price(item, inv)
                rev_engine += price
                if price > 1:
                    inv += 1
            assert economy.sell_revenue(item, qty, 10000) == rev_engine, (
                f"{item} x{qty}: ours={economy.sell_revenue(item, qty, 10000)} engine={rev_engine}")


def test_sell_revenue_floor_stall():
    """At price $1, further sales give $1 each and do NOT raise inventory."""
    rev = economy.sell_revenue("MELON", 1000, 10000)
    # 300+ units crash melon to $1; excess sells at $1 with no supply feedback.
    assert rev < 1000 * 250
    assert rev > 0


# ---------------------------------------------------------------- crop yields
def test_expected_yield_wheat():
    # WHEAT: window_start = (4+1)//2 = 2; daily water; age2->1+1, age3->1+2, age4->1+3=4
    assert economy.expected_yield("WHEAT", 1) == 0   # before first_yield_day
    assert economy.expected_yield("WHEAT", 2) == 2
    assert economy.expected_yield("WHEAT", 3) == 3
    assert economy.expected_yield("WHEAT", 4) == 4


def test_expected_yield_carrot():
    assert economy.expected_yield("CARROT", 2) == 2
    assert economy.expected_yield("CARROT", 3) == 3


def test_expected_yield_melon():
    # MELON: first_yield_day=10, window_start=6; age 10 -> 1+(10-6+1)=6 = max_yield
    assert economy.expected_yield("MELON", 9) == 0
    assert economy.expected_yield("MELON", 10) == 6
    assert economy.expected_yield("MELON", 12) == 6


# ---------------------------------------------------------------- economics
def test_wheat_roi_day0():
    a = economy.crop_analysis("WHEAT", 0)
    assert a["expected_yield"] == 4
    # Lockstep selling decays price per unit: 25+24+24+24 = 97, not 4*25=100.
    # (Even tiny quantities move the log above-curve.) Parity-verified vs engine.
    assert a["expected_revenue"] == 97
    assert a["seed_cost"] == 10
    assert a["expected_profit"] == 87
    assert a["profit_per_day"] == pytest.approx(87 / 4)


def test_carrot_roi_day0():
    a = economy.crop_analysis("CARROT", 0)
    assert a["expected_yield"] == 3
    # Lockstep: 35+34+33 = 102 (sqrt above-curve), not 3*35=105.
    assert a["expected_revenue"] == 102
    assert a["seed_cost"] == 20
    assert a["expected_profit"] == 82
    assert a["profit_per_day"] == pytest.approx(82 / 3)


def test_melon_economics_and_crash_risk():
    a = economy.crop_analysis("MELON", 0)
    assert a["expected_yield"] == 6
    assert a["expected_profit"] == 6 * 250 - 80
    assert a["risk_glut_above_target"] == 3.60
    # Saturation price (a full T=300 field flooded): $1 floor.
    assert a["price_if_flooded"] == 1


def test_wheat_gentle_vs_melon_severe():
    """Wheat absorbs supply gently; melon crashes hard. Core market-diversification signal."""
    wheat_sat = economy.market_price("WHEAT", 10000 + 400)   # T=400
    melon_sat = economy.market_price("MELON", 10000 + 300)   # T=300
    assert wheat_sat >= 20    # drops from 25 to ~20
    assert melon_sat == 1     # crashes to floor


# ---------------------------------------------------------------- horizon
def test_day_0_all_viable():
    vc = economy.viable_crops(0)
    assert set(vc) == {"WHEAT", "CARROT", "MELON"}


def test_day_15_ranking():
    """Day 15: melon still feasible (15+10=25 <= 29) but tight."""
    vc = economy.viable_crops(15)
    assert "WHEAT" in vc and "CARROT" in vc and "MELON" in vc


def test_day_25_only_short_crops():
    """Day 25: melon (25+10=35) infeasible; wheat/carrot (27) still feasible."""
    vc = economy.viable_crops(25)
    assert "MELON" not in vc
    assert "WHEAT" in vc
    assert "CARROT" in vc


def test_day_28_nothing_plantable_unbuffered_cutoff():
    """Day 28: even wheat needs 30 = 28+2 > 29 -> infeasible."""
    vc = economy.viable_crops(28)
    assert vc == []


def test_last_plant_days():
    assert economy.last_plant_day("WHEAT") == 27   # 29 - 2
    assert economy.last_plant_day("CARROT") == 27  # 29 - 2
    assert economy.last_plant_day("MELON") == 19   # 29 - 10


# ---------------------------------------------------------------- ranking output
def test_ranking_day0_structure():
    r = economy.crop_ranking(0)
    assert set(r) == {"WHEAT", "CARROT", "MELON"}
    for crop, a in r.items():
        assert {"expected_profit", "profit_per_turn", "risk_glut_above_target"} <= set(a)


def test_ranking_day0_profit_per_day_order():
    """Unfertilized, undisturbed market: MELON >> CARROT > WHEAT on profit/day."""
    r = economy.crop_ranking(0)
    assert r["MELON"]["profit_per_day"] > r["CARROT"]["profit_per_day"]
    assert r["CARROT"]["profit_per_day"] > r["WHEAT"]["profit_per_day"]


def test_ranking_day25_excludes_melon_feasible_flag():
    r = economy.crop_ranking(25)
    assert r["MELON"]["feasible"] is False
    assert r["WHEAT"]["feasible"] is True
