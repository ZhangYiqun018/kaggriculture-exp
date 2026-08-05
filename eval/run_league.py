#!/usr/bin/env python3
"""Run a full league: candidate vs all opponents, both seats, across seed set.

Produces JSON, CSV, and Markdown reports. Deterministic and reproducible.

Usage:
    python -m eval.run_league --candidate dist/main.py --seed-set smoke
    python -m eval.run_league --candidate dist/main.py --seed-set screen --output reports/league_screen
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eval.run_match import run_match  # noqa: E402
from eval.metrics import aggregate_metrics, family_macro_average  # noqa: E402

SEED_SETS_PATH = ROOT / "eval" / "seed_sets.json"

# Opponent roster by family (mirrors seed_sets.json _families).
OPPONENTS = {
    "basic_baselines": [
        ("pass", "pass"),
        ("deterministic_random", "opponents/baselines/deterministic_random.py"),
        ("wheat_only", "opponents/baselines/wheat_only.py"),
    ],
    "crop_closed_loop": [
        ("starter", "starter"),
    ],
    "replay_tape_lineage": [
        ("moon", "opponents/public/moon_counts_melons.py"),
        ("soil", "opponents/public/soil_remembers_rain.py"),
        ("roman_anchor", "opponents/public/roman_hamburger_anchor.py"),
    ],
    "learned_market_ranker": [
        ("kaito_v17", "opponents/public/kaitofukami_v17_market_ranker.py"),
    ],
    "economic_control": [
        ("pilkwang", "opponents/public/pilkwang_economic_control.py"),
    ],
    "historical_own_agents": [],
}


def load_seed_set(name: str) -> list[int]:
    data = json.loads(SEED_SETS_PATH.read_text())
    return data[name]


def run_league(candidate: str, seed_set_name: str, episode_steps: int = 720) -> dict:
    """Run candidate vs all opponents across a seed set, both seats."""
    seeds = load_seed_set(seed_set_name)
    all_matches = []
    family_results = {}
    
    for family, opp_list in OPPONENTS.items():
        if not opp_list:
            continue
        family_matches = []
        for opp_name, opp_path in opp_list:
            for seed in seeds:
                matches = run_match(candidate, opp_path, seed, episode_steps)
                for m in matches:
                    m["opponent_name"] = opp_name
                    m["family"] = family
                all_matches.extend(matches)
                family_matches.extend(matches)
        if family_matches:
            family_results[family] = aggregate_metrics(family_matches)
    
    overall = aggregate_metrics(all_matches)
    macro = family_macro_average(family_results)
    
    return {
        "candidate": candidate,
        "seed_set": seed_set_name,
        "seeds": seeds,
        "episode_steps": episode_steps,
        "overall": overall,
        "family_macro_score": macro,
        "families": family_results,
        "matches": all_matches,
    }


def write_reports(result: dict, output_prefix: Path):
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    # JSON
    (output_prefix.with_suffix(".json")).write_text(json.dumps(result, indent=2, default=str))
    # CSV (one row per match)
    csv_path = output_prefix.with_suffix(".csv")
    if result["matches"]:
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["seed", "seat", "opponent_name", "family",
                                              "outcome", "candidate_final_money",
                                              "opponent_final_money", "status"])
            w.writeheader()
            for m in result["matches"]:
                w.writerow({k: m.get(k) for k in w.fieldnames})
    # Markdown
    md = [f"# League Report: {result['candidate']} ({result['seed_set']})\n"]
    md.append(f"Seeds: {len(result['seeds'])} | Steps: {result['episode_steps']}\n")
    md.append(f"## Overall\n")
    md.append(f"- Matches: {result['overall']['n']}")
    md.append(f"- W/L/T: {result['overall']['wins']}/{result['overall']['losses']}/{result['overall']['ties']}")
    md.append(f"- Avg outcome: {result['overall']['avg_outcome']}")
    md.append(f"- Wilson LB 95%: {result['overall']['wilson_lower_95']}")
    md.append(f"- Family macro score: {result['family_macro_score']}")
    md.append(f"- Exception rate: {result['overall']['exception_rate']}\n")
    md.append(f"## By Family\n")
    md.append("| Family | N | W/L/T | Avg Outcome | Wilson LB | Macro |")
    md.append("|--------|---|------|-------------|-----------|-------|")
    for fam, r in result["families"].items():
        md.append(f"| {fam} | {r['n']} | {r['wins']}/{r['losses']}/{r['ties']} | "
                  f"{r['avg_outcome']} | {r['wilson_lower_95']} | {r['avg_outcome']} |")
    (output_prefix.with_suffix(".md")).write_text("\n".join(md))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="dist/main.py")
    ap.add_argument("--seed-set", default="smoke")
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--output", default=None, help="output prefix (default reports/league_<seedset>)")
    args = ap.parse_args()
    
    output = Path(args.output) if args.output else ROOT / "reports" / f"league_{args.seed_set}"
    result = run_league(args.candidate, args.seed_set, args.steps)
    write_reports(result, output)
    
    print(f"League: {result['overall']['n']} matches")
    print(f"  W/L/T: {result['overall']['wins']}/{result['overall']['losses']}/{result['overall']['ties']}")
    print(f"  Avg outcome: {result['overall']['avg_outcome']}")
    print(f"  Wilson LB: {result['overall']['wilson_lower_95']}")
    print(f"  Family macro: {result['family_macro_score']}")
    print(f"  Reports: {output}.{{json,csv,md}}")


if __name__ == "__main__":
    main()
