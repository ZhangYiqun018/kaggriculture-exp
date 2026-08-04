"""Wheat-only agent: buy wheat, plant, water, harvest, sell."""
from __future__ import annotations

WHEAT_FIRST = 2
WHEAT_MAX = 4


def agent(obs, config=None):
    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    private = obs.get("private", {}) or {}
    fx, fy = farm["farmer"]
    tile = farm["tiles"][fy][fx]
    day = obs.get("day", 0)
    seeds = private.get("seeds", {})
    shed = private.get("shed", {})
    money = farm.get("money", 0)
    
    market = []
    if shed.get("WHEAT", 0) > 0:
        market.append(["SELL", "WHEAT", shed["WHEAT"]])
    if seeds.get("WHEAT", 0) == 0 and money >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])
    
    farmer = ["PASS"]
    if tile is None and seeds.get("WHEAT", 0) > 0:
        farmer = ["PLANT", "WHEAT"]
    elif isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile["crop"] == "WHEAT":
        age = day - tile["planted_day"]
        if age >= WHEAT_MAX:
            farmer = ["HARVEST"]
        elif not tile["watered_today"]:
            farmer = ["WATER"]
    return {"farmer": farmer, "hands": [], "market": market}
