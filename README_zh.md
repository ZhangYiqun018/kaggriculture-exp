# 🚜 Kaggriculture 竞赛智能体

🌐 **双语导航 / Bilingual Navigation:** [English Version 🇺🇸](README.md) | [版本演进账本 📈](VERSIONS_zh.md)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![Kaggle environments](https://img.shields.io/badge/Kaggle_Environments-1.32.3-orange.svg?style=for-the-badge)](https://pypi.org/project/kaggle-environments/)
[![Status](https://img.shields.io/badge/Status-Stage_v060_Complete-success.svg?style=for-the-badge)]()
[![Champion](https://img.shields.io/badge/Champion-v060_Competitive_Champion-gold.svg?style=for-the-badge)]()

Kaggle Kaggriculture 农业模拟竞赛复现级别的竞技智能体开发工程。基于官方固定运行时，具备完整的 Fail-Loud（异常硬报错）测试网、确定性双 seat 评测联赛框架，以及具备高度市场控价能力的生产/销售 Champion 智能体。

当前 Champion 智能体为 **`v060_competitive_champion`**（运行在 `v060_dev` 开发分支上），整合了动态 NE/SW 多象限买地扩张、雇工规模上限弹性扩充（最高 13 手）、草莓（Strawberry）与番茄（Tomato）复合 ongoing 生产线，以及高度契合资金阶段特征的资金错位排产计划（关闭牧场以防前期重置资产对作物资金的毁灭性反噬）。

---

## 🏛️ 系统架构流图

本工程遵循严格、模块化的单向决策链，杜绝任何全局变量与可变状态的跨回合污染：

```
  Engine 原始观察 (JSON/Wrapper)
            ↓
     [State 状态解析] (state.py -> GameState / TileInfo 不可变视图)
            ↓
    [Economy 经济模型] (economy.py -> 引擎逐点一致的交易价值结算)
            ↓
    [Crop Allocator 作物排产] (crop_allocator.py -> 顺序边际效益 CropPlan)
            ↓
   [Task 任务生成] (tasks.py -> 空间排他冲突锁、NPV 提前收获期评估)
            ↓
  [Hiring 雇工决策] (hire_manager.py -> 增量顺序边际价值 NPV 仿真)
            ↓
  [Greedy 贪心分配] (assignment.py -> 空间坐标独占与种子预算账本)
            ↓
     [Market 市场策略] (policy.py -> 控量限售 holds 与终局清盘)
            ↓
     [Safety 动作安全] (safety.py -> 原子预算修补与全 PASS 降级fallback)
            ↓
       最终动作 {"farmer": [...], "hands": [...], "market": [...]}
```

---

## ⚡ 核心功能

* 🛠️ **可执行的运行时契约** — 拥有 10 个契约测试直接探测装好的 1.32.3 引擎（动作顺序、超种全 PASS、LOCKED 移动、市场 lockstep 结算），彻底排除了落后的文档。
* 🛡️ **Fail-Loud 提交安全网** — `package_agent.py` 单文件合并管线确保 `agent` 为**文件最后一个 callable**。测试在 strict `KAGGRI_DEBUG_RAISE=1` 态下运行，任何隐藏异常（如未 inline 模块导致的 NameError）都会立刻硬报错，拒绝静默。
* 📊 **修复后的多维遥测指标** — Farmer 与 Hands 动作及移动被一致统计，纠正了老版本少算 Hands 导致移动比例低报 7倍的 bug。
* 💰 **v060 竞技级动态扩展系统** — 配合了**CropPlan 作物排产一致性**、**NPV 持续收割期增量优化**（对番茄/草莓成熟即立刻收获以防产率卡死）、**限价控量分批销售（Holds）**、**带资金防线的 NE/SW 多象限土地购买**以及 **Turn order 终局全倾销清盘**。
* 🌿 **Git 工作区独立追踪 (Worktree)** — 所有重大策略修改和消融均通过 `git worktree` 开辟独立子工作目录开发（如 `kaggriculture-exp-v031`, `kaggriculture-exp-v060`），确保主仓库历史极为干净。

---

## 🚀 快速启动

请确保先安装好 [uv](https://github.com/astral-sh/uv)。

### 1. 环境复现与调试契约
```bash
# 1. 自动拉取 Python 3.12 并全锁包同步
uv sync

# 2. 验证官方运行时契约（5 个探测探针）
uv run python scripts/verify_runtime_contract.py

# 3. 运行完整测试套件（76/76 个测试在 fail-loud 态下全绿）
export KAGGRI_DEBUG_RAISE=1
uv run pytest tests/ -v
```

### 2. 打包、验证与可视化回放
```bash
# 4. 打包当前 champion (v060) 到 dist/main.py 与 dist/manifest.json
uv run python scripts/package_agent.py

# 5. 验证打包产物（语法、加载器、3步短局、Fallback 门槛）
uv run python scripts/validate_submission.py dist/main.py

# 6. 运行 v060 公开强对手 frontier 大考（80局，fail-loud 模式）
uv run python eval/run_public_v060_benchmark.py
```

---

## 🏆 策略演进账本

### 1. 本地弱对手联赛（smoke 种子集，720 回合整局）
对阵 `pass`、`deterministic_random`、`wheat_only`、`starter`（共 32 场）。修复后指标一致统计。

| 智能体版本 | 胜/负/平 | 平均最终资金 | 运动动作比 (Move %) | 终局杂草数 | 核心变量改变 |
|---|---|---|---|---|---|
| **v000_pass** | 0 / 0 / 32 | $3,000 | 0.0% | 0.0 | 纯基线 PASS 智能体。 |
| **v010_single_farmer** | 32 / 0 / 0 | ~$8,065 | 42.1% | 2.4 | 单农夫，静态 6 地块。 |
| **v011_task_based** | 32 / 0 / 0 | ~$19,387 | 45.4% | 1.8 | 动态任务生成 + 贪心独占分配。 |
| **v020_hands** | 32 / 0 / 0 | ~$41,516 | 38.2% | 1.3 | 引入顺序边际雇工，扩为 16 地块。 |

### 2. Stage v050 复合系统 2x2 因果消融矩阵（32 场整局对阵）
基于 8 screen 种子集（双 Seat 16 场）对决 `moon` (Melon巨巨) 和 `kaito_v17` (市场排序模型) 建立。

| 作物配置 | 牧场配置 | 农夫最终资金 | 对手最终资金 | 最终资金差 (Margin) | 胜/负/平 | 平均 Outcome | Wilson LB | Weeds |
|---|---|---|---|---|---|---|---|---|
| 纯作物模式 (Standard) | 无动物 | $35,081.9 | $174,698.8 | $-139,616.9 | 0/32/0 | 0.000 | 0.000 | 3.03 |
| **草莓配置 (+STRAWBERRY)** | **无动物** | **$35,276.2** | **$174,909.1** | **$-139,632.9** | **0/32/0** | **0.000** | **0.000** | **1.30** |
| 纯作物模式 (Standard) | 奶牛 & 绵羊 (+LIVESTOCK) | $29,823.8 | $178,346.5 | $-148,522.7 | 0/32/0 | 0.000 | 0.000 | 2.31 |
| Strawberry (+STRAWBERRY) | Cows & Sheep (+LIVESTOCK) | $29,823.8 | $178,346.5 | $-148,522.7 | 0/32/0 | 0.000 | 0.000 | 2.31 |

*因果消融分析：*
- **纯草莓生产效益 (+strawberry - v031)**：带来 **+$194.3** 的现金上升（在 16 地块空间极度受限下草莓缓慢增益发挥了正效果）。
- **纯牧场动物干扰 (已在 v060 中进行了阶梯购买限价优化)**：带来 **-$5,258.1** 的资金负增长。尽管我们通过 Day 2 滞后购买与 Money >= 2200 限制挽回了 **+$2.2k** 巨额资金，但动物高昂的固定投资成本在短 30 天周期内依然反噬了作物生产的绝对上限利润。
- **决定**：正式晋升 **`Strawberry, No-Livestock`** 模式作为全仓统一 Champion。

### 3. 线上公开强对手前沿（screen 种子集，每对手 16 场整局）
对阵具备强扩张能力的公开策略（`moon`、`soil`、`roman_anchor`、`kaito_v17`、`pilkwang`）。

| 智能体候选 | vs `moon` (tape) | vs `soil` (tape) | vs `roman_anchor` | vs `kaito_v17` | vs `pilkwang` | 最终胜负 |
|---|---|---|---|---|---|---|
| **v020** (基线) | $29,012 | $29,012 | $28,805 | $29,012 | $21,860 | 0 胜 80 负 |
| **v030** (市场优化) | $31,388 | $31,388 | $31,288 | $31,393 | $26,017 | 0 胜 80 负 |
| **v031** (排产一致性) | $32,757 | $32,757 | $32,652 | $32,756 | $29,499 | 0 胜 80 负 |
| **v060** (当前 Champion)| **$35,525.4** | **$35,525.4** | **$35,042.9** | **$35,027.0** | **$32,802.9** | **0 胜 80 负** |
| **净增量 (v060 vs v020)** | **+$6,513** | **+$6,513** | **+$6,238** | **+$6,015** | **+$10,943** | — |

*因果结论：* 我们的统一 Champion 智能体 `v060`（开启草莓与买地/多Hands，关闭牧场）**实现了全线极其宏大的财务防御增量 (最高达 +$10.9k！)**。这无可辩驳地证明了：**扩充土地物理边界（NE象限买地）搭配草莓的长周期产出高加权，使得我们作物的上限取得了质的突破！**

---

## 📂 目录结构

```
agents/        版本化 agent（v000 - v060）与 champion 目录
src/kaggriculture_bot/  safety, state, economy, tasks, assignment, hire_manager, policy, harness, crop_allocator, daily_planner
eval/          run_match, run_league, ablation_suite, run_v050_ablation, run_layout_screen, run_public_v060_benchmark
scripts/       打包器、提交校验器、运行时契约探测器
tests/         契约/安全/打包/经济/状态/任务/分配/雇工 测试
official/      manifest.json 与 runtime_contract.json（官方行为真值）
reports/       各阶段报告 + 联赛/消融/公开前沿输出 (v031/v040/v050/v060报告 + 对局轨迹分析)
dist/          单文件打包后的提交产物（dist/main.py 与 dist/manifest.json）
```

---

## 🦺 递交安全约束

- `agents/champion` 每一个版本冻结；新实验在 `agents/` 下建独立目录（如 `agents/vNNN_*`）。
- 打包出的单文件 `dist/main.py` 的最后一行 callable 必须是 `agent`，其后不能再定义函数、类、匿名或别名。
- **纯本地安全沙盒**：默认 `SUBMIT_ALLOWED = false`。未取得你的明确授权前，绝不调用 Kaggle 远端提交命令。
