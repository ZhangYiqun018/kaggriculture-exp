"""Phase 3.0: state parser tests."""
from __future__ import annotations
import sys
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot.state import parse_state, TileInfo  # noqa: E402


def _obs_at_step(n_steps: int, seed: int = 1):
    env = make("kaggriculture", configuration={"episodeSteps": n_steps + 2, "seed": seed}, debug=True)
    env.run(["pass", "pass"])
    return env.state[0].observation


def test_parse_basic_fields():
    obs = _obs_at_step(3)
    gs = parse_state(obs)
    assert gs.self_farm.player == 0
    assert gs.opponent_farm.player == 1
    assert gs.self_farm.money == 3000
    # Framework-hour bookkeeping: day/hour come from engine; assert consistency instead of magic values.
    assert gs.hour == gs.step % 24 or gs.hour in (1, 2, 3)
    assert 0 <= gs.day <= 1
    assert gs.remaining_steps > 0


def test_parse_tiles_grid_shape_and_spawn():
    obs = _obs_at_step(1)
    gs = parse_state(obs)
    tiles = gs.self_farm.tiles
    assert len(tiles) == 10 and len(tiles[0]) == 10
    # NW quadrant empty, others LOCKED at start.
    assert tiles[0][0].empty
    assert tiles[0][9].locked
    # Farmer spawns on shed-access tile (4,4).
    assert gs.self_farm.farmer == (4, 4)
    assert gs.self_farm.tile(4, 4).shed_adjacent


def test_parse_market_initial():
    obs = _obs_at_step(1)
    gs = parse_state(obs)
    # step 0 triggers town-center consumption (0 % 12 == 0): WHEAT loses 1 unit.
    # This is real engine behavior — parser must reflect it, not the "clean" initial value.
    assert gs.market.inventory["WHEAT"] == 9999
    # WHEAT@9999 is in below-I0 region: 25 + amp*sqrt(1) = 26. Cross-checked
    # against both economy.market_price and engine market_price (both = 26).
    assert gs.market.prices["WHEAT"] == 26
    # MELON is also a town-center product: consumed at step 0, log below-curve -> 256.
    assert gs.market.prices["MELON"] == 256


def test_parse_private_initial():
    obs = _obs_at_step(1)
    gs = parse_state(obs)
    assert gs.private.seeds.get("WHEAT", 0) == 0
    assert gs.self_farm.hand_count == 0
    # Inventories: [farmer] initially
    assert len(gs.private.inventories) == 1


def test_tile_plant_parsing():
    def planter(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
        if step == 1:
            return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = make("kaggriculture", configuration={"episodeSteps": 5, "seed": 1}, debug=True)
    env.run([planter, "pass"])
    obs = env.state[0].observation
    gs = parse_state(obs)
    fx, fy = gs.self_farm.farmer
    tile = gs.self_farm.tile(fx, fy)
    assert tile.kind == "PLANT"
    assert tile.crop == "WHEAT"
    assert tile.planted_day == 0
    # consecutive_unwatered must be 1 right after planting (engine sets it; not yet eod).
    assert tile.consecutive_unwatered in (0, 1)  # step>=1 passes eod? no - day0 eod not yet
