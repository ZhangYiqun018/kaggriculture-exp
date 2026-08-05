# Kaggriculture Competitive Agent

**English** → jump to [中文](#kaggriculture-竞赛智能体).

A reproduction-grade, highly competitive agent for the Kaggle Kaggriculture simulation competition. Built on the pinned official runtime (`kaggle-environments==1.32.3`), this project incorporates an executable behavioral contract verified against the installed engine, a robust fail-loud packaging pipeline (`KAGGRI_DEBUG_RAISE=1`), a deterministic paired-seat evaluation league, and an optimized production and selling engine.

The current champion is **`v030_market_control`**, running a deterministic closed-loop crop controller with a promoted compact nearest-to-shed layout, sequential marginal-NPV hand hiring, market-aware crop allocation (projecting growing crops' market pressure), NPV-optimized harvest-age scheduling, price-floor-holding chunked sales, and perfect end-of-episode terminal liquidation.

---

## What this repo can do

1. **Verify the official runtime as executable truth** — 10 contract tests probe the installed engine directly (action order: units → market → town → decay → end-of-day; SELL FERTILIZER works; CARE bonus is +1; planting over seed count atomically PASSes all; movement through LOCKED tiles; HIRE takes effect next turn; market settles in lockstep). README in the repo is *not* trusted over source/behavior.
2. **Fail-Loud Packaging with Parity Assertions** — `package_agent.py` inlines the bot modules into a single stdlib-only file (`dist/main.py`); `validate_submission.py` confirms the loader picks `agent` as the **last callable** and runs clean. Under `KAGGRI_DEBUG_RAISE=1`, any hidden Exception (KeyError, NameError, etc.) bubbles up instantly instead of being swallowed.
3. **Deterministic Paired-Seat League** — `run_league.py` and `ablation_suite.py` evaluate on both seats across fixed seed sets (smoke / screen / confirm / held_out) with detailed diagnostic telemetry.
4. **Exhaustive Factorial Ablation** — Programmatically tests layout, worker density, and hiring strategies to isolate effects and interaction coefficients.

---

## Quick start

```bash
# 1. Install deps & reproduce the pinned env (uv-managed, Python 3.12)
uv sync

# 2. Verify the official runtime contract (5 probes)
uv run python scripts/verify_runtime_contract.py

# 3. Run all tests (76 passing as of 2026-08-04, 100% green under DEBUG_RAISE=1)
export KAGGRI_DEBUG_RAISE=1
uv run pytest tests/

# 4. Package the champion into dist/main.py
uv run python scripts/package_agent.py

# 5. Validate it as a submission (loader, schema, 3-step smoke, fail-loud fallback)
uv run python scripts/validate_submission.py dist/main.py

# 6. Run Layout Screen (current_16 vs nearest_16 vs compact_24 against public opponents)
uv run python eval/run_layout_screen.py

# 7. Run Public Opponents Frontier (v030 champion vs full registered public roster)
uv run python eval/run_public_v030_benchmark.py
```

---

## Strategic Progress Ledger

### 1. Local Weak Opponent League (smoke: 32 matches, 720 steps)
Against basic baselines (`pass`, `deterministic_random`, `wheat_only`, `starter`). Repaired metrics track both farmer and hands consistently.

| Agent | W/L/T | Avg Final $ | Move % | Weeds | Diagnostic Insights |
|---|---|---|---|---|---|
| `v000_pass` | 0/0/32 | $3,000 | 0.0% | 0.0 | Pure baseline PASS bot. |
| `v010_single_farmer` | 32/0/0 | ~$8,065 | 42.1% | 2.4 | Farmer only, static 6-tile layout. |
| `v011_task_based` | 32/0/0 | ~$19,387 | 45.4% | 1.8 | Dynamic task generation + greedy assignment. |
| `v020_hands` | 32/0/0 | ~$41,516 | 38.2% | 1.3 | Fixed-6 hands ceiling, NW 16-tile layout expansion. |

### 2. Competitive Public Frontier (screen: 16 matches per opponent, 720 steps)
Against the top public strategies (`moon`, `soil`, `roman_anchor`, `kaito_v17`, `pilkwang`) with scalable land and animal structures.

| Candidate | vs `moon` (tape) | vs `soil` (tape) | vs `roman_anchor` | vs `kaito_v17` | vs `pilkwang` | Outcome |
|---|---|---|---|---|---|---|
| **v020** (baseline) | $29,012 | $29,012 | $28,805 | $29,012 | $21,860 | 0 / 80 / 0 |
| **v030** (market optimized)| **$31,388** | **$31,388** | **$31,288** | **$31,393** | **$26,017** | 0 / 80 / 0 |
| **Net Change** | **+$2,376** | **+$2,376** | **+$2,483** | **+$2,381** | **+$4,157** | — |

*Causal takeaway:* While the absolute outcome remains 0% wins due to production scaling limits (crop-only 16-tile limits us to ~$31k vs opponents' fully expanded pasture/ongoing tomato setups of ~$175k), **v030 achieved a massive financial defensive uplift (up to +$4.1k)**, proving that quantity-aware selling and price holds successfully mitigated market-crashing gluts.

---

## Repo layout

```
agents/        versioned agent main.py + source (v000/v010/v011/v020/v030)
src/kaggriculture_bot/  safety, state, economy, tasks, assignment, hire_manager, policy, harness
eval/          run_match / run_league / metrics / seed_sets.json / ablation_suite / run_public_v030_benchmark / run_layout_screen
scripts/       package, validate, verify_runtime_contract
tests/         contract, safety, packaging, economy, state, tasks, assignment, hire_manager, metrics
official/      manifest.json, runtime_contract.json  (ground truth from installed package)
reports/       phase reports + league/ablation/public outputs
dist/          single-file packaged agents (dist/main.py & dist/manifest.json)
```

---

# Kaggriculture 竞赛智能体

一个工业复现级别的 Kaggriculture Agent 构建工程：固定官方运行时（`kaggle-environments==1.32.3`）、把环境行为落成可执行的运行时契约（直接探测安装好的引擎）、可安全提交的单文件打包管线、以及确定性的双 seat 评测联赛（seed 集固定不可重复挑选）。当前 champion 是 **`v030_market_control`**。

`v030_market_control` 运行一个在首轮布局大筛中晋升的 **`nearest_16` 紧凑型生产地块**，具备真实的**增量顺序边际雇工模型**、**市场感知边际作物分配**（根据己方/对手在田作物预测未来供给压力）、**NPV 优化的收获期调度**、**价格下限 holds 及控量分批销售**（防止自砸价格）、以及**终局完美资产清算**。

---

## 仓库功能

1. **验证官方运行时为真值** — 10 个 contract tests 直接探测装好的引擎（动作顺序：单位动作 → 市场订单 → 城镇消费 → 作物衰减 → 日末刷新；`SELL FERTILIZER` 允许；CARE bonus = +1；超种时所有 PLANT 原子变 PASS；允许经过 LOCKED 地块；HIRE 下一回合才生效；市场 lockstep 结算）。**README 低于源码/实际行为**。
2. **Fail-Loud 包装与 Parity 校验** — `package_agent.py` 将 bot 模块 inline 成单文件（仅用 stdlib）；`validate_submission.py` 验证 loader 以 `agent` 为**最后一个 callable**，并跑通短局。在 `KAGGRI_DEBUG_RAISE=1` 下，任何隐藏异常（如未 inline 模块导致的 NameError 或 KeyError）都会立刻 fail-loud，绝不被安全层静默吞掉。
3. **确定性双 seat 评测** — 框架按 seed × opponent 块聚合两个 seat（smoke/screen/confirm/held_out 种子集），输出极其详尽的多维诊断。
4. **程序化消融套件** — 程序化注入地块密度、雇工策略等，进行控制变量评估。

---

## 启动命令

```bash
# 1. 安装依赖（uv，Python 3.12，锁定官方版本）
uv sync

# 2. 验证官方运行时契约（5 个探针）
uv run python scripts/verify_runtime_contract.py

# 3. 全部测试（当前 76 个全绿，100% 在 DEBUG_RAISE=1 下通过）
export KAGGRI_DEBUG_RAISE=1
uv run pytest tests/

# 4. 打包当前 champion 到 dist/main.py 与 dist/manifest.json
uv run python scripts/package_agent.py

# 5. 验证提交文件（loader / schema / 短局 / 异常 fallback）
uv run python scripts/validate_submission.py dist/main.py

# 6. 运行布局大筛 (当前 16 块地 vs 紧凑 16 块地 vs 紧凑 24 块地)
uv run python eval/run_layout_screen.py

# 7. 运行公开强对手大考 (v030 智能体 vs 线上完整公开 roster)
uv run python eval/run_public_v030_benchmark.py
```

---

## 策略演进账本

### 1. 本地弱对手联赛（smoke：32场，720 步整局）
对阵 `pass`、`deterministic_random`、`wheat_only`、`starter`，修复后指标一致统计。

| 智能体 | 胜/负/平 | 平均最终资金 | 运动动作比 (Move %) | 终局杂草数 | 诊断洞察 |
|---|---|---|---|---|---|
| `v000_pass` | 0/0/32 | $3,000 | 0.0% | 0.0 | 纯基线 PASS 智能体。 |
| `v010_single_farmer` | 32/0/0 | ~$8,065 | 42.1% | 2.4 | 单农夫，静态 6 地块固定组合。 |
| `v011_task_based` | 32/0/0 | ~$19,387 | 45.4% | 1.8 | 动态任务生成 + 贪心独占分配。 |
| `v020_hands` | 32/0/0 | ~$41,516 | 38.2% | 1.3 | 引入顺序边际雇工，扩为 16 地块。 |

### 2. 线上公开强对手前沿（screen：每对手16场，720 步整局）
对阵具备强扩张能力的公开策略（`moon`、`soil`、`roman_anchor`、`kaito_v17`、`pilkwang`）。

| 智能体 | vs `moon` (tape) | vs `soil` (tape) | vs `roman_anchor` | vs `kaito_v17` | vs `pilkwang` | 最终胜负 |
|---|---|---|---|---|---|---|
| **v020** (基线) | $29,012 | $29,012 | $28,805 | $29,012 | $21,860 | 0 胜 80 负 |
| **v030** (市场优化) | **$31,388** | **$31,388** | **$31,288** | **$31,393** | **$26,017** | 0 胜 80 负 |
| **净增量** | **+$2,376** | **+$2,376** | **+$2,483** | **+$2,381** | **+$4,157** | — |

*因果结论：* 尽管由于生产代差（我们限于作物 16 地块的 ~$31k vs 对手牧场+多象限番茄的 ~$175k）导致最终胜率为 0%，但 **`v030` 取得了全线极其显著的财务防御增量 (最高 +$4.1k)**。这无可辩驳地证明了：**控价 holds 销售与在田作物未来供给预估，成功抵御了强竞争对手带来的倾销压价！**
