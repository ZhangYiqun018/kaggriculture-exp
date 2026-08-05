"""Ablation Suite (Phase 3R.6): Programmatic Causal Factorial Evaluation.

Evaluates candidates A-E on the fixed 8-seed 'screen' set (both seats, 16 matches each).

Candidates:
- A:  6 tiles / 0 hands
- B: 16 tiles / 0 hands
- C:  6 tiles / fixed 6 hands
- D: 16 tiles / fixed 6 hands
- E: 16 tiles / sequential marginal hands (the true v020)
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kaggle_environments import make  # noqa: E402
from eval.metrics import extract_match_metrics, aggregate_metrics  # noqa: E402

SEED_SETS_PATH = ROOT / "eval" / "seed_sets.json"


def load_seeds() -> list[int]:
    return json.loads(SEED_SETS_PATH.read_text())["screen"]


def create_ablation_agent(variant: str):
    """Load dist/main.py and dynamically patch its parameters to enforce variants A-E."""
    # Mount into sys.modules to prevent Python 3.12 dataclasses sys.modules.get(cls.__module__) NoneType crash
    name = "dist_main"
    spec = importlib.util.spec_from_file_location(name, str(ROOT / "dist" / "main.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    
    # Corrected package variables of the inlined modules inside mod
    # Because of how they are inlined, they are global in mod.
    if variant == "A":
        mod.MANAGED_TILES = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (3, 4)]
        mod.TARGET_HANDS_DAY = 0
        mod.plan_hires = lambda *args, **kwargs: 0
    elif variant == "B":
        mod.TARGET_HANDS_DAY = 0
        mod.plan_hires = lambda *args, **kwargs: 0
    elif variant == "C":
        mod.MANAGED_TILES = [(2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (3, 4)]
        mod.TARGET_HANDS_DAY = 6
        # To make it "fixed 6 hands", we patch plan_hires to return max(0, 6 - current_hands)
        mod.plan_hires = lambda gs, tasks, max_hands=6, **kwargs: max(0, max_hands - gs.self_farm.hand_count)
    elif variant == "D":
        mod.TARGET_HANDS_DAY = 6
        mod.plan_hires = lambda gs, tasks, max_hands=6, **kwargs: max(0, max_hands - gs.self_farm.hand_count)
    elif variant == "E":
        # Uses the default (16 tiles + true sequential plan_hires)
        pass
        
    return mod.agent


def run_ablation() -> dict:
    seeds = load_seeds()
    # Opponent is the starter baseline
    opponent_path = str(ROOT / "opponents" / "baselines" / "wheat_only.py")
    variants = ["A", "B", "C", "D", "E"]
    results = {}
    
    print(f"Running Factorial Ablation on {len(seeds)} screen seeds (both seats) against wheat_only...")
    
    for v in variants:
        matches = []
        # Create fresh patched agent per run to avoid leaks
        for seed in seeds:
            for seat in (0, 1):
                agent_fn = create_ablation_agent(v)
                agents = [agent_fn, opponent_path] if seat == 0 else [opponent_path, agent_fn]
                
                env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
                env.run(agents)
                m = extract_match_metrics(env, candidate_idx=seat)
                m["seed"] = seed
                m["seat"] = seat
                matches.append(m)
        results[v] = {
            "summary": aggregate_metrics(matches),
            "matches": matches,
        }
        print(f"  Variant {v}: outcome={results[v]['summary']['avg_outcome']} margin=${results[v]['summary']['avg_money_margin']:.0f} weeds={results[v]['summary']['avg_weeds_at_end']}")
        
    return results


def write_reports(results: dict):
    # JSON
    jp = ROOT / "reports" / "ablation_results.json"
    jp.write_text(json.dumps(results, indent=2, default=str))
    
    # Markdown
    md = [
        "# Phase 3R.6: Causal Factorial Ablation Report\n",
        "Evaluated on 8 'screen' seeds × both seats (16 matches per candidate) against `wheat_only`.",
        "\n## Factorial Matrix\n",
        "| Candidate | Managed Tiles | Hiring Strategy | Avg Final $ (Agent) | Avg Margin ($) | Avg Outcome | Wilson LB | Terminal Weeds | Movement % |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for v, r in results.items():
        s = r["summary"]
        tiles = "6 (block)" if v in ("A", "C") else "16 (quadrant)"
        strategy = "0 hands (farmer only)" if v in ("A", "B") else ("6 hands (blind fixed)" if v in ("C", "D") else "sequential marginal")
        
        # Pull extra details from first match of the variant
        m_sample = r["matches"][0]
        md.append(
            f"| **{v}** | {tiles} | {strategy} | "
            f"${s['min_candidate_money']:.0f} (min) | "
            f"${s['avg_money_margin']:.0f} | "
            f"{s['avg_outcome']:.3f} | "
            f"{s['wilson_lower_95']:.3f} | "
            f"{s['avg_weeds_at_end']:.1f} | "
            f"{m_sample['movement_action_ratio'] * 100:.1f}% |"
        )
    
    md.append("\n## Causal Interpretation\n")
    # Calculate effects
    # Tile effect at 0 hands: B - A
    tile_effect_no_hands = results["B"]["summary"]["avg_money_margin"] - results["A"]["summary"]["avg_money_margin"]
    # Hand effect at 6 tiles: C - A
    hand_effect_small_farm = results["C"]["summary"]["avg_money_margin"] - results["A"]["summary"]["avg_money_margin"]
    # Interactive effect: D - (A + tile_effect + hand_effect)
    inter_effect = results["D"]["summary"]["avg_money_margin"] - (results["A"]["summary"]["avg_money_margin"] + tile_effect_no_hands + hand_effect_small_farm)
    # Marginal vs Blind hiring effect: E - D
    marginal_vs_blind = results["E"]["summary"]["avg_money_margin"] - results["D"]["summary"]["avg_money_margin"]

    md.append(f"- **Tile Scaling Effect (0 hands, B - A)**: ${tile_effect_no_hands:+.0f} margin.")
    md.append(f"- **Hand Hiring Effect (6 tiles, C - A)**: ${hand_effect_small_farm:+.0f} margin.")
    md.append(f"- **Synergistic Interactive Effect (D - [A+T+H])**: ${inter_effect:+.0f} margin.")
    md.append(f"- **Marginal-Hiring vs Blind-Hiring Effect (E - D)**: ${marginal_vs_blind:+.0f} margin.")

    (ROOT / "reports" / "ablation_report.md").write_text("\n".join(md))
    print(f"Reports written to: reports/ablation_report.md")


if __name__ == "__main__":
    import os
    os.environ["KAGGRI_DEBUG_RAISE"] = "1"  # fail-loud during ablation!
    r = run_ablation()
    write_reports(r)
