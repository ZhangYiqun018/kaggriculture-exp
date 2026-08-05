# Phase 3.6: Public Opponents Frontier Benchmark Report (v041)
**Candidate:** `/Users/yiqun/Documents/proj/kaggriculture-exp/dist/main.py` (v041_market_control with market-aware allocation, NPV harvesting, chunked selling, and liquidation)
**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent against full registered public roster.

## 1. Roster Summary & Macro Ratings

| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |
|---|---|---|---|---|---|---|---|---|---|---|
| replay_tape_lineage | `moon` | 16 | 0 | 16 | 0 | 0.000 | $27624 | $179772 | $-152148 | 0.000 |
| replay_tape_lineage | `soil` | 16 | 0 | 16 | 0 | 0.000 | $27624 | $179772 | $-152148 | 0.000 |
| replay_tape_lineage | `roman_anchor` | 16 | 0 | 16 | 0 | 0.000 | $27450 | $178101 | $-150651 | 0.000 |
| learned_market_ranker | `kaito_v17` | 16 | 0 | 16 | 0 | 0.000 | $27495 | $178978 | $-151483 | 0.000 |
| economic_control | `pilkwang` | 16 | 0 | 16 | 0 | 0.000 | $22019 | $156490 | $-134471 | 0.000 |

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
| 0 | $418.0 | 2 | MELON:12 | $30 / $36 / $260 |
| 1 | $417.0 | 1 | MELON:12 | $30 / $37 / $264 |
| 2 | $415.0 | 2 | MELON:12 | $31 / $37 / $267 |
| 3 | $414.0 | 1 | MELON:12 | $31 / $38 / $269 |
| 4 | $412.0 | 2 | MELON:12 | $32 / $38 / $271 |
| 5 | $411.0 | 1 | MELON:12 | $31 / $38 / $272 |
| 6 | $409.0 | 2 | MELON:12 | $32 / $38 / $274 |
| 7 | $408.0 | 1 | MELON:12 | $33 / $38 / $275 |
| 8 | $406.0 | 2 | MELON:12 | $34 / $38 / $276 |
| 9 | $405.0 | 1 | MELON:12 | $35 / $38 / $277 |
| 10 | $3.0 | 2 | MELON:3 | $37 / $39 / $250 |
| 11 | $6288.0 | 10 | MELON:10, WHEAT:11 | $40 / $39 / $214 |
| 12 | $10021.0 | 9 | MELON:9, WHEAT:29 | $38 / $39 / $183 |
| 13 | $10275.0 | 12 | MELON:9, WHEAT:30 | $41 / $39 / $181 |
| 14 | $10404.0 | 12 | MELON:9, WHEAT:17 | $41 / $39 / $188 |
| 15 | $11459.0 | 12 | MELON:9, WHEAT:17 | $41 / $40 / $174 |
| 16 | $11696.0 | 10 | MELON:9, WHEAT:32 | $42 / $40 / $181 |
| 17 | $10932.0 | 12 | MELON:9, WHEAT:17 | $42 / $40 / $181 |
| 18 | $11551.0 | 12 | MELON:9, WHEAT:13 | $42 / $40 / $188 |
| 19 | $12792.0 | 3 | MELON:9, WHEAT:3 | $42 / $40 / $194 |
| 20 | $12323.0 | 12 | MELON:9, WHEAT:21 | $43 / $41 / $205 |
| 21 | $11842.0 | 12 | WHEAT:36 | $43 / $41 / $213 |
| 22 | $19908.0 | 9 | WHEAT:42 | $45 / $41 / $140 |
| 23 | $21293.0 | 9 | WHEAT:42 | $46 / $41 / $127 |
| 24 | $20327.0 | 12 | WHEAT:37 | $47 / $41 / $131 |
| 25 | $22148.0 | 12 | WHEAT:30 | $47 / $41 / $122 |
| 26 | $23236.0 | 12 | WHEAT:35 | $47 / $42 / $131 |
| 27 | $23680.0 | 9 | WHEAT:42 | $47 / $42 / $136 |
| 28 | $23537.0 | 8 | WHEAT:8 | $48 / $42 / $152 |
| 29 | $26969.0 | 1 | None | $45 / $42 / $144 |

### Terminal State Inventory (Seed 101, Seat 0)
- **Terminal Shed Inventory:** `{'WHEAT': 0, 'CARROT': 0, 'TOMATO': 0, 'STRAWBERRY': 0, 'MELON': 0, 'EGG': 0, 'MILK': 0, 'WOOL': 0, 'FERTILIZER': 0, 'GOOSE': 0, 'COW': 2, 'SHEEP': 2}`
- **Terminal Carry Inventory:** `[{'WHEAT': 4}, {'WHEAT': 4}]`