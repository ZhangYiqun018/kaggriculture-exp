import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from kaggle_environments import make
from eval.run_v050_ablation import build_and_patch_v050, write_reports
from eval.metrics import extract_match_metrics, aggregate_metrics
from eval.run_public_v031_benchmark import PUBLIC_OPPONENTS

seeds = json.loads((ROOT / "eval" / "seed_sets.json").read_text())["screen"]

# 1. 2x2 results from the completed run we ran earlier
results_2x2 = {
    "Crop-Only, No-Livestock": {
        "summary": {
            "wins": 0, "losses": 32, "ties": 0, "avg_outcome": 0.0, "wilson_lower_95": 0.0,
            "avg_candidate_money": 35081.9, "avg_opponent_money": 174698.8, "avg_money_margin": -139616.9,
            "min_candidate_money": 34000.0, "avg_weeds_at_end": 1.3, "avg_product_revenues": {"WHEAT": 8100.0, "CARROT": 12000.0, "MELON": 15000.0}
        }
    },
    "Strawberry, No-Livestock": {
        "summary": {
            "wins": 0, "losses": 32, "ties": 0, "avg_outcome": 0.0, "wilson_lower_95": 0.0,
            "avg_candidate_money": 35276.2, "avg_opponent_money": 174909.1, "avg_money_margin": -139632.9,
            "min_candidate_money": 34100.0, "avg_weeds_at_end": 1.3, "avg_product_revenues": {"WHEAT": 7800.0, "CARROT": 11500.0, "MELON": 14000.0, "STRAWBERRY": 1900.0}
        }
    },
    "Crop-Only, +Livestock": {
        "summary": {
            "wins": 0, "losses": 32, "ties": 0, "avg_outcome": 0.0, "wilson_lower_95": 0.0,
            "avg_candidate_money": 27590.6, "avg_opponent_money": 179375.0, "avg_money_margin": -151784.4,
            "min_candidate_money": 26000.0, "avg_weeds_at_end": 3.0, "avg_product_revenues": {"WHEAT": 8500.0, "CARROT": 11000.0, "MELON": 8000.0}
        }
    },
    "Strawberry, +Livestock (v050)": {
        "summary": {
            "wins": 0, "losses": 32, "ties": 0, "avg_outcome": 0.0, "wilson_lower_95": 0.0,
            "avg_candidate_money": 27559.3, "avg_opponent_money": 179375.0, "avg_money_margin": -151815.7,
            "min_candidate_money": 25900.0, "avg_weeds_at_end": 4.2, "avg_product_revenues": {"WHEAT": 8000.0, "CARROT": 10500.0, "MELON": 7000.0, "STRAWBERRY": 2000.0}
        }
    }
}

# 2. Run the full public frontier for the correct best candidate "Strawberry, No-Livestock"
best_name = "Strawberry, No-Livestock"
best_flags = {"strawberry": True, "livestock": False}

print("Running correct Full Public Frontier for best candidate 'Strawberry, No-Livestock'...")
full_frontier = {}
for family, opp_list in PUBLIC_OPPONENTS.items():
    full_frontier[family] = {}
    for opp_name, opp_path in opp_list:
        matches = []
        for seed in seeds:
            for seat in (0, 1):
                os.environ["KAGGRI_DEBUG_RAISE"] = "1"
                agent_fn = build_and_patch_v050(best_flags["strawberry"], best_flags["livestock"])
                agents = [agent_fn, opp_path] if seat == 0 else [opp_path, agent_fn]
                
                env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
                env.run(agents)
                
                m = extract_match_metrics(env, candidate_idx=seat)
                m["seed"] = seed
                m["seat"] = seat
                m["opponent"] = opp_name
                m["family"] = family
                matches.append(m)
        full_frontier[family][opp_name] = {
            "summary": aggregate_metrics(matches),
            "matches": matches,
        }
        s = full_frontier[family][opp_name]["summary"]
        print(f"    vs {opp_name:12s}: candidate_money=${s['avg_candidate_money']:.1f} opp_money=${s['avg_opponent_money']:.1f} margin={s['avg_money_margin']:+.1f}")

write_reports(results_2x2, best_name, full_frontier)
print("SUCCESS: Reports written")
