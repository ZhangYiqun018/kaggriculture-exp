# Phase 3.6: Public Opponents Frontier Benchmark Report (v031)
**Candidate:** `/Users/yiqun/Documents/proj/kaggriculture-exp/dist/main.py` (v031_market_control with market-aware allocation, NPV harvesting, chunked selling, and liquidation)
**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent against full registered public roster.

## 1. Roster Summary & Macro Ratings

| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |
|---|---|---|---|---|---|---|---|---|---|---|
| replay_tape_lineage | `moon` | 16 | 0 | 16 | 0 | 0.000 | $32757 | $176906 | $-144149 | 0.000 |
| replay_tape_lineage | `soil` | 16 | 0 | 16 | 0 | 0.000 | $32757 | $176906 | $-144149 | 0.000 |
| replay_tape_lineage | `roman_anchor` | 16 | 0 | 16 | 0 | 0.000 | $32652 | $175567 | $-142915 | 0.000 |
| learned_market_ranker | `kaito_v17` | 16 | 0 | 16 | 0 | 0.000 | $32756 | $175486 | $-142730 | 0.000 |
| economic_control | `pilkwang` | 16 | 0 | 16 | 0 | 0.000 | $29499 | $155884 | $-126385 | 0.000 |

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
| 0 | $1716.0 | 3 | MELON:15 | $30 / $36 / $260 |
| 1 | $1714.0 | 2 | MELON:16 | $30 / $37 / $264 |
| 2 | $1712.0 | 2 | MELON:16 | $31 / $37 / $267 |
| 3 | $1710.0 | 2 | MELON:16 | $31 / $38 / $269 |
| 4 | $1708.0 | 2 | MELON:16 | $32 / $38 / $271 |
| 5 | $1706.0 | 2 | MELON:16 | $31 / $38 / $272 |
| 6 | $1704.0 | 2 | MELON:16 | $32 / $38 / $274 |
| 7 | $1702.0 | 2 | MELON:16 | $33 / $38 / $275 |
| 8 | $1700.0 | 2 | MELON:16 | $34 / $38 / $276 |
| 9 | $1698.0 | 2 | MELON:16 | $35 / $38 / $277 |
| 10 | $478.0 | 6 | MELON:9 | $37 / $39 / $250 |
| 11 | $11124.0 | 2 | WHEAT:5, MELON:11 | $39 / $39 / $214 |
| 12 | $19799.0 | 2 | WHEAT:5, MELON:11 | $38 / $39 / $129 |
| 13 | $20023.0 | 2 | WHEAT:3, MELON:11 | $41 / $40 / $133 |
| 14 | $20309.0 | 2 | WHEAT:4, MELON:11 | $41 / $40 / $142 |
| 15 | $20379.0 | 2 | WHEAT:5, MELON:11 | $41 / $40 / $125 |
| 16 | $20347.0 | 2 | WHEAT:4, MELON:11 | $42 / $40 / $133 |
| 17 | $20557.0 | 2 | WHEAT:4, MELON:11 | $43 / $41 / $133 |
| 18 | $20717.0 | 2 | WHEAT:5, MELON:11 | $44 / $41 / $142 |
| 19 | $20685.0 | 2 | WHEAT:4, MELON:11 | $45 / $41 / $150 |
| 20 | $20849.0 | 5 | WHEAT:10, MELON:3 | $45 / $41 / $165 |
| 21 | $25083.0 | 3 | WHEAT:16 | $46 / $41 / $115 |
| 22 | $25297.0 | 3 | WHEAT:16 | $48 / $41 / $115 |
| 23 | $26531.0 | 3 | WHEAT:15 | $48 / $41 / $101 |
| 24 | $26603.0 | 5 | WHEAT:15 | $49 / $41 / $106 |
| 25 | $27408.0 | 4 | WHEAT:14 | $50 / $42 / $96 |
| 26 | $28446.0 | 2 | WHEAT:16 | $50 / $42 / $106 |
| 27 | $28564.0 | 2 | WHEAT:15 | $51 / $42 / $111 |
| 28 | $29436.0 | 3 | WHEAT:2 | $52 / $42 / $115 |
| 29 | $32869.0 | 0 | None | $50 / $42 / $54 |

### Terminal State Inventory (Seed 101, Seat 0)
- **Terminal Shed Inventory:** `{'WHEAT': 0, 'CARROT': 0, 'TOMATO': 0, 'STRAWBERRY': 0, 'MELON': 0, 'EGG': 0, 'MILK': 0, 'WOOL': 0, 'FERTILIZER': 0, 'GOOSE': 0, 'COW': 0, 'SHEEP': 0}`
- **Terminal Carry Inventory:** `[{'WHEAT': 2}]`