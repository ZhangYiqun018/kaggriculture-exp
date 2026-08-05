"""Phase 3R.3: Repaired metrics correctness tests."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot.metrics import outcome_score, wilson_lower_bound  # noqa: E402


def test_outcome_scoring():
    assert outcome_score(100, 50) == 1.0
    assert outcome_score(50, 100) == 0.0
    assert outcome_score(50, 50) == 0.5


def test_wilson_score_lower_bound():
    # 100% wins of 10 matches
    lb1 = wilson_lower_bound(10, 10)
    assert lb1 > 0.50
    # 50% wins of 100 matches
    lb2 = wilson_lower_bound(50, 100)
    assert 0.35 <= lb2 <= 0.45
    # 0 wins of 10 matches
    assert wilson_lower_bound(0, 10) == 0.0
