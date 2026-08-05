"""Phase 3R.2: Fail-loud champion packaging and parity tests.

Asserts:
- KAGGRI_DEBUG_RAISE=1 successfully forces exceptions to bubble up.
- The compiled artifact dist/main.py produces action-by-action parity with
  the source agent across full trajectories.
- The champion does not silently fallback to PASS actions during a run.
"""
from __future__ import annotations
import importlib.util
import os
import sys
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_bot.harness import FALLBACK_COUNT  # noqa: E402

AGENT_SRC = ROOT / "agents" / "champion" / "main.py"
DIST = ROOT / "dist" / "main.py"


def _load_source_agent():
    spec = importlib.util.spec_from_file_location("champion_source", str(AGENT_SRC))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_dist_agent():
    source = DIST.read_text(encoding="utf-8")
    fn = get_last_callable(source, path=str(DIST))
    return fn


def test_debug_raise_bubbles_exceptions():
    """Assert KAGGRI_DEBUG_RAISE=1 actually re-raises internal exceptions."""
    mod = _load_source_agent()
    # Mock core_agent to raise an exception.
    def faulty_core(obs, config=None):
        raise ValueError("simulated internal error")
    
    # Wrap it.
    from kaggriculture_bot.harness import make_agent
    wrapped = make_agent(faulty_core)
    
    # 1) With KAGGRI_DEBUG_RAISE=1 -> should raise
    os.environ["KAGGRI_DEBUG_RAISE"] = "1"
    with pytest.raises(ValueError, match="simulated internal error"):
        wrapped({"step": 0})
        
    # 2) With KAGGRI_DEBUG_RAISE=0 or unset -> should catch and fallback to PASS
    os.environ["KAGGRI_DEBUG_RAISE"] = "0"
    res = wrapped({"step": 0})
    assert res["farmer"] == ["PASS"]


def test_source_dist_strict_parity_on_trajectory():
    """Run a 50-step episode and assert every step return action is identical."""
    os.environ["KAGGRI_DEBUG_RAISE"] = "1"
    src_agent = _load_source_agent().agent
    dist_agent = _load_dist_agent()
    
    env = make("kaggriculture", configuration={"episodeSteps": 50, "seed": 42}, debug=True)
    # Collect observations from a pass-vs-pass run to evaluate.
    env.run(["pass", "pass"])
    
    # Reset tracking state for both.
    if hasattr(src_agent, "_core"):
        # If the loaded function is the harness wrapper, invoke its internal state reset
        src_module = sys.modules[src_agent.__module__]
        if hasattr(src_module, "_reset_episode_state"):
            src_module._reset_episode_state()
            
    # For a fair parity test, we evaluate both on the sequence of observations
    for step_state in env.steps:
        obs = step_state[0]["observation"]
        # Convert observation to dict if it's not (core environments can pass wrapper objects).
        obs_dict = dict(obs) if isinstance(obs, dict) else {k: getattr(obs, k) for k in obs.__dict__ if not k.startswith("_")}
        if "private" in obs_dict:
            obs_dict["private"] = dict(obs_dict["private"])
        
        # Call both.
        a_src = src_agent(obs_dict)
        a_dist = dist_agent(obs_dict)
        
        # Verify action-by-action parity.
        assert a_src == a_dist, f"Parity mismatch at step {obs_dict.get('step')}:\nsrc={a_src}\ndist={a_dist}"


def test_champion_does_not_silently_fallback():
    """Run the champion for 50 steps with KAGGRI_DEBUG_RAISE=1.
    If it hits any internal exception (NameError, KeyError, etc.), it will fail-loud here."""
    os.environ["KAGGRI_DEBUG_RAISE"] = "1"
    dist_agent = _load_dist_agent()
    
    env = make("kaggriculture", configuration={"episodeSteps": 50, "seed": 99}, debug=True)
    # Run champion vs pass.
    env.run([dist_agent, "pass"])
    
    # Assert it finished DONE without crashing.
    statuses = env.toJSON()["statuses"]
    assert statuses == ["DONE", "DONE"], f"Episode failed: {statuses}"


def test_packaged_artifact_forced_exception():
    """Verify that the packaged agent's fallback harness works.

    - Under KAGGRI_DEBUG_RAISE=1, a bad observation (like {"farms": 123}) raises.
    - Under KAGGRI_DEBUG_RAISE=0, it falls back gracefully to PASS actions.
    """
    dist_agent = _load_dist_agent()
    bad_obs = {"farms": 123}

    # 1) If KAGGRI_DEBUG_RAISE is "1", it must raise on invalid input
    os.environ["KAGGRI_DEBUG_RAISE"] = "1"
    with pytest.raises(Exception):
        dist_agent(bad_obs)

    # 2) If KAGGRI_DEBUG_RAISE is "0" or unset, it must fallback to a safe PASS schema
    os.environ["KAGGRI_DEBUG_RAISE"] = "0"
    res = dist_agent(bad_obs)
    assert isinstance(res, dict)
    assert res["farmer"] == ["PASS"]
    assert isinstance(res["hands"], list)
    assert isinstance(res["market"], list)

