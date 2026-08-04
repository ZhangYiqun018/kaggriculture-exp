"""Match and league metrics (spec §9.6).

Computes per-match and aggregate metrics for Kaggressricature episodes.
"""
from __future__ import annotations
import json
from typing import Any


def outcome_score(candidate_reward: float, opponent_reward: float) -> float:
    """win=1, tie=0.5, loss=0 based on final money (reward)."""
    if candidate_reward > opponent_reward:
        return 1.0
    if candidate_reward < opponent_reward:
        return 0.0
    return 0.5


def wilson_lower_bound(wins: int, n: int, z: float = 1.96) -> float:
    """One-sided 95% Wilson score lower bound for a binomial proportion."""
    if n == 0:
        return 0.0
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z / denom) * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return max(0.0, center - margin)


def extract_match_metrics(env, candidate_idx: int) -> dict:
    """Extract §9.6 metrics from a completed episode env.
    
    candidate_idx: 0 or 1 — which seat the candidate was in.
    """
    to = env.toJSON()
    statuses = to["statuses"]
    steps = to["steps"]
    final = steps[-1]
    rewards = [s["reward"] for s in final]
    
    cand_reward = rewards[candidate_idx]
    opp_reward = rewards[1 - candidate_idx]
    
    # Count action types across candidate's steps.
    action_counts: dict[str, int] = {}
    total_steps = 0
    pass_count = 0
    move_count = 0
    market_orders = 0
    for step in steps[1:]:  # step[0] is initial state
        if candidate_idx < len(step):
            action = step[candidate_idx].get("action", {})
            if isinstance(action, dict):
                fa = action.get("farmer", [])
                if isinstance(fa, list) and fa:
                    action_counts[fa[0]] = action_counts.get(fa[0], 0) + 1
                    if fa[0] == "PASS":
                        pass_count += 1
                    elif fa[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                        move_count += 1
                for h in action.get("hands", []):
                    if isinstance(h, list) and h:
                        action_counts[h[0]] = action_counts.get(h[0], 0) + 1
                        if h[0] == "PASS":
                            pass_count += 1
                market_orders += len(action.get("market", []))
        total_steps += 1
    
    total_actions = max(1, sum(action_counts.values()))
    return {
        "status": statuses[candidate_idx],
        "opponent_status": statuses[1 - candidate_idx],
        "outcome": outcome_score(cand_reward, opp_reward),
        "candidate_final_money": cand_reward,
        "opponent_final_money": opp_reward,
        "money_margin": cand_reward - opp_reward,
        "total_steps": total_steps,
        "market_order_count": market_orders,
        "action_type_counts": action_counts,
        "movement_action_ratio": move_count / total_actions,
        "pass_ratio": pass_count / total_actions,
        "exception": statuses[candidate_idx] not in ("DONE",),
        "timeout": False,  # kaggle-environments doesn't surface timeout in toJSON easily
        "invalid_action": False,  # would need error logs to detect
    }


def aggregate_metrics(matches: list[dict]) -> dict:
    """Aggregate a list of match metric dicts into a league summary."""
    n = len(matches)
    if n == 0:
        return {"n": 0}
    wins = sum(1 for m in matches if m["outcome"] == 1.0)
    ties = sum(1 for m in matches if m["outcome"] == 0.5)
    losses = sum(1 for m in matches if m["outcome"] == 0.0)
    outcomes = [m["outcome"] for m in matches]
    avg_outcome = sum(outcomes) / n
    margins = [m["money_margin"] for m in matches]
    return {
        "n": n,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "avg_outcome": round(avg_outcome, 4),
        "wilson_lower_95": round(wilson_lower_bound(wins, n), 4),
        "avg_money_margin": round(sum(margins) / n, 2),
        "min_candidate_money": round(min(m["candidate_final_money"] for m in matches), 2),
        "exception_count": sum(1 for m in matches if m.get("exception")),
        "exception_rate": round(sum(1 for m in matches if m.get("exception")) / n, 4),
    }


def family_macro_average(family_results: dict[str, dict]) -> float:
    """Macro-average of avg_outcome across opponent families."""
    scores = [r["avg_outcome"] for r in family_results.values() if r.get("n", 0) > 0]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)
