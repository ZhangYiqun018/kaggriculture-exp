#!/usr/bin/env python3
"""Run current champion against the public opponents frontier (Phase 3.6).

Opponents:
- moon (replay_tape_lineage)
- soil (replay_tape_lineage)
- roman_anchor (replay_tape_lineage)
- kaito_v17 (learned_market_ranker)
- pilkwang (economic_control)

Collects detailed diagnostic logs: daily cash, crop counts, market prices,
HIRE counts, and terminal inventory.

Outputs: reports/public_frontier_v020.{json,csv,md}
"""
from __future__ import annotations
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
from kaggriculture_bot.state import parse_state  # noqa: E402
from kaggriculture_bot.metrics import extract_match_metrics, aggregate_metrics  # noqa: E402

SEED_SETS_PATH = ROOT / "eval" / "seed_sets.json"
CHAMPION_PATH = str(ROOT / "dist" / "main.py")

PUBLIC_OPPONENTS = {
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
}


def load_seeds() -> list[int]:
    return json.loads(SEED_SETS_PATH.read_text())["screen"]


def run_benchmark():
    seeds = load_seeds()
    results = {}
    all_flat_matches = []
    
    # We also collect timeline aggregates (daily cash, crop counts, prices, hires)
    # to meet the "Include daily cash, crop counts, market prices, HIRE counts" requirement.
    timeline_stats = defaultdict(lambda: defaultdict(list))
    
    print(f"Running Public Frontier Benchmark (8 seeds x 2 seats = 16 matches per opponent) against Champion...")
    
    for family, opp_list in PUBLIC_OPPONENTS.items():
        results[family] = {}
        for opp_name, opp_path in opp_list:
            matches = []
            print(f"  vs {opp_name}...")
            for seed in seeds:
                for seat in (0, 1):
                    # Always run under debug-raise to fail-loud on any internal errors
                    os.environ["KAGGRI_DEBUG_RAISE"] = "1"
                    
                    agents = [CHAMPION_PATH, opp_path] if seat == 0 else [opp_path, CHAMPION_PATH]
                    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
                    env.run(agents)
                    
                    # Extract standard corrected metrics
                    m = extract_match_metrics(env, candidate_idx=seat)
                    m["seed"] = seed
                    m["seat"] = seat
                    m["opponent"] = opp_name
                    m["family"] = family
                    
                    # Terminal inventory & step diagnostics
                    final_state = parse_state(env.state[0].observation)
                    m["terminal_shed"] = dict(final_state.private.shed)
                    # total item count carried by units
                    m["terminal_unit_inventory"] = [dict(i) for i in final_state.private.inventories]
                    
                    # Step-by-step telemetry extraction: pull at the end of each day (steps where step % 24 == 23)
                    daily_telemetry = []
                    for step_idx, step_state in enumerate(env.steps):
                        obs = step_state[seat]["observation"]
                        step = obs.get("step", 0)
                        if step % 24 == 23:  # End of day
                            gs = parse_state(obs)
                            farm = gs.self_farm
                            
                            # Count active crop plants on tiles
                            crop_counts = defaultdict(int)
                            for row in farm.tiles:
                                for tile in row:
                                    if tile.kind == "PLANT" and tile.crop:
                                        crop_counts[tile.crop] += 1
                                        
                            day = step // 24
                            daily_telemetry.append({
                                "day": day,
                                "cash": farm.money,
                                "crop_counts": dict(crop_counts),
                                "prices": dict(gs.market.prices),
                                "hand_count": farm.hand_count,
                                "hires_today": farm.hires_today,
                            })
                            
                    m["daily_telemetry"] = daily_telemetry
                    matches.append(m)
                    all_flat_matches.append(m)
                    
            results[family][opp_name] = {
                "summary": aggregate_metrics(matches),
                "matches": matches,
            }
            
    return results, all_flat_matches


def write_reports(results, flat_matches):
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. JSON report
    jp = reports_dir / "public_frontier_v041.json"
    jp.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    
    # 2. CSV match report
    cp = reports_dir / "public_frontier_v041.csv"
    with open(cp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "seed", "seat", "opponent", "family", "outcome", 
            "candidate_final_money", "opponent_final_money", "money_margin",
            "p99_latency", "weeds_at_end"
        ])
        w.writeheader()
        for m in flat_matches:
            w.writerow({
                "seed": m["seed"],
                "seat": m["seat"],
                "opponent": m["opponent"],
                "family": m["family"],
                "outcome": m["outcome"],
                "candidate_final_money": m["candidate_final_money"],
                "opponent_final_money": m["opponent_final_money"],
                "money_margin": m["money_margin"],
                "p99_latency": m["p99_latency"],
                "weeds_at_end": m["weeds_at_end"]
            })
            
    # 3. Markdown report
    md = [
        "# Phase 3.6: Public Opponents Frontier Benchmark Report (v041)",
        f"**Candidate:** `{CHAMPION_PATH}` (v041_market_control with market-aware allocation, NPV harvesting, chunked selling, and liquidation)",
        f"**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent against full registered public roster.",
        "\n## 1. Roster Summary & Macro Ratings\n",
        "| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    
    macro_scores = {}
    for family, opp_dict in results.items():
        fam_scores = []
        for opp_name, r in opp_dict.items():
            s = r["summary"]
            md.append(
                f"| {family} | `{opp_name}` | {s['n']} | {s['wins']} | {s['losses']} | {s['ties']} | "
                f"{s['avg_outcome']:.3f} | ${s['avg_candidate_money']:.0f} | ${s['avg_opponent_money']:.0f} | "
                f"${s['avg_money_margin']:+.0f} | {s['wilson_lower_95']:.3f} |"
            )
            fam_scores.append(s["avg_outcome"])
        macro_scores[family] = sum(fam_scores) / len(fam_scores) if fam_scores else 0.0
        
    md.append("\n## 2. Opponent Family Macro-Averages\n")
    md.append("| Opponent Family | Macro Average Outcome |")
    md.append("|---|---|")
    for fam, score in macro_scores.items():
        md.append(f"| {fam} | {score:.3f} |")
        
    # Add a global family macro league rating
    league_macro = sum(macro_scores.values()) / len(macro_scores) if macro_scores else 0.0
    md.append(f"\n**Global Public-Field Macro League Score:** `{league_macro:.3f}`")
    
    # 4. Step/Daily diagnostics of a representative match
    md.append("\n## 3. Representative Match Telemetry (vs Kaito v17, Seed 101, Seat 0)\n")
    md.append("Demonstrates daily cash, crop counts, market prices, and hire counts at the end of each day (Turns 23, 47, ...).")
    md.append("\n| Day | Cash ($) | Hired Hands | Active Crops | Market Prices (WHEAT/CARROT/MELON) |")
    md.append("|---|---|---|---|---|")
    
    # Find that match
    sample_m = None
    for m in flat_matches:
        if m["opponent"] == "kaito_v17" and m["seed"] == 101 and m["seat"] == 0:
            sample_m = m
            break
    if sample_m:
        for t in sample_m["daily_telemetry"]:
            day = t["day"]
            # format crops: e.g. WHEAT:3, CARROT:2
            crops_str = ", ".join(f"{k}:{v}" for k, v in t["crop_counts"].items()) or "None"
            p = t["prices"]
            prices_str = f"${p.get('WHEAT', 0)} / ${p.get('CARROT', 0)} / ${p.get('MELON', 0)}"
            md.append(f"| {day} | ${t['cash']:.1f} | {t['hand_count']} | {crops_str} | {prices_str} |")
            
        md.append("\n### Terminal State Inventory (Seed 101, Seat 0)")
        md.append(f"- **Terminal Shed Inventory:** `{sample_m['terminal_shed']}`")
        md.append(f"- **Terminal Carry Inventory:** `{sample_m['terminal_unit_inventory']}`")
        
    (reports_dir / "public_frontier_v041.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Benchmark reports successfully written to: reports/public_frontier_v041.{{json,csv,md}}")


def main():
    results, flat_matches = run_benchmark()
    write_reports(results, flat_matches)


if __name__ == "__main__":
    main()
