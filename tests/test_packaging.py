"""Phase 1 packaging tests: source/dist parity + 100-seed reliability."""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parent.parent
AGENT_SRC = ROOT / "agents" / "v000_pass" / "main.py"
DIST = ROOT / "dist" / "main.py"


def _load_source_agent():
    """Load agents/v000_pass/main.py as a module (it imports from src/kaggriculture_bot)."""
    sys.path.insert(0, str(ROOT / "src"))
    spec = importlib.util.spec_from_file_location("v000_pass_main", AGENT_SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_dist_agent():
    """Load dist/main.py via get_last_callable (the official loader path)."""
    source = DIST.read_text()
    fn = get_last_callable(source, path=str(DIST))
    return fn


@pytest.fixture(scope="module")
def packaged():
    """Ensure dist/main.py is packaged before tests."""
    if not DIST.exists():
        pytest.skip("dist/main.py not built; run scripts/package_agent.py")
    return DIST


def test_dist_exists_and_loads(packaged):
    source = packaged.read_text()
    fn = get_last_callable(source, path=str(packaged))
    assert fn.__name__ == "agent"


def test_source_dist_parity_single_obs(packaged):
    """Source agent and dist agent return identical actions for the same observation."""
    src_agent = _load_source_agent().agent
    dist_agent = _load_dist_agent()
    # Build a real observation by running 1 step.
    env = make("kaggriculture", configuration={"episodeSteps": 2, "seed": 42}, debug=True)
    env.run(["pass", "pass"])
    obs = env.state[0].observation
    # observation objects may not be plain dicts; convert via the framework's serialization.
    obs_dict = obs if isinstance(obs, dict) else _obs_to_dict(obs)
    a_src = src_agent(obs_dict)
    a_dist = dist_agent(obs_dict)
    assert a_src == a_dist, f"source/dist mismatch:\n src={a_src}\n dist={a_dist}"


def _obs_to_dict(obs):
    """Best-effort conversion of an observation object to a plain dict."""
    if isinstance(obs, dict):
        return obs
    out = {}
    for k in ["player", "step", "day", "hour", "farms", "market", "town"]:
        if hasattr(obs, k):
            out[k] = getattr(obs, k)
    if hasattr(obs, "private"):
        out["private"] = obs.private
    return out


def test_100_seeds_pass_vs_pass_zero_errors(packaged):
    """§8.4: 100 different seeds, pass-vs-pass, all DONE, zero exceptions/timeouts/invalid."""
    failures = []
    for seed in range(1, 101):
        try:
            env = make("kaggriculture", configuration={"episodeSteps": 30, "seed": seed}, debug=True)
            env.run([str(packaged), "pass"])
            statuses = env.toJSON()["statuses"]
            if statuses != ["DONE", "DONE"]:
                failures.append((seed, f"statuses={statuses}"))
        except Exception as e:
            failures.append((seed, f"exception: {e}"))
    if failures:
        pytest.fail(f"{len(failures)}/100 seeds failed: {failures[:5]}")


def test_hands_count_always_matches(packaged):
    """Hands action count must match observed hand count at every step."""
    # Run an episode where opponent hires hands, so our agent sees varying hand counts.
    def opponent(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
        if step == 1:
            return {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = make("kaggriculture", configuration={"episodeSteps": 30, "seed": 1}, debug=True)
    env.run([str(packaged), opponent])
    # If we got here without error, hands counts matched throughout (env would error otherwise).
    assert env.toJSON()["statuses"] == ["DONE", "DONE"]
