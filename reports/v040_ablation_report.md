# Stage v040 — Compound Crop Capacity Ablation & Evaluation Report
Evaluates Strawberry, Land Expansion (NE Quadrant), and Dynamic hands scaling.

## 1. Quick Stress Screening Matrix (32 matches per candidate)

| Candidate | Strawberry | Land Expansion | Target Hands | Avg Candidate Cash | Avg Opponent Cash | Avg Money Margin | Win/Loss/Tie | Avg Outcome | Wilson LB | Weeds |
|---|---|---|---|---|---|---|---|---|---|---|
| `v031` | No | No | Up to 6 | $34595.8 | $175633.6 | $-141037.8 | 0/32/0 | 0.000 | 0.000 | 0.31 |
| `+strawberry` | Yes | No | Up to 6 | $34561.0 | $175627.3 | $-141066.3 | 0/32/0 | 0.000 | 0.000 | 0.31 |
| `+land/hands` | No | Yes | Up to 10/12 (Dynamic) | $35081.9 | $174698.8 | $-139616.9 | 0/32/0 | 0.000 | 0.000 | 3.03 |
| `+strawberry+land/hands (v040)` | Yes | Yes | Up to 10/12 (Dynamic) | $35276.2 | $174909.1 | $-139632.9 | 0/32/0 | 0.000 | 0.000 | 4.28 |

## 2. Full Public Frontier Benchmark (Selected Candidate)

The promoted candidate is **`+strawberry+land/hands (v040)`**.

| Family | Opponent | N | Wins | Losses | Ties | Avg Outcome | Avg Candidate $ | Avg Opponent $ | Avg Money Margin | Wilson LB |
|---|---|---|---|---|---|---|---|---|---|---|
| replay_tape_lineage | `moon` | 16 | 0 | 16 | 0 | 0.000 | $35525.4 | $174737.3 | $-139211.9 | 0.000 |
| replay_tape_lineage | `soil` | 16 | 0 | 16 | 0 | 0.000 | $35525.4 | $174737.3 | $-139211.9 | 0.000 |
| replay_tape_lineage | `roman_anchor` | 16 | 0 | 16 | 0 | 0.000 | $35042.9 | $171512.5 | $-136469.6 | 0.000 |
| learned_market_ranker | `kaito_v17` | 16 | 0 | 16 | 0 | 0.000 | $35027.0 | $175080.9 | $-140053.9 | 0.000 |
| economic_control | `pilkwang` | 16 | 0 | 16 | 0 | 0.000 | $32802.9 | $154561.9 | $-121759.1 | 0.000 |

**Global Public-Field Macro League Score (Promoted Candidate):** `0.000`

## 3. Causal Interpretation & Dynamic Growth Insights

- **Strawberry Economy Impact (+strawberry - v031)**: **-34.8** average cash change on 16 tiles.
- **Land & Labor Expansion Impact (+land/hands - v031)**: **+486.1** average cash change on three-crop economy.
- **Synergistic Compound Growth Impact (v040 - v031)**: **+680.4** average cash change when combining both factors.