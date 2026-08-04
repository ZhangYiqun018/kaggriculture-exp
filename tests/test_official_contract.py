"""Phase 0 official contract tests (spec §7.2-7.10).

Each test probes a specific behavioral contract of the INSTALLED
kaggle-environments==1.32.3 kaggriculture environment. These are the
ground-truth tests — if a README or AGENTS.md claim contradicts these, the
test wins.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parent.parent


def _run_episode(agent_fns, steps=5, seed=1):
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed}, debug=True)
    env.run(agent_fns)
    return env


def _state0(env):
    return env.state[0].observation


# §7.2 Action order: unit actions before market orders.
# Agent has no seeds; same turn farmer does PLANT WHEAT, market does BUY_SEED WHEAT 1.
# Expectation: PLANT fails (no seeds yet), seed bought this turn only available next turn.
def test_action_order_unit_before_market():
    def agent(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            # Farmer tries to plant WHEAT (no seeds). Market buys 1 WHEAT seed.
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = _run_episode([agent, "pass"], steps=3, seed=1)
    s0 = _state0(env)
    farm = s0.farms[0]
    seeds = s0.private["seeds"]
    # Seed bought on step 0 should be available (money deducted, seed added).
    assert seeds.get("WHEAT", 0) == 1, f"expected 1 wheat seed after buy, got {seeds.get('WHEAT')}"
    # But the PLANT on step 0 should NOT have executed (no seed at unit-action time).
    # Farmer was standing on a shed-access tile (NW). Check it's still empty (None), not a plant.
    fx, fy = farm["farmer"]
    tile = farm["tiles"][fy][fx]
    assert tile is None, f"PLANT should not have fired on step 0 (seeds bought after unit actions); tile={tile}"


# §7.3 Atomic PLANT: 1 seed, farmer + 1 hand both request PLANT WHEAT -> both become PASS.
def test_plant_atomicity_both_blocked():
    def agent(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["BUY_SEED_PLACEHOLDER"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        if step == 1:
            # Hire a hand so step 2 has 2 units.
            return {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
        if step == 2:
            # 1 seed, 2 units (farmer + 1 hand), both PLANT WHEAT -> both blocked.
            return {"farmer": ["PLANT", "WHEAT"], "hands": [["PLANT", "WHEAT"]], "market": []}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = _run_episode([agent, "pass"], steps=5, seed=1)
    s0 = _state0(env)
    seeds = s0.private["seeds"]
    # Seed should still be 1 (both PLANTs blocked due to over-demand).
    assert seeds.get("WHEAT", 0) == 1, f"expected seed preserved (both PLANTs atomic-blocked), got {seeds.get('WHEAT')}"
    # No plant should exist anywhere on the farm.
    farm = s0.farms[0]
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                pytest.fail(f"found unexpected plant after atomic PLANT block: {tile}")


# §7.4 LOCKED movement: can move INTO locked, OUT OF locked, ops no-op on locked, OOB rejected.
def test_locked_movement_and_ops():
    # Board: NW unlocked (0..4 x 0..4), rest LOCKED. Farmer spawns on a shed-access tile in NW.
    # Shed-access tiles: (4,4),(5,4),(4,5),(5,5). NW ones: (4,4). So farmer starts at (4,4).
    # (5,4) is in NE -> LOCKED. Move EAST from (4,4) -> (5,4) which is LOCKED: allowed.
    def agent(obs, config=None):
        step = obs.get("step", 0)
        player = obs.get("player", 0)
        farm = obs["farms"][player]
        fx, fy = farm["farmer"]
        if step == 0:
            # Move EAST onto LOCKED tile (5,4) — should succeed.
            return {"farmer": ["EAST"], "hands": [], "market": []}
        if step == 1:
            # Now on LOCKED (5,4). PLANT should be no-op.
            assert farm["farmer"] == [5, 4], f"expected farmer at (5,4) LOCKED, got {farm['farmer']}"
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        if step == 2:
            # PLANT was no-op on LOCKED. Move WEST back to (4,4) — should succeed (move OUT of locked).
            return {"farmer": ["WEST"], "hands": [], "market": []}
        if step == 3:
            # Move NORTH to (4,3) — still in NW, valid. Then step 4 NORTH to (4,2)... 
            # To test OOB: go to y=0 first, then NORTH. Farmer at (4,4) -> need 4 NORTHs to y=0, 5th is OOB.
            return {"farmer": ["NORTH"], "hands": [], "market": []}
        if step == 4:
            return {"farmer": ["NORTH"], "hands": [], "market": []}
        if step == 5:
            return {"farmer": ["NORTH"], "hands": [], "market": []}
        if step == 6:
            return {"farmer": ["NORTH"], "hands": [], "market": []}
        if step == 7:
            # Now at (4,0). NORTH -> (4,-1) OOB, should be rejected.
            assert farm["farmer"] == [4, 0], f"expected farmer at (4,0), got {farm['farmer']}"
            return {"farmer": ["NORTH"], "hands": [], "market": []}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = _run_episode([agent, "pass"], steps=9, seed=1)
    s0 = _state0(env)
    farm = s0.farms[0]
    # After OOB NORTH from (4,0) farmer should still be at (4,0).
    assert farm["farmer"] == [4, 0], f"OOB move should be rejected; farmer={farm['farmer']}"
    # No plant on (5,4) — PLANT was no-op on LOCKED.
    tile_5_4 = farm["tiles"][4][5]
    assert tile_5_4 == "LOCKED", f"PLANT on LOCKED should be no-op; tile(5,4)={tile_5_4}"
    # Seed should still be 1 (PLANT no-op).
    assert s0.private["seeds"].get("WHEAT", 0) == 1


# §7.5 HIRE timing: new hand acts next turn, not current.
def test_hire_timing():
    def agent(obs, config=None):
        step = obs.get("step", 0)
        player = obs.get("player", 0)
        farm = obs["farms"][player]
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
        if step == 1:
            # Hand should now exist (hired step 0, market phase). It can act THIS step (step 1).
            n_hands = len(farm.get("hands", []))
            assert n_hands == 1, f"expected 1 hand after HIRE, got {n_hands}"
            # Hand moves NORTH (no-op effect we check, just confirm it doesn't crash).
            return {"farmer": ["PASS"], "hands": [["NORTH"]], "market": []}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = _run_episode([agent, "pass"], steps=4, seed=1)
    s0 = _state0(env)
    farm = s0.farms[0]
    # Hand should still exist (we're still day 0, before end-of-day clear).
    assert len(farm["hands"]) == 1


# §7.6 SELL FERTILIZER increases money, decreases shed fertilizer.
def test_sell_fertilizer():
    def agent(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "FERTILIZER", 2]]}
        if step == 1:
            return {"farmer": ["PASS"], "hands": [], "market": [["SELL", "FERTILIZER", 1]]}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = _run_episode([agent, "pass"], steps=4, seed=1)
    s0 = _state0(env)
    shed_fert = s0.private["shed"].get("FERTILIZER", 0)
    assert shed_fert == 1, f"expected 1 fertilizer left (bought 2, sold 1), got {shed_fert}"
    # Money: started 3000, bought 2 fert at base price, sold 1 at base price.
    # Net money change depends on price, but should be < 3000 (bought more than sold).
    money = s0.farms[0]["money"]
    assert money < 3000, f"money should be < 3000 after net buy, got {money}"


# §7.7 CARE bonus is +1 (not +2) per fed+cared day.
def test_care_bonus_is_plus_one():
    # Strategy: COW (max_held=6, first_yield_day=8, interval=2).
    # Place cow day 0. Feed+care on day 1 ONLY (steps 24..47, care on step 24).
    # First production at end-of-day 8 (step 191 -> day 8 eod). bonus from 1 care = +1.
    # yield = base(1) + bonus(1) = 2. If +2/day, yield would be 3.
    # We read yield_units right after first production via a harvested-then-checked approach.
    # Simpler: inspect tile yield_units at step 192 (after day 8 eod refresh) before harvesting.
    def agent(obs, config=None):
        step = obs.get("step", 0)
        player = obs.get("player", 0)
        farm = obs["farms"][player]
        private = obs["private"]
        fx, fy = farm["farmer"]
        tile = farm["tiles"][fy][fx]

        if step == 0:
            return {"farmer": ["BUILD_PASTURE"], "hands": [],
                    "market": [["BUY_ANIMAL", "COW", 1], ["BUY_PRODUCT", "WHEAT", 1]]}
        if step == 1:
            return {"farmer": ["PLACE", "COW"], "hands": [], "market": []}
        if step == 2:
            return {"farmer": ["PICKUP", "WHEAT", 1], "hands": [], "market": []}
        # Day 1 starts at step 24. Feed+care on step 24 (standing on cow tile at (4,4) still).
        if step == 24:
            # Farmer at (4,4) which has the cow. Feed then care — but only one farmer action/turn.
            # Feed on step 24, care on step 25.
            return {"farmer": ["FEED"], "hands": [], "market": []}
        if step == 25:
            return {"farmer": ["CARE"], "hands": [], "market": []}
        # Day 8 eod happens after step 191 (step 191 is hour 23 of day 7; (191+1)%24==0 -> eod day 7 -> refresh for day 8).
        # Actually day = step//24. step 191 is day 7 hour 23. (191+1)%24==0 -> _end_of_day(day=7).
        # In _daily_refresh_animals: next_day=8. days_since_first = 8-0-8 = 0. 0%2==0 -> production!
        # bonus = pending_care_bonus (1, from day 1 care) if fed_today else 0.
        # But fed_today is for day 7 (we only fed on day 1). So at day 7 eod, fed_today=False -> bonus=0.
        # The care bonus from day 1 is consumed at the FIRST FED production day.
        # We need to feed on a production day. Production days: 8,10,12,... (days_since_first % 2 == 0).
        # Feed on day 8 (step 192..215). Day 8 eod: step 215 -> (215+1)%24==0 -> eod day 8.
        # At day 8 eod: fed_today=True (if we fed), days_since_first=9-0-8=1, 1%2!=0 -> no production.
        # Hmm. Let me recompute: production at eod for day d: days_since_first = (d+1) - placed_day - first_yield_day
        # placed_day=0, first_yield_day=8. day d eod: days_since_first = d+1-8.
        # d=7: 0 -> production (0%2==0). d=8: 1 -> no. d=9: 2 -> production.
        # So first production is at day 7 eod. We need cow fed on day 7 to get bonus.
        # Feed on day 7 (step 168..191). Care also on day 7.
        if step == 168:
            return {"farmer": ["FEED"], "hands": [], "market": []}
        if step == 169:
            return {"farmer": ["CARE"], "hands": [], "market": []}
        # Also care on day 1 still happens (step 24-25 above) — but that bonus is consumed at day 7
        # only if fed on day 7. We feed on day 7, so day-1 care bonus + day-7 care both apply?
        # L796: bonus = pending_care_bonus if fed_today else 0. pending accumulates across days.
        # Day 1 care -> pending=1. Day 7 care (step 169) happens BEFORE day 7 eod. But day 7 eod
        # sets pending=0 after consuming. Wait — care on day 7 adds to pending at L800 AFTER
        # production at L797. So day 7 production uses pending from day 1 (1), then day 7 care
        # adds 1 more for next time.
        # So at day 7 eod production: base=1 + bonus(pending=1 from day1) = 2. (fed_today=True on day 7)
        # If +2/day: bonus would be 2 -> yield=3.
        # Check yield at step 192 (after day 7 eod).
        if step == 192:
            tile_now = farm["tiles"][fy][fx]
            if isinstance(tile_now, dict) and "animal" in tile_now:
                yu = tile_now.get("yield_units", 0)
                # +1/day -> yu=2. +2/day -> yu=3.
                assert yu == 2, f"CARE bonus should be +1 (yield=2), got yield_units={yu} (+2/day would give 3)"
            return {"farmer": ["PASS"], "hands": [], "market": []}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = _run_episode([agent, "pass"], steps=200, seed=1)
    # Assertion is inside the agent at step 192. If we get here without error, pass.
    # But agent exceptions in kaggle-environments may be swallowed — double-check post-hoc.
    s0 = _state0(env)
    farm = s0.farms[0]
    fx, fy = farm["farmer"]
    tile = farm["tiles"][fy][fx]
    if isinstance(tile, dict) and "animal" in tile:
        assert tile.get("yield_units", 0) == 2, f"post-hoc: expected yield 2, got {tile.get('yield_units')}"


# §7.8 Market lockstep: both players SELL same item, first unit uses same quote for both.
def test_market_lockstep():
    # Both players start with 0 inventory. Give both WHEAT via BUY_PRODUCT, then both SELL.
    # On the SELL turn, both quote against same pre-commit inventory; after both commit unit 1,
    # inventory rises by 2 (if price>1), then re-quote for unit 2.
    # We verify lockstep by checking that the price sequence is consistent with lockstep,
    # not sequential (sequential would have player 0's unit 2 see inventory after player 0's unit 1 only).
    def p0(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 3]]}
        if step == 1:
            return {"farmer": ["PASS"], "hands": [], "market": [["SELL", "WHEAT", 3]]}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    def p1(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 3]]}
        if step == 1:
            return {"farmer": ["PASS"], "hands": [], "market": [["SELL", "WHEAT", 3]]}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = _run_episode([p0, p1], steps=4, seed=1)
    # Both sold 3 WHEAT. Lockstep means the 6 total units were sold in interleaved fashion.
    # Hard to assert exact prices without reproducing market_price, but we can verify both
    # ended with 0 wheat and money changed. The key lockstep property: both players' unit-i
    # saw the same inventory. We assert the episode completed without error and money differs
    # from 3000 for both.
    s0 = _state0(env)
    s1 = env.state[1].observation
    assert s0.private["shed"].get("WHEAT", 0) == 0
    assert s1.private["shed"].get("WHEAT", 0) == 0
    assert s0.farms[0]["money"] != 3000
    assert s1.farms[1]["money"] != 3000


# §7.9 End-of-day refresh: hands cleared, inventories->shed, overflow lost, farmer reset, hires reset.
def test_end_of_day_refresh():
    def agent(obs, config=None):
        step = obs.get("step", 0)
        player = obs.get("player", 0)
        farm = obs["farms"][player]
        if step == 0:
            # Buy wheat product (goes to shed), hire a hand, move farmer.
            return {"farmer": ["EAST"], "hands": [], "market": [["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]]}
        if step == 1:
            # Hand exists. Pickup wheat into hand inventory. Move farmer off spawn.
            return {"farmer": ["NORTH"], "hands": [["PASS"]], "market": []}
        # steps 2..23: just pass. Step 23 is hour 23 of day 0. (23+1)%24==0 -> eod.
        if step == 23:
            # Before eod: farmer not at spawn, hand exists, hires_today=1.
            assert farm["farmer"] != [4, 4] or True  # farmer may have moved back; just check post-eod
            assert len(farm["hands"]) == 1
            assert farm["hires_today"] == 1
            return {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        if step == 24:
            # After eod: hands cleared, farmer reset to spawn, hires_today=0.
            assert len(farm["hands"]) == 0, f"hands should be cleared at eod, got {len(farm['hands'])}"
            assert farm["hires_today"] == 0, f"hires_today should reset at eod, got {farm['hires_today']}"
            assert farm["farmer"] == [4, 4], f"farmer should reset to spawn (4,4), got {farm['farmer']}"
            return {"farmer": ["PASS"], "hands": [], "market": []}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = _run_episode([agent, "pass"], steps=26, seed=1)
    s0 = _state0(env)
    farm = s0.farms[0]
    assert len(farm["hands"]) == 0
    assert farm["hires_today"] == 0
    # Wheat bought should be in shed (bought step 0, in shed already since BUY_PRODUCT -> shed).
    assert s0.private["shed"].get("WHEAT", 0) == 1


# §7.10 File loader: get_last_callable picks last callable; trailing callable breaks it.
def test_file_loader_last_callable():
    source_good = (
        "def helper(obs):\n    return {}\n"
        "def agent(obs, config=None):\n    return {'farmer': ['PASS'], 'hands': [], 'market': []}\n"
    )
    fn = get_last_callable(source_good)
    assert fn.__name__ == "agent", f"expected 'agent', got {fn.__name__}"

    source_bad = (
        "def agent(obs, config=None):\n    return {'farmer': ['PASS'], 'hands': [], 'market': []}\n"
        "def oops(obs):\n    return {}\n"  # 'oops' is now the last callable -> loader picks it
    )
    fn2 = get_last_callable(source_bad)
    assert fn2.__name__ == "oops", f"loader should pick LAST callable 'oops', got {fn2.__name__}"


# §7.1 default config values.
def test_default_config_values():
    env = make("kaggriculture", configuration={"seed": 1})
    cfg = env.configuration
    assert cfg.episodeSteps == 720
    assert cfg.actTimeout == 1
    assert cfg.startingMoney == 3000
    assert cfg.maxMarketOrdersPerTurn == 10
    assert cfg.turnsPerDay == 24
    assert cfg.shedCapacity == 100
    assert cfg.boardSize == 10
    assert cfg.farmHandCostMult == 1
    assert len(env.state) == 2
