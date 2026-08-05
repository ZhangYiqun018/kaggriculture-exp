"""Phase 1 packaging tests: source/dist parity + 100-seed reliability (dynamic manifest-driven parity)."""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "main.py"
MANIFEST = ROOT / "dist" / "manifest.json"


def _get_agent_src():
    if MANIFEST.exists():
        try:
            d = json.loads(MANIFEST.read_text(encoding="utf-8"))
            p = ROOT / d.get("source_path", "agents/champion/main.py")
            if p.exists():
                return p
        except Exception:
            pass
    return ROOT / "agents" / "champion" / "main.py"


def _load_source_agent():
    src = _get_agent_src()
    sys.path.insert(0, str(ROOT / "src"))
    spec = importlib.util.spec_from_file_location("source_agent", str(src))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_dist_agent():
    source = DIST.read_text()
    fn = get_last_callable(source, path=str(DIST))
    return fn


@pytest.fixture(scope="module")
def packaged():
    if not DIST.exists():
        pytest.skip("dist/main.py not built; run scripts/package_agent.py")
    return DIST


def test_dist_exists_and_loads(packaged):
    source = packaged.read_text()
    fn = get_last_callable(source, path=str(packaged))
    assert fn.__name__ == "agent"


def test_source_dist_parity_single_obs(packaged):
    src_agent = _load_source_agent().agent
    dist_agent = _load_dist_agent()
    env = make("kaggriculture", configuration={"episodeSteps": 2, "seed": 42}, debug=True)
    env.run(["pass", "pass"])
    obs = env.state[0].observation
    obs_dict = obs if isinstance(obs, dict) else _obs_to_dict(obs)
    
    # reset module level states if present (clean slate)
    src_mod = sys.modules[src_agent.__module__]
    if hasattr(src_mod, "_reset_episode_state"):
        src_mod._reset_episode_state()
        
    a_src = src_agent(obs_dict)
    a_dist = dist_agent(obs_dict)
    assert a_src == a_dist, f"source/dist mismatch:\n src={a_src}\n dist={a_dist}"


def _obs_to_dict(obs):
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
    failures = []
    for seed in range(1, 101):
        try:
            env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": seed}, debug=True)
            env.run([str(packaged), "pass"])
            statuses = env.toJSON()["statuses"]
            if statuses != ["DONE", "DONE"]:
                failures.append((seed, f"statuses={statuses}"))
        except Exception as e:
            failures.append((seed, f"exception: {e}"))
    if failures:
        pytest.fail(f"{len(failures)}/100 seeds failed: {failures[:5]}")


def test_hands_count_always_matches(packaged):
    def opponent(obs, config=None):
        step = obs.get("step", 0)
        if step == 0:
            return {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
        if step == 1:
            return {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = make("kaggriculture", configuration={"episodeSteps": 15, "seed": 1}, debug=True)
    env.run([str(packaged), opponent])
    assert env.toJSON()["statuses"] == ["DONE", "DONE"]
