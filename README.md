# 🚜 Kaggriculture Competitive Agent

🌐 **Bilingual Navigation / 双语导航:** [中文版 (Chinese Version) 🇨🇳](README_zh.md)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![Kaggle environments](https://img.shields.io/badge/Kaggle_Environments-1.32.3-orange.svg?style=for-the-badge)](https://pypi.org/project/kaggle-environments/)
[![Status](https://img.shields.io/badge/Status-Phase_3R.8_Complete-success.svg?style=for-the-badge)]()
[![Champion](https://img.shields.io/badge/Champion-v030_Market_Control-gold.svg?style=for-the-badge)]()

An industry-grade, reproducible competitive agent framework for the Kaggle Kaggriculture simulation competition. Built on top of the pinned official runtime, featuring fail-loud testing diagnostics, deterministic evaluation leagues, and a market-aware production/selling champion.

---

## 🏛️ Pipeline Architecture

Our framework enforces a strict, modular separation of concerns. Decisions flow in one direction with zero global mutable state leaks:

```
  Engine Observation (JSON/Wrapper)
            ↓
     [State Parser] (state.py -> GameState / TileInfo immutable views)
            ↓
    [Economy Engine] (economy.py -> Exact lockstep transaction value)
            ↓
   [Task Generator] (tasks.py -> Exclusivity conflicts, NPV harvest-age)
            ↓
  [Hiring Optimizer] (hire_manager.py -> Sequential planned NPV evaluation)
            ↓
  [Greedy Assigner] (assignment.py -> Space locking & seed-budget ledger)
            ↓
     [Market Policy] (policy.py -> Quantity-aware holds & liquidation)
            ↓
     [Safety Layer] (safety.py -> Atomic budget repairs & fallback schema)
            ↓
       Final Action {"farmer": [...], "hands": [...], "market": [...]}
```

---

## ⚡ Key Features

* 🛠️ **Executable Runtime Contract** — Backed by 10 contract tests verifying real engine behavior directly (turn-ordering, atomic planting PASSes, LOCKED tile traversals, and lockstep market quoting), ignoring outdated documentation.
* 🛡️ **Fail-Loud Submission Safety** — Single-file bundler `package_agent.py` inlines modules in dependency order, ensuring `agent` is the **final callable**. Runs under strict `KAGGRI_DEBUG_RAISE=1` validation to instantly bubble up exceptions.
* 📊 **Repaired Multitrust Telemetry** — Hand movement is tracked consistently, correcting a 7x low-bias under-reporting bug. Parses engine logs for timeouts and stack traces.
* 💰 **v030 Competitive Production & Trading** — Combines **projected-supply marginal crop allocation**, **early-harvest NPV optimization**, **quantity-aware hold price controls**, and **turn-order exploit terminal liquidation**.

---

## 🚀 Quick Start

Ensure you have [uv](https://github.com/astral-sh/uv) installed.

### 1. Environment & Diagnostics Setup
```bash
# Clone the repository and sync pinned dependencies (Python 3.12, environments 1.32.3)
uv sync

# Verify the official runtime contract (5 diagnostic probes)
uv run python scripts/verify_runtime_contract.py

# Run the complete test suite (76/76 passing under fail-loud execution)
export KAGGRI_DEBUG_RAISE=1
uv run pytest tests/ -v
```

### 2. Compilation, Verification & Simulation
```bash
# Package the current champion (v030_market_control) into dist/
uv run python scripts/package_agent.py

# Validate the packaged artifact (syntax, callable check, 3-step run)
uv run python scripts/validate_submission.py dist/main.py

# Generate an interactive HTML sandbox movie of the match (visual沙盘)
uv run python -c "
from kaggle_environments import make, agent
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 101}, debug=True)
env.run([agent.get_last_callable(open('dist/main.py').read()), 'opponents/public/kaitofukami_v17_market_ranker.py'])
with open('replays/champion_vs_kaito_101.html', 'w') as f: f.write(env.render(mode='html'))
"
```

---

## 🏆 Strategic Progress

### 1. Local Weak Opponent League
Smoke seeds set, 720-step episodes, both seats against 4 baseline opponents (pass, random, wheat_only, starter) -> 32 matches.

| Version | Win / Loss / Tie | Avg Final Cash | Movement % | Terminal Weeds | Primary Variable Changes |
|---|---|---|---|---|---|
| **v000_pass** | 0 / 0 / 32 | $3,000 | 0.0% | 0.0 | Pure baseline PASS bot. |
| **v010_single_farmer** | 32 / 0 / 0 | ~$8,065 | 42.1% | 2.4 | Farmer only, static 6-tile layout. |
| **v011_task_based** | 32 / 0 / 0 | ~$19,387 | 45.4% | 1.8 | Dynamic task generation + greedy assignment. |
| **v020_hands** | 32 / 0 / 0 | ~$41,516 | 38.2% | 1.3 | Sequential marginal hiring + NW 16-tile. |

### 2. Competitive Public Frontier
Screen seeds set, 720-step episodes, both seats (16 matches per candidate) against public champions (`moon`, `soil`, `roman_anchor`, `kaito_v17`, `pilkwang`).

| Candidate | vs `moon` (tape) | vs `soil` (tape) | vs `roman_anchor` | vs `kaito_v17` | vs `pilkwang` | Outcome |
|---|---|---|---|---|---|---|
| **v020** (baseline) | $29,012 | $29,012 | $28,805 | $29,012 | $21,860 | 0 / 80 / 0 |
| **v030** (market optimized) | **$31,388** | **$31,388** | **$31,288** | **$31,393** | **$26,017** | **0 / 80 / 0** |
| **Net Gain** | **+$2,376** | **+$2,376** | **+$2,483** | **+$2,381** | **+$4,157** | — |

*Causal Analysis:* Although absolute outcomes remain 0 wins due to severe production-scale caps (crop-only 16-tile restricts us to ~$31k vs opponents' fully unlocked multi-quadrant pastures/tomato setups of ~$175k), **v030 achieves a massive defensive boost (up to +$4.1k)**, proving that quantity-aware selling and hold thresholds successfully mitigate competitor-induced gluts.

---

## 📂 Repository Layout

```
agents/        Versioned agent main.py + source (v000 - v030)
src/kaggriculture_bot/  Safety, state, economy, tasks, assignment, hire_manager, policy, harness
eval/          run_match, run_league, ablation_suite, run_public_v030_benchmark, run_layout_screen
scripts/       package, validate, verify_runtime_contract
tests/         contract, safety, packaging, economy, state, tasks, assignment, hire_manager, metrics
official/      manifest.json, runtime_contract.json (ground truth from installed package)
reports/       Phase reports + league/ablation/public outputs
dist/          Single-file packaged agents (main.py + manifest.json)
```

---

## 🦺 Submission Safety Rules

- `agents/champion` is frozen per version; new experiments must spawn versioned directories `agents/vNNN_*`.
- The final packaged single-file `dist/main.py` must end with `agent` as the last callable; no functions/classes defined after it.
- **Strictly Local Sandbox:** Submission is disabled by default (`SUBMIT_ALLOWED = false`). No actual external commands are executed without explicit auth.
