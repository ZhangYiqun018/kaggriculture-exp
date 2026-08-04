"""v000_pass: submission-safe skeleton agent.

Always returns PASS for farmer and hands, empty market.
Hands count is matched to observation via the safety layer.
"""
from __future__ import annotations

import sys
import os

# Allow importing the safety layer when run from source (dev mode).
_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kaggriculture_bot.safety import safe_action  # noqa: E402

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
