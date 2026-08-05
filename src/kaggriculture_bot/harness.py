"""Fail-loud agent harness.

Policy modules expose `core_agent(obs, config)` with NO catch-all. The
production `agent(obs, config)` wraps it and only merges to the safe fallback
when KAGGRI_DEBUG_RAISE=1 is NOT set.

Tests and the local league set KAGGRI_DEBUG_RAISE=1 so any internal exception
(ex: missing inlined module, NameError from a stripped import, bad index) is a
loud failure, not a silent PASS. `harness.py` also counts fallback events for
telemetry — the engine-visible counts of `last_callable`-suppressed failures.
"""
from __future__ import annotations
import os
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
