#!/usr/bin/env python3
"""Run Stage v040 Causal Ablation and Public Frontier Evaluation (Phase 3.6).

Ablations compared:
- v031 (Baseline):              Strawberry=False, Land/Hands=False
- +strawberry:                  Strawberry=True,  Land/Hands=False
- +land/hands:                  Strawberry=False, Land/Hands=True
- +strawberry+land/hands (v040):Strawberry=True,  Land/Hands=True

Quick Stress Screening:
- Done against Moon and Kaito v17 on 8 'screen' seeds, both seats.

Selected Candidate:
- Promoted to Champion, then run on the FULL public frontier (all 5 opponents).
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
SOURCE_PATH = ROOT / "agents" / "v040_compound_crop" / "main.py"
TEMP_PACKAGED_PATH = ROOT / "dist" / "v040_compound_crop" / "main.py"


def load_seeds() -> list[int]:
    return json.loads(SEED_SETS_PATH.read_text())["screen"]


def build_and_patch_v040(include_strawberry: bool, include_land: bool):
    # Package into dist
    package(SOURCE_PATH, TEMP_PACKAGED_PATH)
    
    # Load and patch the globals
    name = "v040_packaged"
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, str(TEMP_PACKAGED_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    
    mod.INCLUDE_STRAWBERRY = include_strawberry
    mod.INCLUDE_LAND = include_land
    return mod.agent


def run_quick_stress_screening() -> dict:
    seeds = load_seeds()
    # Stress screening opponents
    opponents = {
        "moon": str(ROOT / "opponents" / "public" / "moon_counts_melons.py"),
        "kaito_v17": str(ROOT / "opponents" / "public" / "kaitofukami_v17_market_ranker.py"),
    }
    configs = {
        "v031": {"strawberry": False, "land": False},
        "+strawberry": {"strawberry": True, "land": False},
        "+land/hands": {"strawberry": False, "land": True},
        "+strawberry+land/hands (v040)": {"strawberry": True, "land": True},
    }
    results = {}
    
    print("Executing v040 Quick Stress Screening (32 matches per config)...")
    for name, flags in configs.items():
        matches = []
        for opp_name, opp_path in opponents.items():
            for seed in seeds:
                for seat in (0, 1):
                    os.environ["KAGGRI_DEBUG_RAISE"] = "1"
                    agent_fn = build_and_patch_v040(flags["strawberry"], flags["land"])
                    
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
        print(f"  Ablation {name:28s}: margin={s['avg_money_margin']:+.1f} cand_money=${s['avg_candidate_money']:.1f} opp_money=${s['avg_opponent_money']:.1f} outcome={s['avg_outcome']:.3f}")
        
    return results


def run_full_frontier_for_candidate(best_name: str, best_flags: dict):
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
                    agent_fn = build_and_patch_v040(best_flags["strawberry"], best_flags["land"])
                    
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
            
    return results


def write_report(ab_results, best_name, full_frontier):
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Save raw json
    (reports_dir / "v040_ablation_results.json").write_text(json.dumps({
        "ablation_screening": ab_results,
        "promoted_frontier": full_frontier
    }, indent=2, default=str), encoding="utf-8")
    
    # Markdown
    md = [
        "# Stage v040 — Compound Crop Capacity Ablation & Evaluation Report",
        "Evaluates Strawberry, Land Expansion (NE Quadrant), and Dynamic hands scaling.",
        "\n## 1. Quick Stress Screening Matrix (32 matches per candidate)\n",
        "| Candidate | Strawberry | Land Expansion | Target Hands | Avg Candidate Cash | Avg Opponent Cash | Avg Money Margin | Win/Loss/Tie | Avg Outcome | Wilson LB | Weeds |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, r in ab_results.items():
        s = r["summary"]
        straw = "Yes" if "strawberry" in name or "v040" in name else "No"
        land = "Yes" if "land" in name or "v040" in name else "No"
        hands = "Up to 10/12 (Dynamic)" if land == "Yes" else "Up to 6"
        md.append(
            f"| `{name}` | {straw} | {land} | {hands} | ${s['avg_candidate_money']:.1f} | ${s['avg_opponent_money']:.1f} | "
            f"${s['avg_money_margin']:+.1f} | {s['wins']}/{s['losses']}/{s['ties']} | {s['avg_outcome']:.3f} | {s['wilson_lower_95']:.3f} | {s['avg_weeds_at_end']:.2f} |"
        )
        
    md.append("\n## 2. Full Public Frontier Benchmark (Selected Candidate)\n")
    md.append(f"The promoted candidate is **`{best_name}`**.")
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
    
    md.append(f"\n**Global Public-Field Macro League Score (Promoted Candidate):** `{league_macro:.3f}`\n")
    
    # Causal insights
    md.append("## 3. Causal Interpretation & Dynamic Growth Insights\n")
    v31_cash = ab_results["v031"]["summary"]["avg_candidate_money"]
    straw_cash = ab_results["+strawberry"]["summary"]["avg_candidate_money"]
    land_cash = ab_results["+land/hands"]["summary"]["avg_candidate_money"]
    full_cash = ab_results["+strawberry+land/hands (v040)"]["summary"]["avg_candidate_money"]
    
    md.append(f"- **Strawberry Economy Impact (+strawberry - v031)**: **{straw_cash - v31_cash:+.1f}** average cash change on 16 tiles.")
    md.append(f"- **Land & Labor Expansion Impact (+land/hands - v031)**: **{land_cash - v31_cash:+.1f}** average cash change on three-crop economy.")
    md.append(f"- **Synergistic Compound Growth Impact (v040 - v031)**: **{full_cash - v31_cash:+.1f}** average cash change when combining both factors.")
    
    (reports_dir / "v040_ablation_report.md").write_text("\n".join(md), encoding="utf-8")
    print("Ablation & benchmark reports successfully written to: reports/v040_ablation_report.md")


def main():
    # 1. Run quick stress screening
    ab_results = run_quick_stress_screening()
    
    # 2. Select the best candidate based on avg_candidate_money (tie-breaker)
    best_name = max(ab_results.keys(), key=lambda name: (ab_results[name]["summary"]["avg_outcome"], ab_results[name]["summary"]["avg_candidate_money"]))
    
    # 3. Determine best flags
    best_flags = {
        "strawberry": "strawberry" in best_name or "v040" in best_name,
        "land": "land" in best_name or "v040" in best_name,
    }
    
    # 4. Run full frontier for the selected best candidate
    full_frontier = run_full_frontier_for_candidate(best_name, best_flags)
    
    # 5. Write beautiful reports
    write_report(ab_results, best_name, full_frontier)


if __name__ == "__main__":
    main()
