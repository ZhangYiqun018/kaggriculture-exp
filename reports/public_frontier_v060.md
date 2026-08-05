# Phase 3.6: Public Opponents Frontier Benchmark Report (v060)
**Candidate:** `/Users/yiqun/Documents/proj/kaggriculture-exp-v060/dist/main.py` (v060_market_control with market-aware allocation, NPV harvesting, chunked selling, and liquidation)
**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent against full registered public roster.

## 1. Roster Summary & Macro Ratings

| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |
|---|---|---|---|---|---|---|---|---|---|---|
| replay_tape_lineage | `moon` | 16 | 0 | 16 | 0 | 0.000 | $30883 | $173009 | $-142126 | 0.000 |
| replay_tape_lineage | `soil` | 16 | 0 | 16 | 0 | 0.000 | $30883 | $173009 | $-142126 | 0.000 |
| replay_tape_lineage | `roman_anchor` | 16 | 0 | 16 | 0 | 0.000 | $29407 | $170577 | $-141170 | 0.000 |
| learned_market_ranker | `kaito_v17` | 16 | 0 | 16 | 0 | 0.000 | $30468 | $174775 | $-144307 | 0.000 |
| economic_control | `pilkwang` | 16 | 0 | 16 | 0 | 0.000 | $17075 | $158877 | $-141803 | 0.000 |

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
| 11 | $5552.0 | 13 | MELON:10, WHEAT:11, STRAWBERRY:11, CARROT:1 | $38 / $39 / $214 |
| 12 | $11802.0 | 13 | MELON:10, WHEAT:13, STRAWBERRY:22, CARROT:2 | $37 / $39 / $133 |
| 13 | $12315.0 | 4 | MELON:10, STRAWBERRY:21, WHEAT:1 | $40 / $39 / $133 |
| 14 | $12266.0 | 13 | MELON:9, WHEAT:15, STRAWBERRY:21 | $40 / $39 / $142 |
| 15 | $12922.0 | 10 | MELON:9, WHEAT:13, STRAWBERRY:21 | $41 / $39 / $111 |
| 16 | $12828.0 | 8 | MELON:9, STRAWBERRY:21, WHEAT:4 | $42 / $39 / $120 |
| 17 | $13386.0 | 0 | MELON:9, STRAWBERRY:21, WHEAT:3 | $42 / $40 / $120 |
| 18 | $13379.0 | 4 | MELON:9, STRAWBERRY:12, WHEAT:2 | $43 / $40 / $129 |
| 19 | $13456.0 | 2 | MELON:9, STRAWBERRY:6 | $44 / $40 / $138 |
| 20 | $12970.0 | 12 | MELON:9, STRAWBERRY:6, WHEAT:4 | $45 / $40 / $154 |
| 21 | $12231.0 | 13 | MELON:6, WHEAT:40, STRAWBERRY:6 | $45 / $40 / $165 |
| 22 | $14670.0 | 13 | WHEAT:45, STRAWBERRY:6 | $47 / $41 / $133 |
| 23 | $17151.0 | 13 | WHEAT:43, STRAWBERRY:6 | $48 / $41 / $101 |
| 24 | $17046.0 | 13 | WHEAT:49, STRAWBERRY:6 | $49 / $41 / $106 |
| 25 | $17081.0 | 13 | WHEAT:22, STRAWBERRY:6 | $50 / $41 / $96 |
| 26 | $20735.0 | 13 | WHEAT:43, STRAWBERRY:6 | $49 / $41 / $101 |
| 27 | $22120.0 | 11 | WHEAT:43, STRAWBERRY:6 | $50 / $41 / $106 |
| 28 | $22912.0 | 11 | STRAWBERRY:4, WHEAT:8 | $51 / $42 / $115 |
| 29 | $28037.0 | 0 | None | $48 / $42 / $65 |

### Terminal State Inventory (Seed 101, Seat 0)
- **Terminal Shed Inventory:** `{'WHEAT': 0, 'CARROT': 0, 'TOMATO': 0, 'STRAWBERRY': 0, 'MELON': 0, 'EGG': 0, 'MILK': 0, 'WOOL': 0, 'FERTILIZER': 0, 'GOOSE': 0, 'COW': 0, 'SHEEP': 0}`
- **Terminal Carry Inventory:** `[{'WHEAT': 8}]`