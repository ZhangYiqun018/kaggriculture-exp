# Phase 3.6: Public Opponents Frontier Benchmark Report (v060)
**Candidate:** `/Users/yiqun/Documents/proj/kaggriculture-exp/dist/main.py` (v060_market_control with market-aware allocation, NPV harvesting, chunked selling, and liquidation)
**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent against full registered public roster.

## 1. Roster Summary & Macro Ratings

| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |
|---|---|---|---|---|---|---|---|---|---|---|
| replay_tape_lineage | `moon` | 16 | 0 | 16 | 0 | 0.000 | $35448 | $180873 | $-145425 | 0.000 |
| replay_tape_lineage | `soil` | 16 | 0 | 16 | 0 | 0.000 | $35448 | $180873 | $-145425 | 0.000 |
| replay_tape_lineage | `roman_anchor` | 16 | 0 | 16 | 0 | 0.000 | $26175 | $178812 | $-152636 | 0.000 |
| learned_market_ranker | `kaito_v17` | 16 | 0 | 16 | 0 | 0.000 | $34233 | $178295 | $-144062 | 0.000 |
| economic_control | `pilkwang` | 16 | 0 | 16 | 0 | 0.000 | $29408 | $155389 | $-125981 | 0.000 |

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
| 0 | $493.0 | 5 | MELON:8 | $31 / $36 / $260 |
| 1 | $473.0 | 3 | MELON:11 | $31 / $37 / $264 |
| 2 | $411.0 | 3 | MELON:10 | $31 / $37 / $267 |
| 3 | $409.0 | 2 | MELON:10 | $32 / $38 / $269 |
| 4 | $405.0 | 3 | MELON:11 | $33 / $38 / $271 |
| 5 | $404.0 | 1 | MELON:11 | $32 / $38 / $272 |
| 6 | $403.0 | 1 | MELON:11 | $33 / $38 / $274 |
| 7 | $322.0 | 1 | MELON:11 | $33 / $38 / $275 |
| 8 | $322.0 | 0 | MELON:11 | $35 / $38 / $276 |
| 9 | $322.0 | 0 | MELON:11 | $36 / $39 / $277 |
| 10 | $82.0 | 0 | MELON:9 | $37 / $39 / $250 |
| 11 | $1832.0 | 6 | MELON:12 | $39 / $40 / $240 |
| 12 | $4707.0 | 11 | MELON:11, WHEAT:23 | $38 / $40 / $216 |
| 13 | $1443.0 | 13 | MELON:9, WHEAT:33, CARROT:1 | $40 / $40 / $221 |
| 14 | $3636.0 | 13 | MELON:9, WHEAT:18 | $41 / $40 / $208 |
| 15 | $4411.0 | 13 | MELON:8, WHEAT:23 | $40 / $41 / $197 |
| 16 | $5450.0 | 13 | MELON:8, WHEAT:33 | $41 / $41 / $194 |
| 17 | $4485.0 | 13 | MELON:8, WHEAT:14 | $41 / $41 / $194 |
| 18 | $6510.0 | 13 | MELON:8, WHEAT:23 | $41 / $41 / $200 |
| 19 | $8044.0 | 13 | MELON:8, WHEAT:38 | $41 / $41 / $205 |
| 20 | $10266.0 | 13 | MELON:8, WHEAT:40 | $42 / $41 / $215 |
| 21 | $10378.0 | 13 | WHEAT:41, MELON:2 | $43 / $41 / $222 |
| 22 | $19069.0 | 13 | WHEAT:34, MELON:1 | $45 / $42 / $174 |
| 23 | $21185.0 | 13 | WHEAT:33 | $45 / $42 / $167 |
| 24 | $25112.0 | 13 | WHEAT:44 | $45 / $42 / $160 |
| 25 | $25235.0 | 13 | WHEAT:49 | $47 / $42 / $152 |
| 26 | $26128.0 | 13 | WHEAT:43 | $47 / $42 / $156 |
| 27 | $27073.0 | 13 | WHEAT:34 | $48 / $42 / $160 |
| 28 | $30327.0 | 11 | WHEAT:1 | $48 / $42 / $174 |
| 29 | $35010.0 | 1 | WHEAT:1 | $46 / $42 / $167 |

### Terminal State Inventory (Seed 101, Seat 0)
- **Terminal Shed Inventory:** `{'WHEAT': 0, 'CARROT': 0, 'TOMATO': 0, 'STRAWBERRY': 0, 'MELON': 0, 'EGG': 0, 'MILK': 0, 'WOOL': 0, 'FERTILIZER': 0, 'GOOSE': 0, 'COW': 2, 'SHEEP': 0}`
- **Terminal Carry Inventory:** `[{'FERTILIZER': 2}, {'MILK': 3, 'WOOL': 4}]`