# Phase 3 Report: Crop Closed-Loop Controller (Incremental 3.0-3.4)

**Date:** 2026-08-04
**Status:** COMPLETE (through Phase 3.4)
**Decision:** PROMOTE (v020_hands as champion)

## 0. Approach

Per user direction, Phase 3 was decomposed into 3.0-3.5 rather than a single 500-800 line controller. Phase 3.5 (market optimization / terminal polish) is intentionally NOT done yet — market overlay is deferred until the production engine is validated, per plan.

## 1. Completed modules

| File | Purpose |
|---|---|
| `state.py` | Immutable GameState/FarmState/TileInfo/MarketState/PrivateState parser — no planner state |
| `economy.py` | Pure functions; `market_price` + `sell_revenue` are **engine-parity verified** over full inventory grid × 9 products |
| `tasks.py` | Tier-disciplined candidate task generation (DYING/DECAY/HARVEST/ROUTINE/PLANT/DROP), no rule-dispatch |
| `assignment.py` | Greedy assignment (closest feasible unit per task), forward-compatible with hands |
| `hire_manager.py` | `should_hire()` marginal same-day completion sim with phantom-hand comparison |
| `agents/v010_single_farmer` | Farmer-only crop loop (reference baseline) |
| `agents/v011_task_based` | Same loop expressed via tasks+assignment; **2.5x v010** |
| `agents/v020_hands` | + marginal hiring; **2.5x v011** |
| `agents/champion` | copy of v020 |

## 2. Exact commands run

```bash
uv run pytest tests/                                    # 65 tests all green
uv run python scripts/package_agent.py agents/v020_hands/main.py
uv run python -m eval.run_league --candidate dist/v020_hands/main.py --seed-set smoke --steps 720
```

## 3. League results (smoke: 4 seeds × 2 seats × 4 opponents = 32 matches)

| Version | W/L/T | Avg outcome | Family macro |
|---|---|---|---|
| v010 | 32/0/0 | 1.0 | 1.0 |
| v011 | 32/0/0 | 1.0 | 1.0 |
| v020 | 32/0/0 | 1.0 | 1.0 |

Head-to-head money (seed 11/23 avg):
- v010: ~$8.0k
- v011: ~$14.0k
- v020: ~$35.8k

## 4. Acceptance probes answered (Phase 3.0)

- **day 0 ranking**: MELON $1420 profit/cycle ($118/day), CARROT $82 (27/day), WHEAT $87 (22/day)
- **day 15**: all three still feasible; melon saturates to $1 if flooded at capacity T
- **day 25**: WHEAT/CARROT viable; MELON infeasible; **day 28**: nothing plantable

## 5. Key incidents logged

1. **`kaggressriculture_bot` vs `kaggressriculture_bot` spelling confusion** caused dist/bundle breakage twice. Root cause: repeated near-identical typos; partially fixed then regressed when rewrite overwrote the fix. lesson: package strips must regex-match the real directory programmatically (done via `os.listdir('src')`).
2. **v020 silent-fail bug**: hire_manager not inlined → NameError → outer except → all-PASS fallback. Diagnosed via official loader repro + short trace. Fix landed.
3. **Town-center consume at step 0** (0%12==0) drops WHEAT inventory to 9999 immediately; parser reflects engine truth, not documentation values.

## 6. Known risks

- Opponent pool is all-own-baselines (pass/starter/wheat_only/det_random). Strong public opponents (replay/tape lineage, Kaito, Pilkwang) not frozen yet — Phase 2's `opponents/public` requirement still open.
- No annotation on per-opponent catastrophic regression yet (all margins positive).
- Market optimization (chunked pricing, ordering search) not yet layered — current v020 sells whole shed each turn (works vs these opponents because they sell little; will fail vs real glut competition).

## 7. Deprecation & rollback

- If hands regress: revert to v011 (`dist/v011_task_based/main.py`, sha256 cee82818...)
- If task architecture itself regresses: revert to v010 (`dist/v010_single_farmer/main.py`, sha256 9247a384...)

## 8. Next phase

**Phase 3.5 or Phase 5A pending user direction** — per user plan, before animals/land we should finish market strategy (chunked selling, terminal liquidation-aware selling) and add task_ablation of aggressive opening (target_hands sweep). Recommend: fill in remaining baseline opponents (market_dump, conservative_cash, previous_champion) before the confirm-tier screen, so the promotion gate has teeth.
