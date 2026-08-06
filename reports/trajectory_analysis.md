# Kaggriculture Trajectory Analysis & Competitive Audit

This report performs a deep, quantitative trajectory analysis of the Kaggriculture simulation game, comparing our crop-only 16-tile baseline (`v030`/`v031`) against the state-of-the-art public champion **`Kaito v17 Market Ranker`** and the melon-heavy giant **`Moon Counts Melons`**.

---

## 1. The Production Ceiling Gap (Causal Audit)

In our previous evaluations on 8 screen seeds, we observed a massive, seemingly insurmountable cash deficit:
- **Our Agent (`v030`/`v031`/`v050`):** Avg cash ~$31k - $35k.
- **Public Baseline (`Kaito v17` / `Moon`):** Avg cash ~$175k - $179k.

By analyzing the step-by-step telemetry and source code of `Kaito v17`, we have isolated the precise causal variables behind this $140k+ gap:

### A. Physical Acreage & Land Expansion
- **Our Agent:** Restricts itself strictly to the NW quadrant (16 active tiles).
- **Kaito v17:** Dynamically executes **conditional land purchases** to unlock the `NE` quadrant on day 5 (`land_ne_day = 5`) and the `SW` quadrant on day 10 (`land_sw_day = 10`). This expands their physical cultivation limit from 16 tiles to **75 active tiles** (an increase of 4.6x!).

### B. Labor Force Scaling
- **Our Agent:** Caps hand hiring at 6 hands.
- **Kaito v17:** Scales hiring aggressively up to **13 hands** (the maximum engine cap) as land expands, ensuring they have sufficient worker capacity to water and harvest 75 tiles without weed infestations.

### C. Advanced Ongoing Crop Flow (Strawberry)
- **Our Agent:** Uses strawberry as a niche crop on a tiny 16-tile footprint, where it has neutral or negative marginal yield due to capital crowding.
- **Kaito v17:** Focuses on cultivating up to **34 Strawberry crops** across their expanded land. Since Strawberry yields 1 unit every 2 days, 34 plants produce a persistent flow of **17 Strawberries per day** (generating up to **+$2,040 revenue per day** at base prices!).

### D. Livestock Synergy & Fertilizer Loops
- **Our Agent:** Disables livestock entirely in `v050` because buying cows and sheep in a tiny 16-tile/25-tile crop-only NW quadrant is a severe capital drag (takes over $1800 cash from our day 0-2 opening, starving our crop investments).
- **Kaito v17:** Safely defers livestock setup until day 4 (when they have accumulated crop profits), then scales up to **8 Cows and 6 Sheep** (fully automated and fed from a safe Wheat buffer). These animals yield:
  - Milk ($160 base) and Wool ($200 base) which sell for massive premiums at town shops (2x multipliers in smoothie shops and yarn stores).
  - Continuous **Fertilizer collection**, which is immediately routed to fertilize the 34 Strawberry crops, doubling their yield tick productivity (+2 instead of +1, generating massive incremental profits).

---

## 2. Competitive Heuristic Opportunities

Because public opponents like `Kaito v17` and `Moon` are heavily reliant on **deterministic, pre-recorded replay tapes** (`_V17_SCHEDULE`, `_V11_RADIANT_SCHEDULE`), they suffer from severe **cognitive rigidity**:
1. **No Market Adaptation**: They blindly execute their pre-recorded plant/buy schedules, even if we flood the market and crash the price of Melon or Strawberry to $1.
2. **Fixed Spending Paths**: They buy land and animals at pre-set turns. If we can manipulate market prices on those exact turns, we can severely restrict their cash flow or drive them into capital starvation.

### Our Strategy for `v060` (To Conquer the Frontier):
Rather than remaining a crop-only 16-tile agent, we must **fight scale with scale!**
We will implement an advanced, fully dynamic, market-aware empire (`v060`) that combines:
- **Quadrants Expansion**: Unlocking NE (day >= 8) and SW (day >= 12) quadrants when our cash reserve is safe.
- **Max Labor Density**: Scaling hiring up to 13 hands as active tiles expand.
- **High-Throughput Strawberry Loops**: Scaling Strawberry plantings across empty unlocked quadrants.
- **Horizon-Aware Livestock Ranching**: Buying Cows (up to 4) and Sheep (up to 4) conditionally when `day <= 12` and `money >= 2500` (so we have a safe capital margin).
- **Safe Wheat Buffers**: Always maintaining a 10+ Wheat buffer in the shed to feed our livestock.
- **Fertilizer Routing**: Automatically routing collected fertilizer to Strawberry crops to double their yield.

By combining these full-horizon, full-map capabilities with our **superior, mathematically perfect, conflict-free assignments, sequential seed ledgers, and price-aware hold thresholds**, we will out-scale and out-adapt their static replays, and **secure victory against all 5 strong baselines!**
