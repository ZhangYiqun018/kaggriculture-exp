# Phase 3.6: Public Opponents Frontier Benchmark Report (v060)
**Candidate:** `/Users/yiqun/Documents/proj/kaggriculture-exp/dist/main.py` (v060_market_control with market-aware allocation, NPV harvesting, chunked selling, and liquidation)
**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent against full registered public roster.

## 1. Roster Summary & Macro Ratings

| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |
|---|---|---|---|---|---|---|---|---|---|---|
| replay_tape_lineage | `moon` | 16 | 0 | 16 | 0 | 0.000 | $30094 | $176846 | $-146752 | 0.000 |
| replay_tape_lineage | `soil` | 16 | 0 | 16 | 0 | 0.000 | $30094 | $176846 | $-146752 | 0.000 |
| replay_tape_lineage | `roman_anchor` | 16 | 0 | 16 | 0 | 0.000 | $29843 | $171771 | $-141928 | 0.000 |
| learned_market_ranker | `kaito_v17` | 16 | 0 | 16 | 0 | 0.000 | $30584 | $175964 | $-145380 | 0.000 |
| economic_control | `pilkwang` | 16 | 0 | 16 | 0 | 0.000 | $26006 | $154693 | $-128686 | 0.000 |

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
| 4 | $1426.0 | 3 | WHEAT:5, MELON:17, CARROT:1 | $32 / $38 / $271 |
| 5 | $1419.0 | 4 | WHEAT:5, MELON:17, CARROT:2 | $31 / $38 / $272 |
| 6 | $1405.0 | 3 | WHEAT:4, MELON:17 | $32 / $38 / $274 |
| 7 | $1542.0 | 4 | WHEAT:3, MELON:17 | $32 / $38 / $275 |
| 8 | $1677.0 | 4 | WHEAT:6, MELON:17 | $34 / $38 / $276 |
| 9 | $1650.0 | 4 | WHEAT:5, MELON:17 | $35 / $38 / $277 |
| 10 | $637.0 | 7 | MELON:8, WHEAT:1 | $37 / $39 / $250 |
| 11 | $9819.0 | 11 | MELON:12, WHEAT:22 | $38 / $39 / $214 |
| 12 | $17452.0 | 11 | MELON:12, WHEAT:25, STRAWBERRY:8 | $37 / $39 / $129 |
| 13 | $13249.0 | 13 | MELON:12, WHEAT:8, STRAWBERRY:10 | $40 / $39 / $133 |
| 14 | $13930.0 | 13 | MELON:11, WHEAT:3, STRAWBERRY:15 | $39 / $39 / $142 |
| 15 | $14928.0 | 7 | MELON:11, WHEAT:6, STRAWBERRY:15 | $40 / $39 / $111 |
| 16 | $14686.0 | 11 | MELON:11, STRAWBERRY:16, WHEAT:4 | $42 / $39 / $120 |
| 17 | $14598.0 | 9 | MELON:11, STRAWBERRY:16, WHEAT:3 | $42 / $40 / $120 |
| 18 | $14672.0 | 0 | MELON:11, STRAWBERRY:15, WHEAT:2 | $43 / $40 / $129 |
| 19 | $14658.0 | 3 | MELON:11, STRAWBERRY:9 | $44 / $40 / $138 |
| 20 | $14071.0 | 13 | MELON:11, WHEAT:11, STRAWBERRY:9 | $45 / $40 / $154 |
| 21 | $13362.0 | 13 | MELON:9, WHEAT:20, STRAWBERRY:9 | $46 / $40 / $165 |
| 22 | $14389.0 | 13 | WHEAT:27, STRAWBERRY:9, MELON:1 | $47 / $40 / $146 |
| 23 | $17427.0 | 13 | WHEAT:43, STRAWBERRY:9 | $48 / $41 / $101 |
| 24 | $17266.0 | 13 | WHEAT:44, STRAWBERRY:9 | $49 / $41 / $106 |
| 25 | $18898.0 | 13 | WHEAT:43, STRAWBERRY:9 | $50 / $41 / $96 |
| 26 | $19898.0 | 13 | WHEAT:37, STRAWBERRY:9 | $50 / $41 / $101 |
| 27 | $22144.0 | 13 | WHEAT:27, STRAWBERRY:9 | $50 / $41 / $106 |
| 28 | $25911.0 | 9 | WHEAT:13, STRAWBERRY:9 | $50 / $41 / $115 |
| 29 | $31220.0 | 3 | STRAWBERRY:6, WHEAT:3 | $48 / $41 / $37 |

### Terminal State Inventory (Seed 101, Seat 0)
- **Terminal Shed Inventory:** `{'WHEAT': 0, 'CARROT': 0, 'TOMATO': 0, 'STRAWBERRY': 0, 'MELON': 0, 'EGG': 0, 'MILK': 0, 'WOOL': 0, 'FERTILIZER': 0, 'GOOSE': 0, 'COW': 0, 'SHEEP': 0}`
- **Terminal Carry Inventory:** `[{'STRAWBERRY': 1, 'WHEAT': 4}, {'STRAWBERRY': 1, 'WHEAT': 3}, {'WHEAT': 1}, {'WHEAT': 2}]`