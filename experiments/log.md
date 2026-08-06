# 实验记录 / Experiment Log

## 评测协议
- smoke: 4 seed × 5 opp × 2 seat = 40 场 (~5分钟)
- screen: 8 seed × 5 opp × 2 seat = 80 场 (~10分钟)
- confirm: 50 seed × 5 opp × 2 seat = 500 场 (~60分钟)
- 基线: v060_competitive_champion (当前 champion)

## v060 基线 (已核实)
| 对手 | 我方均价 | 对手均价 | 差距 |
|------|---------|---------|------|
| moon | $30,094 | $176,846 | -$146,752 |
| soil | $30,094 | $176,846 | -$146,752 |
| roman | $29,843 | $171,771 | -$141,928 |
| kaito | $30,584 | $175,964 | -$145,380 |
| pilkwang | $26,006 | $154,693 | -$128,686 |

---

## v061_scale_unlock (进行中 — 畜牧管线修复)
**目标**: 修复畜牧业管线 + 保守规模参数

### 发现的 4 个 P0 级 Bug（畜牧业从未工作过）
1. **PASTURE_TILES 被作物覆盖**: `daily_planner` 的 `crop_plan` 包含 PASTURE_TILES → 牧场永远建不起来
   - 修复: `include_livestock=True` 时从 `empty_tiles` 中排除 PASTURE_TILES
2. **动物被立即出售**: `policy.py` SELL 循环遍历 shed 所有物品，COW/SHEEP 无 CROP_POLICIES 条目 → 默认 hold_threshold=1 → 以 $1 价格立即卖出（买入$400的牛$1卖出）
   - 修复: 添加 `NEVER_SELL = {"COW", "SHEEP"}` 过滤
3. **小麦缓冲区填满 shed**: `total_animals > 0` 包括 shed 中的动物 → 持续购买小麦 → shed 满100 → 日终 _drop_inventories_to_shed 丢弃动物
   - 修复: 仅在 `animals_on_board > 0` 时购买小麦，缓冲区上限 min(10, 3×animals)
4. **PICKUP-PLACE 序列无法完成**: 贪心分配不规划多步序列，farmer 被作物任务占用，PICKUP→移动→PLACE 需要3+步，日终动物回到 shed 循环往复
   - 状态: **未修复** — 需要架构级重设计

### 已尝试但失败的方案
| 方案 | 结果 | 原因 |
|------|------|------|
| 激进规模参数 (NE day≥5, 储备$250) | $8k (vs $30k) | 资本饥饿 |
| 适度规模参数 (NE day≥8, 储备$400) | $27k (vs $30k) | 雇工开销增加但产能不足 |
| Farmer 专用畜牧阶段 (day 0-6) | $8k (vs $30k) | Farmer 不浇水 → 37杂草 → 作物死亡 |
| 修复 Bug 1-3 + 开启畜牧 | MILK=$0 | Bug 4 未修复 |

### 当前状态
- v061 = v060 参数 + Bug 1-3 修复 + 畜牧关闭
- 性能 = v060 基线 ($30k)
- Bug 1-3 修复在畜牧关闭时中性

### 下一步计划
1. **脚本化开局**: 提取冠军磁带前 20 步作为硬编码开局（建牧场+买动物+放置）
2. **或**: 购买后自动放置（跳过 PICKUP-PLACE 序列，直接在购买时放置到最近的空牧场）
3. 规模参数调优需在畜牧工作后进行（畜牧收入是纯增量）
