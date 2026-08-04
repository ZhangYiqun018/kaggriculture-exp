#!/usr/bin/env python3
"""Run a single match between a candidate and an opponent, both seats.

Fresh module state per episode (reloads agent files each match to avoid
global state pollution / self-play shared mutables).

Usage:
    python -m eval.run_match --candidate dist/main.py --opponent opponents/baselines/wheat_only.py --seed 11
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
from kaggle_environments.agent import get_last_callable  # noqa: E402

from eval.metrics import extract_match_metrics  # noqa: E402


def load_agent(path_or_name: str):
    """Load an agent from a file path, or return a built-in name string."""
    if path_or_name in ("pass", "random", "starter"):
        return path_or_name
    p = Path(path_or_name)
    if not p.is_absolute():
        p = ROOT / path_or_name
    if not p.exists():
        # Maybe it's a name we should treat as built-in.
        return path_or_name
    return str(p)


def run_match(candidate: str, opponent: str, seed: int, episode_steps: int = 720) -> list[dict]:
    """Run candidate vs opponent on both seats. Returns [seat0_metrics, seat1_metrics]."""
    results = []
    cand = load_agent(candidate)
    opp = load_agent(opponent)
    
    for seat in (0, 1):
        agents = [cand, opp] if seat == 0 else [opp, cand]
        env = make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=True)
        env.run(agents)
        m = extract_match_metrics(env, candidate_idx=seat)
        m["seat"] = seat
        m["seed"] = seed
        m["candidate"] = candidate
        m["opponent"] = opponent
        results.append(m)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="dist/main.py")
    ap.add_argument("--opponent", default="pass")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    
    results = run_match(args.candidate, args.opponent, args.seed, args.steps)
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        for r in results:
            print(f"seat={r['seat']} seed={r['seed']} outcome={r['outcome']} "
                  f"cand=${r['candidate_final_money']:.0f} opp=${r['opponent_final_money']:.0f} "
                  f"status={r['status']}")
        avg = (results[0]["outcome"] + results[1]["outcome"]) / 2
        print(f"avg outcome: {avg:.2f}")


if __name__ == "__main__":
    main()
