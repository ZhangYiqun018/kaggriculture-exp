# Kaggriculture Competitive Agent

**English** → jump to [中文](#kaggriculture-竞赛智能体).

A reproduction-grade build of a Kaggle Kaggriculture agent: pinned official runtime (`kaggle-environments==1.32.3`), an executable behavior contract verified against the installed engine, a submission-safe single-file packaging pipeline, and a deterministic paired-seat evaluation league with locked seed sets. The current champion is a deterministic closed-loop crop controller with marginal-value hand hiring — no runtime LLM calls anywhere.

## What this repo can do

- **Verify the official runtime as executable truth** — 10 contract tests probe the installed engine directly (action order: units → market → town → decay → end-of-day; SELL FERTILIZER works; CARE bonus is +1; planting over seed count atomically PASSes all; movement through LOCKED tiles; HIRE takes effect next turn; market settles in lockstep). README in the repo is *not* trusted over source/behavior.
- **Run agents and score them reproducibly** — the league runner (archs: `run_match.py` / `run_league.py`) evaluates on both seats, with fixed seed sets (smoke / screen / confirm / held_out), dimensioned metrics, and JSON/CSV/Markdown reports.
- **Iterate strategies as versioned agents** — agents live in `agents/vNNN_*` (immutable once used in comparison); the latest champion is `agents/champion/main.py` (currently v020_hands).
- **Package a submission artifact** — `scripts/package_agent.py` inlines the bot modules into a single stdlib-only file; `scripts/validate_submission.py` confirms the loader picks `agent` as the **last callable** and that the artifact runs clean.

## Quick start

```bash
# 1. Install deps & reproduce the pinned env (uv-managed, Python 3.12)
uv sync

# 2. Verify the official runtime contract (5 probes)
uv run python scripts/verify_runtime_contract.py

# 3. Run all tests (65 passing as of 2026-08-04)
uv run pytest tests/

# 4. Package the champion into dist/
uv run python scripts/package_agent.py agents/v020_hands/main.py

# 5. Validate it as a submission (loader, schema, 3-step smoke)
uv run python scripts/validate_submission.py dist/v020_hands/main.py

# 6. League evaluation (720-step episodes, both seats, JSON/CSV/MD out)
uv run python -m eval.run_league --candidate dist/v020_hands/main.py --seed-set smoke --steps 720
# or a single match
uv run python -m eval.run_match --candidate dist/v020_hands/main.py --opponent dist/v011_task_based/main.py --seed 11
```

Dependency manager: **uv** (lockfile `uv.lock`). Pin: `kaggle-environments==1.32.3`, `litellm==1.90.0` (avoids the rust-toolchain download in 1.93+).

## Current results (self-play league, 2026-08-04)

Smoke seed set, 720 steps, both seats, 4 opponents (pass / starter / wheat_only / deterministic_random) → 32 matches.

| Agent | W/L/T | Avg final $ (agent) | vs |
|---|---|---|---|
| `v000_pass` | 0/0/32 (baseline) | $3,000 | — |
| `v010_single_farmer` | 32/0/0 | ~$8.0k | beat starter by ~+$4.6k |
| `v011_task_based` | 32/0/0 | ~$14.0k | 2.5× v010 |
| **`v020_hands`** (champion) | **32/0/0** | **~$35.8k** | 2.5× v011 (hiring + larger work block) |

Head-to-head seed 11: v020 $19,248 → $35,670 vs v011 $7,750 → $13,985. All runs deterministic; identical rerun SHA (`0f59af69...`).

## Repo layout

```
agents/        versioned agent main.py + source
src/kaggressriculture_bot/  safety, state, economy, tasks, assignment, hire_manager
eval/          run_match / run_league / metrics / seed_sets.json
scripts/       package, validate, verify_runtime_contract
tests/         contract, safety, packaging, economy, state, tasks, assignment
official/      manifest.json, runtime_contract.json  (ground truth from installed package)
reports/       phase reports + league outputs
dist/          single-file packaged agents
```

## Submission safety rules

- `agents/champion` is frozen per version; new experiments = new `vNNN`.
- The final single-file artifact must end with `agent` as the last callable.
- `deploy allowed` is **off** by default; this repo does not submit without explicit authorization.

---

# Kaggriculture 竞赛智能体

一个可复现的 Kaggriculture Agent 构建工程：固定官方运行时（`kaggle-environments==1.32.3`）、把环境行为落成可执行的运行时契约（直接探测安装好的引擎）、可安全提交的单文件打包管线、以及确定性的双 seat 评测联赛（seed 集固定不可重复挑选）。当前 champion 是一个**确定性闭环作物控制器 + 边际价值雇工**，运行时完全不调 LLM。

## 仓库能做什么

- **验证官方运行时为真值** — 10 个 contract tests 直接探测装好的引擎（动作顺序：单位动作 → 市场订单 → 城镇消费 → 作物衰减 → 日末刷新；`SELL FERTILIZER` 允许；CARE bonus = +1；超种时所有 PLANT 原子变 PASS；允许经过 LOCKED 地块；HIRE 下一回合才生效；市场 lockstep 结算）。**README 低于源码/实际行为**。
- **可复现地跑 agent 和评分** — `eval/run_match.py` / `run_league.py`，双 seat、固定 seed 集（smoke / screen / confirm / held_out）、多维指标、JSON/CSV/Markdown 报告。
- **版本化迭代策略** — agent 放在 `agents/vNNN_*`（用于正式比较后冻结）；最新 champion 是 `agents/champion/main.py`（当前 v020_hands）。
- **安全出包** — `scripts/package_agent.py` 将 bot 模块 inline 成单文件（仅用 stdlib）；`scripts/validate_submission.py` 验证 loader 以 `agent` 为**最后一个 callable**，并跑通短局。

## 启动命令

```bash
# 1. 安装依赖（uv，Python 3.12，锁定官方版本）
uv sync

# 2. 验证官方运行时契约（5 个探针）
uv run python scripts/verify_runtime_contract.py

# 3. 全部测试（当前 65 个全绿）
uv run pytest tests/

# 4. 打包 champion 到 dist/
uv run python scripts/package_agent.py agents/v020_hands/main.py

# 5. 验证提交文件（loader / schema / 短局）
uv run python scripts/validate_submission.py dist/v020_hands/main.py

# 6. 联赛评测（720 步整局，双 seat，输出 JSON/CSV/MD）
uv run python -m eval.run_league --candidate dist/v020_hands/main.py --seed-set smoke --steps 720
# 单场
uv run python -m eval.run_match --candidate dist/v020_hands/main.py --opponent dist/v011_task_based/main.py --seed 11
```

## 当前 self-play 联赛结果（2026-08-04）

smoke seed 集，720 步整局，双 seat，对手 4 个（pass / starter / wheat_only / deterministic_random），共 32 场。

| Agent | 胜/负/平 | 平均最终资金 | 相对 |
|---|---|---|---|
| `v000_pass` | 0/0/32（基线） | $3,000 | — |
| `v010_single_farmer` | 32/0/0 | ~$8.0k | 比 starter 多 ~$4.6k |
| `v011_task_based` | 32/0/0 | ~$14.0k | v010 的 2.5 倍 |
| **`v020_hands`（champion）** | **32/0/0** | **~$35.8k** | v011 的 2.5 倍（雇工 + 扩大作业区） |

单场对位（seed 11）：v020 $35,670 vs v011 $13,985。全部确定性；同参数重跑 SHA 相同。

## 目录结构

```
agents/        版本化 agent（v000/v010/v011/v020）+ champion/
src/kaggressriculture_bot/  safety, state, economy, tasks, assignment, hire_manager
eval/          run_match / run_league / metrics / seed_sets.json
scripts/       打包、验证、运行时契约探测
tests/         契约/安全/打包/经济/状态/任务/分配 测试
official/      manifest.json 与 runtime_contract.json（官方行为真值）
reports/       各阶段报告 + league 输出
dist/          单文件打包后的 agent
```

## 递交安全约束

- `agents/champion` 每个版本冻结；新实验走新 `vNNN`。
- 单文件 artifact 的最后一行 callable 必须是 `agent`。
- 默认 `SUBMIT_ALLOWED=false`；没有明确授权不会做 `kaggle competitions submit`。
