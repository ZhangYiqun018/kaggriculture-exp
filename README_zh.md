# 🚜 Kaggriculture 竞赛智能体

🌐 **双语导航 / Bilingual Navigation:** [English Version 🇺🇸](README.md) | [版本演进账本 📈](VERSIONS_zh.md)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![Kaggle environments](https://img.shields.io/badge/Kaggle_Environments-1.32.3-orange.svg?style=for-the-badge)](https://pypi.org/project/kaggle-environments/)
[![Status](https://img.shields.io/badge/Status-Phase_3R.8_Complete-success.svg?style=for-the-badge)]()
[![Champion](https://img.shields.io/badge/Champion-v030_Market_Control-gold.svg?style=for-the-badge)]()

Kaggle Kaggriculture 农业模拟竞赛复现级别的竞技智能体开发工程。基于官方固定运行时，具备完整的 Fail-Loud（异常硬报错）测试网、确定性双 seat 联赛评测框架，以及具备高度市场控价能力的生产/销售 Champion 智能体。

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
   [Task 任务生成] (tasks.py -> 独占锁定冲突、NPV 收获期评估)
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

* 🛠️ **可执行的运行时契约** — 拥有 10 个契约测试直接探测装好的 1.32.3 引擎（动作顺序、超种全 PASS、LOCKED 移动、市场 lockstep 结算），彻底摒弃有滞后的文档。
* 🛡️ **Fail-Loud 提交安全网** — `package_agent.py` 单文件合并管线确保 `agent` 为**文件最后一个 callable**。测试在 strict `KAGGRI_DEBUG_RAISE=1` 态下运行，任何隐藏异常（如未 inline 模块导致的 NameError）都会立刻硬报错，拒绝静默。
* 📊 **修复后的多维遥测指标** — Farmer 与 Hands 动作及移动被一致统计，纠正了老版本少算 Hands 导致移动比例低报 7 倍的 bug。
* 💰 **v030 竞技生产与交易** — 协同了**在田作物供给预估**（防砸崩市场）、**提前收割 NPV 优化**、**限价控量分批销售（Holds）** 以及 **Turn order 终局全倾销清算**。

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
# 4. 打包当前 champion (v030_market_control) 到 dist/
uv run python scripts/package_agent.py

# 5. 验证打包产物（语法、加载器、3步短局、Fallback 门槛）
uv run python scripts/validate_submission.py dist/main.py

# 6. 生成一局 720 步与 Kaito v17 对决的交互式可视化 HTML 回放砂盘
uv run python -c "
from kaggle_environments import make, agent
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 101}, debug=True)
env.run([agent.get_last_callable(open('dist/main.py').read()), 'opponents/public/kaitofukami_v17_market_ranker.py'])
with open('replays/champion_vs_kaito_101.html', 'w') as f: f.write(env.render(mode='html'))
"
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

### 2. 线上公开强对手大考（screen 种子集，每对手 16 场整局）
对阵线上知名公开强策略（`moon`、`soil`、`roman_anchor`、`kaito_v17`、`pilkwang`）。

| 智能体候选 | vs `moon` (tape) | vs `soil` (tape) | vs `roman_anchor` | vs `kaito_v17` | vs `pilkwang` | 最终胜负 |
|---|---|---|---|---|---|---|
| **v020** (基线) | $29,012 | $29,012 | $28,805 | $29,012 | $21,860 | 0 胜 80 负 |
| **v030** (市场优化) | **$31,388** | **$31,388** | **$31,288** | **$31,393** | **$26,017** | **0 胜 80 负** |
| **净增量** | **+$2,376** | **+$2,376** | **+$2,483** | **+$2,381** | **+$4,157** | — |

*因果解读：* 虽然由于生产代差（我们限于作物 16 象限的 ~$31k 产能 vs 对手全开多象限/ongoing 番茄施肥/牧场奶牛的 ~$175k）导致最终胜率为 0%，但 **`v030` 取得了极其显著的防御性财务上涨（最高 +$4.1k）**，确凿证明了：**控价 holds 销售与在田作物未来供给预估，成功抵御了强竞争对手带来的倾销砸崩！**

---

## 📂 目录结构

```
agents/        版本化 agent（v000 - v030）与 champion 目录
src/kaggriculture_bot/  safety, state, economy, tasks, assignment, hire_manager, policy, harness
eval/          run_match, run_league, ablation_suite, run_public_v030_benchmark, run_layout_screen
scripts/       打包器、提交校验器、运行时契约探测器
tests/         契约/安全/打包/经济/状态/任务/分配/雇工 测试
official/      manifest.json 与 runtime_contract.json（官方行为真值）
reports/       各阶段报告 + 联赛/消融/公开前沿输出
dist/          单文件打包后的提交产物（dist/main.py 与 dist/manifest.json）
```

---

## 🦺 递交安全约束

- `agents/champion` 每一个版本冻结；新实验在 `agents/` 下建独立目录（如 `agents/vNNN_*`）。
- 打包出的单文件 `dist/main.py` 的最后一行 callable 必须是 `agent`，其后不能再定义函数、类、匿名或别名。
- **纯本地安全沙盒**：默认 `SUBMIT_ALLOWED = false`。未取得你的明确授权前，绝不调用 Kaggle 远端提交命令。
