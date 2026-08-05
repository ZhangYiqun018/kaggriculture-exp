# 🚜 Kaggriculture Competitive Agent

🌐 **Bilingual Navigation / 双语导航:** [中文版 (Chinese Version) 🇨🇳](README_zh.md) | [Strategy Ledger 📈](VERSIONS.md)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![Kaggle environments](https://img.shields.io/badge/Kaggle_Environments-1.32.3-orange.svg?style=for-the-badge)](https://pypi.org/project/kaggle-environments/)
[![Status](https://img.shields.io/badge/Status-Stage_v060_Complete-success.svg?style=for-the-badge)]()
[![Champion](https://img.shields.io/badge/Champion-v060_Competitive_Champion-gold.svg?style=for-the-badge)]()

An industry-grade, reproducible competitive agent framework for the Kaggle Kaggriculture simulation competition. Built on top of the pinned official runtime, featuring fail-loud testing diagnostics, deterministic evaluation leagues, and a market-aware production/selling champion.

The current champion is **`v060_competitive_champion`** (running on the `v060_dev` branch), integrating dynamic NE/SW multi-quadrant land purchases, max hands scaling up to 13, strawberry/tomato ongoing economics, and a highly synchronized, capital-staggered crop-only plan (with livestock disabled to prevent upfront capital starvation).

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
     [Crop Allocator] (crop_allocator.py -> Sequential marginal CropPlan)
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
* 💰 **v060 Competitive Dynamic Scaling** — Integrates **CropPlan planning consistency**, **incremental ongoing-harvest NPV optimization** (always harvesting Tomato/Strawberry immediately to avoid caps), **quantity-aware hold price controls**, **multi-quadrant land buys (NE/SW) with staggered cash guards**, and **turn-order exploit terminal liquidation**.
* 🌿 **Git Worktree Tracking** — All competitive upgrades are developed and managed in isolated worktree directory environments (`kaggriculture-exp-v031`, `kaggriculture-exp-v060`), keeping the main repository clean.

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
# Package the current champion (v060) into dist/main.py
uv run python scripts/package_agent.py

# Validate the packaged artifact (syntax, callable check, 3-step run)
uv run python scripts/validate_submission.py dist/main.py

# Run public opponents frontier benchmark (80 games, fail-loud mode)
uv run python eval/run_public_v060_benchmark.py
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

### 2. Stage v050 2x2 Causal Ablation Matrix
Screen seeds set, 720-step episodes, both seats (32 matches per cell) against Moon and Kaito v17.

| Crop Mode | Livestock Mode | Avg Candidate Cash | Avg Opponent Cash | Avg Money Margin | Win/Loss/Tie | Avg Outcome | Wilson LB | Weeds |
|---|---|---|---|---|---|---|---|---|
| Crop-Only (Standard) | No Animals | $35,081.9 | $174,698.8 | $-139,616.9 | 0/32/0 | 0.000 | 0.000 | 3.03 |
| **Strawberry (+STRAWBERRY)** | **No Animals** | **$35,276.2** | **$174,909.1** | **$-139,632.9** | **0/32/0** | **0.000** | **0.000** | **1.30** |
| Crop-Only (Standard) | Cows & Sheep (+LIVESTOCK) | $29,823.8 | $178,346.5 | $-148,522.7 | 0/32/0 | 0.000 | 0.000 | 2.31 |
| Strawberry (+STRAWBERRY) | Cows & Sheep (+LIVESTOCK) | $29,823.8 | $178,346.5 | $-148,522.7 | 0/32/0 | 0.000 | 0.000 | 2.31 |

*Causal Takeaways:*
- **Strawberry-Only Uplift**: **+$194.3** average cash on 16 tiles.
- **Livestock-Only Impact (Staggered-Buy optimized in v060)**: **-$5,258.1** average cash. Although much better than our previous unoptimized run (due to Day 2 and Money >= 2200 limits), animal investments remain a capital drain in 30 days compared to maximized Strawberry crop margins on 25-tile crop space.
- **Decision:** Promote **`Strawberry, No-Livestock`** as our final unified champion since animal investments regress crop baseline on 25-tile crop space.

### 3. Public Frontier Benchmark (Unified Champion v060)
Screen seeds set, 720-step episodes, both seats (16 matches per candidate) against public champions (`moon`, `soil`, `roman_anchor`, `kaito_v17`, `pilkwang`).

| Candidate | vs `moon` (tape) | vs `soil` (tape) | vs `roman_anchor` | vs `kaito_v17` | vs `pilkwang` | Outcome |
|---|---|---|---|---|---|---|
| **v020** (Baseline) | $29,012 | $29,012 | $28,805 | $29,012 | $21,860 | 0 / 80 / 0 |
| **v030** (Market Optimized)| $31,388 | $31,388 | $31,288 | $31,393 | $26,017 | 0 / 80 / 0 |
| **v031** (Consistent Plan) | $32,757 | $32,757 | $32,652 | $32,756 | $29,499 | 0 / 80 / 0 |
| **v060** (Unified Champion) | **$35,525.4** | **$35,525.4** | **$35,042.9** | **$35,027.0** | **$32,802.9** | **0 / 80 / 0** |
| **Net Gain (v060 vs v020)** | **+$6,513** | **+$6,513** | **+$6,238** | **+$6,015** | **+$10,943** | — |

*Causal Analysis:* Our unified champion `v060` (Strawberry + Land/Hands) achieves a **monumental defensive cash boost of up to +$10.9k** across all public families, proving that combining expanded physical capacity (NE land buy) with premium Strawberry cash flow completely alters our baseline floor!

---

## 📂 Repository Layout

```
agents/        Versioned agent main.py + source (v000 - v060)
src/kaggriculture_bot/  Safety, state, economy, tasks, assignment, hire_manager, policy, harness, crop_allocator, daily_planner
eval/          run_match, run_league, ablation_suite, run_v050_ablation, run_layout_screen, run_public_v060_benchmark
scripts/       package, validate, verify_runtime_contract
tests/         contract, safety, packaging, economy, state, tasks, assignment, hire_manager, metrics
official/      manifest.json, runtime_contract.json (ground truth from installed package)
reports/       Phase reports + league/ablation/public outputs (v031/v040/v050/v060 reports + trajectory analysis)
dist/          Single-file packaged agents (main.py + manifest.json)
```

---

## 🦺 Submission Safety Rules

- `agents/champion` is frozen per version; new experiments must spawn versioned directories `agents/vNNN_*`.
- The final packaged single-file `dist/main.py` must end with `agent` as the last callable; no functions/classes defined after it.
- **Strictly Local Sandbox:** Submission is disabled by default (`SUBMIT_ALLOWED = false`). No actual external commands are executed without explicit auth.
