"""Bridge to kaggricuture_bot/metrics.py (canonical, repaired).

Routes evaluation calls to the corrected package implementation.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot.metrics import (
    outcome_score,
    wilson_lower_bound,
    extract_match_metrics,
    aggregate_metrics,
    family_macro_average,
)
