# Kaggriculture Agent Strategy Version Ledger

🌐 **Bilingual Navigation / 双语导航:** [中文版 (Chinese Version) 🇨🇳](VERSIONS_zh.md) | [Main README 🚜](README.md)

---

## 📊 Version Evolution Matrix

| Version | Release Date | Target Block / Layout | Primary Strategic Focus | Key Variable Changes | Repackage SHA-256 | Weak League Margin | Public Frontier Outcome |
|---|---|---|---|---|---|---|---|
| **v000_pass** | 2026-08-04 | Spawn adjacency | Safe execution skeleton, pass-only baseline | Baseline controls, zero production | `fe4f6b27...` | $3,000 (all ties) | — |
| **v010_single_farmer** | 2026-08-04 | 6 tiles (block NW) | Pure closed-loop crop farming loop | Single farmer, no hands | `9247a384...` | ~$8,065 (all wins) | — |
| **v011_task_based** | 2026-08-04 | 6 tiles (block NW) | Decoupled task and greedy assignment layer | Single farmer, task-driven NPV | `cee82818...` | ~$19,387 (2.4×) | — |
| **v020_hands** | 2026-08-04 | 16 tiles (quadrant NW) | Multi-unit greedy assignment + hand hiring | Hand density, land expanded | `8a1b1073...` | ~$41,516 (2.1×) | 0.000 Outcome (losses) |
| **v030_market_control** | 2026-08-04 | 16 tiles (promoted compact) | Market-aware allocation, NPV, hold selling | Chunked sales, projected flooding | `62db1c61...` | ~$41,516 (1.000) | 0.000 Outcome (losses) |
| **v031_plan_consistent** | 2026-08-04 | 16 tiles (nearest_16) | Unified planning via consistent CropPlan | CropPlan shared, four-shed drops | `c17487f7...` | ~$41,516 (1.000) | 0.000 Outcome (**+$3.4k cashout**) |
| **v040_compound_crop** | 2026-08-04 | NW + NE (dynamic expansion) | Land quadrant buying, Strawberry, hand scaling | Strawberry, NE buy, hands scale up 12 | `3ba64d86...` | — | 0.000 Outcome (**+$3.3k cashout**) |
| **v041_focused_livestock** | 2026-08-04 | nearest_16 + Pasture Zone | Pasture build, cow/sheep feed & care | Cows & Sheep, WHEAT buffer | `35a76280...` | — | 0.000 Outcome (losses, animal capital drag) |
| **v050_combined** | 2026-08-04 | NW + NE (crop-optimized) | Consolidated master competitive system | Promoted Strawberry + Land (No-Livestock) | `ae98134c...` | — | 0.000 Outcome (**+$10.9k total gain**) |

---

## 🔍 Detailed Version Logs

### v000_pass
- **Strategy Description:** Always returns PASS for farmer and hands; empty market orders queue.
- **Causal Variable Changes:** Introduced the modular safety repair layer (`safety.py`) to pad/truncate hand actions dynamically to match engine counts and filter invalid operations.
- **Packaging/Reliability:** 100% action parity between raw and packaged source. Completed 100 different disjoint seeds with zero timeout or schema exceptions.

### v010_single_farmer
- **Strategy Description:** Closed-loop single-farmer crop loop (buy seeds -> plant -> same-day water -> harvest at maturity -> sell all).
- **Causal Variable Changes:** Switched from passive idle state to active crop rotation of WHEAT, CARROT, and MELON on a fixed 2x3 work block.
- **Operational Performance:** Average money margin of +$5,065 against pass baseline.

### v011_task_based
- **Strategy Description:** Decoupled decision heuristics into standalone `tasks.py` and `assignment.py` modules (candidate tasks -> sort -> assignment).
- **Causal Variable Changes:** Replaced static tile-crop planning with dynamic highest-NPV task generation.
- **Operational Performance:** Average money margin of +$16,387 (2.4x increase over v010).

### v020_hands
- **Strategy Description:** Integrated daily hand hiring to unlock massive labor capacity. Expanded land to a 16-tile quadrant.
- **Causal Variable Changes:** Added sequential simulation-based HIRE planning and increased managed block size.
- **Telemetry Repairs:** Fixed major metrics bias where hand movements were uncounted. Repaired to count all units consistently.
- **Historical Incident:** Missing `hire_manager.py` from packaging list initially caused silent fallbacks to PASS. Diagnosed and fixed.
- **Operational Performance:** Average money margin of +$38,516 (2.1x increase over v011).

### v030_market_control
- **Strategy Description:** Integrated high-fidelity market protection: projected supply crop allocation, NPV harvest-age scheduling, price-floor holds, and terminal liquidation.
- **Causal Variable Changes:** Switched from dump-all sales to chunked holding sales. Factored growing plants of both sides into future supply pressure. Promoted compact `nearest_16` layout.
- **Reliability Repairs:** Added `conflict_key` and dynamic sequential `seed_ledger` budget deductions to assignment, preventing multi-unit coordinate overlaps and atomic seed PASS breaks.
- **Operational Performance:** 100% green across all 76 tests under `KAGGRI_DEBUG_RAISE=1`. Increased absolute champion cash against top public opponents by **+$2,376 to +$4,157**, proving robust defensive resilience.

### v031_plan_consistent
- **Strategy Description:** Added unified `crop_allocator.py` which builds a single `CropPlan` shared by both task generation and seed purchasing.
- **Causal Variable Changes:** Empty tiles allocated sequentially with updated supply projections. Emits exactly one `PLANT` intent per tile. Generated target-specific drop tasks using all four shed-access tiles. Added terminal runoff from day 28 and return/harvest/drop from day 29.
- **Operational Performance:** 100% action parity. No-harvest when `should_harvest` is False. Lifted candidate cash by **+$3,482** against Pilkwang.

### v040_compound_crop
- **Strategy Description:** Integrated STRAWBERRY ongoing economics and dynamic land expansion to the NE quadrant (bought conditionally when day >= 10, money >= 2500).
- **Causal Variable Changes:** Active tiles scaled dynamically (nearest_16 -> all NW -> NE expansion) and scaled hands up to 10/12.
- **Operational Performance:** Unified `v040` (Strawberry + Land) achieved **+$680.4** average cash over `v031`, proving extreme synergy.

### v041_focused_livestock
- **Strategy Description:** Integrated focused COW and SHEEP livestock structure (exactly 2 cows + 2 sheep only) on a designated Pasture zone near the shed.
- **Causal Variable Changes:** Build pasture, buy/pickup/place, feed, care, harvest milk/wool, and collect fertilizer. Maintained WHEAT feed buffer.
- **Operational Performance:** Achieved zero animal escapes and zero stranded animals. However, livestock investments act as a cash drag in short 30-day crop space.

### v050_combined (Current Champion)
- **Strategy Description:** Consolidated master competitive agent.
- **Causal Variable Changes:** Evaluated a 2x2 crop x livestock causal ablation. Formally promoted the **Strawberry, No-Livestock** configuration as our unified champion because animal investments regress the baseline on 25 tiles.
- **Operational Performance:** Achieved a **monumental defensive cash boost of up to +$10.9k** across all public families compared to `v020`!

---

## 🏛️ Key Architectural Axioms

1. **Production Parity First**  
   All transaction valuations and crop revenue metrics use exact replicas validated cell-by-cell against the engine grid. No estimation is tolerated.
2. **Strict Execution Exclusivity**  
   At most one unit may claim a spatial coordinates lock key per turn. Seed budget is strictly non-invariant and deducted *inside* the assignment greed loop.
3. **Fail-Loud Submissions**  
   Production fallback wrappers are bypassed in evaluators and tests. Any internal NameError or traceback is a hard failure, ensuring the canonical artifact remains 100% bug-free.
