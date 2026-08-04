"""Deterministic random agent (seeded, reproducible — unlike built-in 'random')."""
from __future__ import annotations
import random as _random

# Per-episode state keyed by player index to keep RNG streams independent.
_RNG = {}


def agent(obs, config=None):
    player = obs.get("player", 0)
    step = obs.get("step", 0)
    if step == 0:
        # Seed deterministically from player + a fixed base; NOT from env (env seed is hidden).
        _RNG[player] = _random.Random(12345 + player * 7919)
    rng = _RNG.get(player, _random.Random(12345 + player * 7919))
    
    farms = obs.get("farms", [])
    farm = farms[player] if farms and player < len(farms) else None
    if farm is None:
        return {"farmer": ["PASS"], "hands": [], "market": []}
    
    private = obs.get("private", {}) or {}
    seeds = private.get("seeds", {})
    money = farm.get("money", 0)
    
    farmer_ops = ["NORTH", "SOUTH", "EAST", "WEST", "WATER", "HARVEST", "PASS"]
    market = []
    affordable = [c for c in ("WHEAT", "CARROT", "MELON") if money >= ({"WHEAT": 10, "CARROT": 20, "MELON": 80}).get(c, 999)]
    if affordable and rng.random() < 0.1:
        market.append(["BUY_SEED", rng.choice(affordable), 1])
    
    available = [c for c, n in seeds.items() if n > 0]
    if available and rng.random() < 0.3:
        farmer = ["PLANT", rng.choice(available)]
    else:
        farmer = [rng.choice(farmer_ops)]
    
    hands_actions = [[rng.choice(farmer_ops)] for _ in farm.get("hands", [])]
    return {"farmer": farmer, "hands": hands_actions, "market": market}
