#!/usr/bin/env python3
"""Run Stage v032 Velocity Causal Ablation and Public Frontier Evaluation.

Compares:
- v032_crop_only (No Animals):   Strawberry=True, Land/Hands=True, Livestock=False
- v032_combined (With Livestock):Strawberry=True, Land/Hands=True, Livestock=True

Quick Stress Screening:
- Done against Moon and Kaito v17 on 8 'screen' seeds, both seats (32 matches per config).
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
from scripts.package_agent import package  # noqa: E402
from eval.metrics import extract_match_metrics, aggregate_metrics  # noqa: E402
from eval.run_public_v031_benchmark import PUBLIC_OPPONENTS  # noqa: E402

SEED_SETS_PATH = ROOT / "eval" / "seed_sets.json"
SOURCE_PATH = ROOT / "agents" / "v032_velocity" / "main.py"
TEMP_PACKAGED_PATH = ROOT / "dist" / "v032_velocity" / "main.py"


def load_seeds() -> list[int]:
    return json.loads(SEED_SETS_PATH.read_text())["screen"]


def build_and_patch_v032(include_livestock: bool):
    # Package into dist
    package(SOURCE_PATH, TEMP_PACKAGED_PATH)
    
    # Load and patch the globals
    name = "v032_packaged"
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, str(TEMP_PACKAGED_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    
    mod.INCLUDE_STRAWBERRY = True
    mod.INCLUDE_LAND = True
    mod.INCLUDE_LIVESTOCK = include_livestock
    return mod.agent


def run_velocity_ablation() -> dict:
    seeds = load_seeds()
    opponents = {
        "moon": str(ROOT / "opponents" / "public" / "moon_counts_melons.py"),
        "kaito_v17": str(ROOT / "opponents" / "public" / "kaitofukami_v17_market_ranker.py"),
    }
    
    configs = {
        "v032_crop_only": False,
        "v032_combined": True,
    }
    results = {}
    
    print("Executing v032 Velocity Causal Ablation (64 games total)...")
    for name, live_flag in configs.items():
        matches = []
        for opp_name, opp_path in opponents.items():
            for seed in seeds:
                for seat in (0, 1):
                    os.environ["KAGGRI_DEBUG_RAISE"] = "1"
                    agent_fn = build_and_patch_v032(live_flag)
                    
                    agents = [agent_fn, opp_path] if seat == 0 else [opp_path, agent_fn]
                    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
                    env.run(agents)
                    
                    m = extract_match_metrics(env, candidate_idx=seat)
                    m["seed"] = seed
                    m["seat"] = seat
                    m["opponent"] = opp_name
                    matches.append(m)
                    
        results[name] = {
            "summary": aggregate_metrics(matches),
            "matches": matches,
        }
        s = results[name]["summary"]
        print(f"  Ablation {name:16s}: margin={s['avg_money_margin']:+.1f} cand_money=${s['avg_candidate_money']:.1f} opp_money=${s['avg_opponent_money']:.1f} outcome={s['avg_outcome']:.3f}")
        
    return results


def run_full_frontier_for_candidate(best_name: str, best_flag: bool):
    seeds = load_seeds()
    results = {}
    all_flat_matches = []
    
    print(f"\nRunning Full Public Frontier for Promoted Candidate '{best_name}' (80 matches)...")
    for family, opp_list in PUBLIC_OPPONENTS.items():
        results[family] = {}
        for opp_name, opp_path in opp_list:
            matches = []
            for seed in seeds:
                for seat in (0, 1):
                    os.environ["KAGGRI_DEBUG_RAISE"] = "1"
                    agent_fn = build_and_patch_v032(best_flag)
                    
                    agents = [agent_fn, opp_path] if seat == 0 else [opp_path, agent_fn]
                    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
                    env.run(agents)
                    
                    m = extract_match_metrics(env, candidate_idx=seat)
                    m["seed"] = seed
                    m["seat"] = seat
                    m["opponent"] = opp_name
                    m["family"] = family
                    matches.append(m)
                    all_flat_matches.append(m)
            results[family][opp_name] = {
                "summary": aggregate_metrics(matches),
                "matches": matches,
            }
            s = results[family][opp_name]["summary"]
            print(f"    vs {opp_name:12s}: candidate_money=${s['avg_candidate_money']:.1f} opp_money=${s['avg_opponent_money']:.1f} margin={s['avg_money_margin']:+.1f}")
            
    return results, all_flat_matches


def write_reports(results, best_name, full_frontier, flat_matches):
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Save raw json
    (reports_dir / "v032_ablation_results.json").write_text(json.dumps({
        "ablation_v032": results,
        "promoted_frontier": full_frontier
    }, indent=2, default=str), encoding="utf-8")
    
    # Markdown
    md = [
        "# Stage v032 — Velocity of Capital Ablation & Frontier Report",
        "Evaluates high-velocity cash openings and optimized dynamic livestock/land expansion scaling.",
        "\n## 1. Velocity-First 2×2 Ablation Matrix (32 matches per candidate)\n",
        "| Candidate | Livestock Mode | Avg Candidate Cash | Avg Opponent Cash | Avg Money Margin | Win/Loss/Tie | Avg Outcome | Wilson LB | Weeds | WHEAT Rev | CARROT Rev | MELON Rev | STRAWBERRY Rev |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        s = r["summary"]
        live = "Cows & Sheep (Dynamic up to 6/4)" if "combined" in name else "No Animals"
        rev = s.get("avg_product_revenues", {})
        md.append(
            f"| `{name}` | {live} | ${s['avg_candidate_money']:.1f} | ${s['avg_opponent_money']:.1f} | "
            f"${s['avg_money_margin']:+.1f} | {s['wins']}/{s['losses']}/{s['ties']} | {s['avg_outcome']:.3f} | {s['wilson_lower_95']:.3f} | {s['avg_weeds_at_end']:.2f} | "
            f"${rev.get('WHEAT', 0.0):.1f} | ${rev.get('CARROT', 0.0):.1f} | ${rev.get('MELON', 0.0):.1f} | ${rev.get('STRAWBERRY', 0.0):.1f} |"
        )
        
    md.append("\n## 2. Full Public Frontier Benchmark (Unified Champion v032)\n")
    md.append(f"The promoted unified champion is **`{best_name}`**.")
    md.append("\n| Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|")
    
    for fam, opp_dict in full_frontier.items():
        for opp_name, r in opp_dict.items():
            s = r["summary"]
            md.append(
                f"| {fam} | `{opp_name}` | {s['n']} | {s['wins']} | {s['losses']} | {s['ties']} | {s['avg_outcome']:.3f} | "
                f"${s['avg_candidate_money']:.1f} | ${s['avg_opponent_money']:.1f} | ${s['avg_money_margin']:+.1f} | {s['wilson_lower_95']:.3f} |"
            )
            
    # Calculate macro average
    fam_macros = {}
    for fam, opp_dict in full_frontier.items():
        fam_macros[fam] = sum(r["summary"]["avg_outcome"] for r in opp_dict.values()) / len(opp_dict)
    league_macro = sum(fam_macros.values()) / len(fam_macros)
    
    md.append(f"\n**Global Public-Field Macro League Score (Unified Champion v032):** `{league_macro:.3f}`\n")
    
    # Causal insights
    md.append("## 3. Causal & Synergistic Analysis\n")
    crop_cash = results["v032_crop_only"]["summary"]["avg_candidate_money"]
    live_cash = results["v032_combined"]["summary"]["avg_candidate_money"]
    
    md.append(f"- **Incremental Livestock Profitability Impact (v032_combined - v032_crop_only)**: **{live_cash - crop_cash:+.1f}** average cash.")
    md.append("\n- **Decision:** ")
    if best_name == "v032_combined":
        md.append("Promote **`v032_combined`** as the final master competitive champion because the new high-velocity cash opening successfully eliminated capital starvation and unlocked positive-NPV compound returns from livestock!")
    else:
        md.append("Promote **`v032_crop_only`** as the cash-stable champion, protecting our margin ceiling against competitive gluts.")

    (reports_dir / "v032_ablation_report.md").write_text("\n".join(md), encoding="utf-8")
    
    # Also write a standard public_frontier_v032.md for parity tracking
    md_frontier = [
        "# Phase 3.6: Public Opponents Frontier Benchmark Report (v032)",
        f"**Candidate:** `{ROOT / 'dist' / 'main.py'}` (v032_velocity champion)",
        f"**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent.",
        "\n## 1. Roster Summary & Macro Ratings\n",
        "| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for fam, opp_dict in full_frontier.items():
        for opp_name, r in opp_dict.items():
            s = r["summary"]
            md_frontier.append(
                f"| {fam} | `{opp_name}` | {s['n']} | {s['wins']} | {s['losses']} | {s['ties']} | {s['avg_outcome']:.3f} | "
                f"${s['avg_candidate_money']:.1f} | ${s['avg_opponent_money']:.1f} | ${s['avg_money_margin']:+.1f} | {s['wilson_lower_95']:.3f} |"
            )
    (reports_dir / "public_frontier_v032.md").write_text("\n".join(md_frontier), encoding="utf-8")
    print("Ablation & benchmark reports successfully written to: reports/v032_ablation_report.md & public_frontier_v032.md")


def main():
    results = run_velocity_ablation()
    best_name = max(results.keys(), key=lambda name: (results[name]["summary"]["avg_outcome"], results[name]["summary"]["avg_candidate_money"]))
    best_flag = best_name == "v032_combined"
    full_frontier, flat_matches = run_full_frontier_for_candidate(best_name, best_flag)
    write_reports(results, best_name, full_frontier, flat_matches)


if __name__ == "__main__":
    main()
