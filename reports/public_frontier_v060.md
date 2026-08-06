# Phase 3.6: Public Opponents Frontier Benchmark Report (v060)
**Candidate:** `/Users/yiqun/Documents/proj/kaggriculture-exp/dist/main.py` (v060_market_control with market-aware allocation, NPV harvesting, chunked selling, and liquidation)
**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent against full registered public roster.

## 1. Roster Summary & Macro Ratings

| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |
|---|---|---|---|---|---|---|---|---|---|---|
| replay_tape_lineage | `moon` | 16 | 0 | 16 | 0 | 0.000 | $31868 | $182098 | $-150230 | 0.000 |
| replay_tape_lineage | `soil` | 16 | 0 | 16 | 0 | 0.000 | $31868 | $182098 | $-150230 | 0.000 |
| replay_tape_lineage | `roman_anchor` | 16 | 0 | 16 | 0 | 0.000 | $28967 | $181845 | $-152878 | 0.000 |
| learned_market_ranker | `kaito_v17` | 16 | 0 | 16 | 0 | 0.000 | $24962 | $183962 | $-158999 | 0.000 |
| economic_control | `pilkwang` | 16 | 0 | 16 | 0 | 0.000 | $13662 | $163505 | $-149843 | 0.000 |

## 2. Opponent Family Macro-Averages

| Opponent Family | Macro Average Outcome |
|---|---|
| replay_tape_lineage | 0.000 |
| learned_market_ranker | 0.000 |
| economic_control | 0.000 |

**Global Public-Field Macro League Score:** `0.000`

## 3. Representative Match Telemetry (vs Kaito v17, Seed 101, Seat 0)

Demonstrates daily cash, crop counts, market prices, and hire counts at the end of each day (Turns 23, 47, ...).

| Day | Cash ($) | Hired Hands | Active Crops | Market Prices (WHEAT/CARROT/MELON) |
|---|---|---|---|---|
| 0 | $2038.0 | 2 | MELON:12 | $30 / $36 / $260 |
| 1 | $2037.0 | 1 | MELON:12 | $30 / $37 / $264 |
| 2 | $2035.0 | 2 | MELON:12 | $31 / $37 / $267 |
| 3 | $2034.0 | 1 | MELON:12 | $31 / $38 / $269 |
| 4 | $482.0 | 3 | MELON:12 | $32 / $38 / $271 |
| 5 | $451.0 | 5 | MELON:12 | $31 / $38 / $272 |
| 6 | $411.0 | 3 | MELON:12 | $33 / $38 / $274 |
| 7 | $344.0 | 2 | MELON:12 | $33 / $38 / $275 |
| 8 | $403.0 | 4 | MELON:12 | $35 / $38 / $276 |
| 9 | $401.0 | 2 | MELON:12 | $36 / $38 / $277 |
| 10 | $400.0 | 1 | MELON:11 | $38 / $39 / $250 |
| 11 | $820.0 | 8 | MELON:11 | $40 / $39 / $243 |
| 12 | $7390.0 | 11 | MELON:10, WHEAT:14 | $38 / $39 / $209 |
| 13 | $8169.0 | 13 | MELON:10, WHEAT:28 | $41 / $40 / $186 |
| 14 | $7438.0 | 13 | MELON:10, WHEAT:22 | $41 / $40 / $192 |
| 15 | $7527.0 | 13 | MELON:10, WHEAT:20 | $42 / $40 / $179 |
| 16 | $7767.0 | 13 | MELON:10, WHEAT:23 | $42 / $40 / $186 |
| 17 | $7481.0 | 13 | MELON:10, WHEAT:25 | $42 / $41 / $186 |
| 18 | $8983.0 | 13 | MELON:10, WHEAT:22 | $42 / $41 / $192 |
| 19 | $10365.0 | 13 | MELON:10, WHEAT:18 | $42 / $41 / $198 |
| 20 | $12588.0 | 13 | MELON:10, WHEAT:29 | $42 / $41 / $209 |
| 21 | $12725.0 | 13 | MELON:4, WHEAT:33 | $43 / $41 / $216 |
| 22 | $21065.0 | 13 | WHEAT:34 | $45 / $41 / $165 |
| 23 | $24422.0 | 13 | WHEAT:33 | $46 / $41 / $120 |
| 24 | $27493.0 | 12 | WHEAT:27 | $46 / $41 / $125 |
| 25 | $28725.0 | 13 | WHEAT:26 | $47 / $42 / $115 |
| 26 | $29999.0 | 13 | WHEAT:32 | $47 / $42 / $125 |
| 27 | $30909.0 | 10 | WHEAT:23 | $48 / $42 / $129 |
| 28 | $33797.0 | 10 | WHEAT:1 | $49 / $42 / $146 |
| 29 | $38882.0 | 0 | None | $47 / $42 / $138 |

### Terminal State Inventory (Seed 101, Seat 0)
- **Terminal Shed Inventory:** `{'WHEAT': 0, 'CARROT': 0, 'TOMATO': 0, 'STRAWBERRY': 0, 'MELON': 0, 'EGG': 0, 'MILK': 0, 'WOOL': 0, 'FERTILIZER': 0, 'GOOSE': 0, 'COW': 0, 'SHEEP': 0}`
- **Terminal Carry Inventory:** `[{'WOOL': 4, 'MILK': 6, 'WHEAT': 1}]`