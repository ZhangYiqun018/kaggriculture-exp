# Phase 3.6: Layout Screening Report
Evaluates three different spatial tile configurations under identical economy and hiring policies.

## 1. Layout Profiles Matrix

| Layout | Capacity (Tiles) | Avg Candidate Money | Avg Opponent Money | Avg Money Margin | Win/Loss/Tie | Avg Outcome | Wilson LB | Weeds |
|---|---|---|---|---|---|---|---|---|
| `current_16` | 16 tiles | $29012.2 | $175277.9 | $-146265.8 | 0/32/0 | 0.000 | 0.000 | 2.44 |
| `nearest_16` | 16 tiles | $29618.2 | $174720.9 | $-145102.8 | 0/32/0 | 0.000 | 0.000 | 1.44 |
| `compact_24` | 24 tiles | $26118.0 | $171002.8 | $-144884.8 | 0/32/0 | 0.000 | 0.000 | 0.12 |

## 2. Layout Selection and Decision

- **Best Performing Layout:** `nearest_16` (Candidate Money: `$29618.2`, Margin: `$-145102.8`).
- **Ablation Insight:** 
  - Compact 24-tile (`compact_24`) vs Baseline 16-tile (`current_16`): **+1380.9** average margin change.
  - Nearest 16-tile (`nearest_16`) vs Baseline 16-tile (`current_16`): **+1163.0** average margin change.

- **Decision:** 
Promote `nearest_16` as our new baseline layout due to higher spatial density (highest average candidate cash of **$29,618.2** and reduced terminal weeds of **1.44**).