# Phase 3.6: Public Opponents Frontier Benchmark Report (v030)
**Candidate:** `/Users/yiqun/Documents/proj/kaggriculture-exp/dist/main.py` (v030_market_control with market-aware allocation, NPV harvesting, chunked selling, and liquidation)
**Evaluated on:** 8 Screen Seeds × 2 seats = 16 matches per opponent against full registered public roster.

## 1. Roster Summary & Macro Ratings

| Opponent Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB 95% |
|---|---|---|---|---|---|---|---|---|---|---|
| replay_tape_lineage | `moon` | 16 | 0 | 16 | 0 | 0.000 | $31388 | $179472 | $-148085 | 0.000 |
| replay_tape_lineage | `soil` | 16 | 0 | 16 | 0 | 0.000 | $31388 | $179472 | $-148085 | 0.000 |
| replay_tape_lineage | `roman_anchor` | 16 | 0 | 16 | 0 | 0.000 | $31288 | $178242 | $-146953 | 0.000 |
| learned_market_ranker | `kaito_v17` | 16 | 0 | 16 | 0 | 0.000 | $31393 | $178017 | $-146624 | 0.000 |
| economic_control | `pilkwang` | 16 | 0 | 16 | 0 | 0.000 | $26017 | $157025 | $-131008 | 0.000 |

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
| 0 | $1718.0 | 2 | MELON:15 | $30 / $36 / $260 |
| 1 | $1636.0 | 2 | MELON:16 | $30 / $37 / $264 |
| 2 | $1634.0 | 2 | MELON:16 | $31 / $37 / $267 |
| 3 | $1632.0 | 2 | MELON:16 | $31 / $38 / $269 |
| 4 | $1630.0 | 2 | MELON:16 | $32 / $38 / $271 |
| 5 | $1628.0 | 2 | MELON:16 | $31 / $38 / $272 |
| 6 | $1626.0 | 2 | MELON:16 | $32 / $38 / $274 |
| 7 | $1624.0 | 2 | MELON:16 | $33 / $38 / $275 |
| 8 | $1622.0 | 2 | MELON:16 | $34 / $38 / $276 |
| 9 | $1620.0 | 2 | MELON:16 | $35 / $38 / $277 |
| 10 | $488.0 | 5 | MELON:9 | $37 / $39 / $250 |
| 11 | $11022.0 | 3 | MELON:12 | $39 / $39 / $214 |
| 12 | $19707.0 | 2 | MELON:12 | $38 / $39 / $129 |
| 13 | $19961.0 | 2 | MELON:12 | $41 / $39 / $133 |
| 14 | $19959.0 | 2 | MELON:12 | $41 / $39 / $142 |
| 15 | $19957.0 | 2 | MELON:12 | $42 / $40 / $125 |
| 16 | $19955.0 | 2 | MELON:12 | $44 / $40 / $133 |
| 17 | $19953.0 | 2 | MELON:12 | $44 / $40 / $133 |
| 18 | $19951.0 | 2 | MELON:12 | $45 / $40 / $142 |
| 19 | $19949.0 | 2 | MELON:12 | $46 / $40 / $150 |
| 20 | $19842.0 | 4 | WHEAT:8, MELON:6 | $47 / $40 / $165 |
| 21 | $24036.0 | 3 | WHEAT:12 | $47 / $41 / $115 |
| 22 | $24220.0 | 3 | WHEAT:14 | $49 / $41 / $115 |
| 23 | $25528.0 | 3 | WHEAT:14 | $49 / $41 / $101 |
| 24 | $26044.0 | 5 | WHEAT:10 | $50 / $41 / $106 |
| 25 | $26770.0 | 3 | WHEAT:15 | $51 / $41 / $96 |
| 26 | $27050.0 | 4 | WHEAT:14 | $51 / $41 / $106 |
| 27 | $27692.0 | 5 | WHEAT:12 | $52 / $41 / $111 |
| 28 | $29018.0 | 1 | WHEAT:3 | $52 / $42 / $115 |
| 29 | $31598.0 | 0 | None | $51 / $42 / $37 |

### Terminal State Inventory (Seed 101, Seat 0)
- **Terminal Shed Inventory:** `{'WHEAT': 0, 'CARROT': 0, 'TOMATO': 0, 'STRAWBERRY': 0, 'MELON': 0, 'EGG': 0, 'MILK': 0, 'WOOL': 0, 'FERTILIZER': 0, 'GOOSE': 0, 'COW': 0, 'SHEEP': 0}`
- **Terminal Carry Inventory:** `[{'WHEAT': 3}]`