# Phase 0 Report: Official Runtime Contract Verification

**Date:** 2026-08-04
**Status:** COMPLETE
**Decision:** PROMOTE (to Phase 1)

## 1. What was completed

Pinned and verified the official Kaggriculture runtime contract against the installed `kaggle-environments==1.32.3` package. All behavioral claims in the spec's preamble were tested against actual source and runtime behavior.

## 2. Files created / modified

- `official/manifest.json` — repository, commit, version, truth-priority
- `official/runtime_contract.json` — full behavioral contract extracted from source
- `scripts/verify_runtime_contract.py` — standalone verifier (5 probes)
- `tests/test_official_contract.py` — 10 pytest contract tests (§7.1-7.10)
- `reports/python_version.txt` — Python 3.12.13
- `reports/pip_freeze.txt` — 120 packages
- `pyproject.toml` — uv project with pinned deps
- `.python-version` — 3.12 pinned

## 3. Exact commands run

```bash
uv python pin 3.12
uv venv --python 3.12
uv pip install --python .venv/bin/python "litellm==1.90.0"   # pin to avoid rust build
uv pip install --python .venv/bin/python "kaggle-environments==1.32.3" pytest numpy
uv sync                                                        # reproduces env
uv run python scripts/verify_runtime_contract.py              # 5/5 probes pass
uv run pytest tests/test_official_contract.py -v              # 10/10 tests pass
```

## 4. Test results

- `verify_runtime_contract.py`: **5/5 probes PASS**
- `pytest tests/test_official_contract.py`: **10/10 PASS** in 0.60s

## 5. Spec premise verification (the 4 "latest facts")

| Spec claim | Verified | Source truth |
|---|---|---|
| kaggle-environments 1.32.3 exists, fixes locked-tile movement | ✅ exists; movement onto/through LOCKED allowed (L313-316) | Cannot confirm it was a "fix" (commit `dfa0b96` is a Quoridor test fix, not Kaggriculture), but **current behavior matches spec claim** |
| SELL FERTILIZER allowed (AGENTS.md wrong) | ✅ TRUE | L571 + PRODUCTS includes FERTILIZER (L25); no special-case in `_commit_unit` |
| CARE bonus is +1 not +2 | ✅ TRUE | L800: `pending_care_bonus += 1` |
| Turn order: unit→market→town→decay→eod | ✅ TRUE | interpreter L882-915 |
| Market lockstep, max 10 orders, 1s timeout | ✅ TRUE | L520-603, L535, json config |

## 6. Key contract values (from runtime_contract.json)

- Default: 720 steps, 24 turns/day, 30 days, $3000 start, 100 shed cap, 10 market orders
- Last processed step: 718; DONE set at step 719 (`step >= episodeSteps - 2`)
- CROPS: WHEAT(10/2/4/6), CARROT(20/2/3/4), TOMATO(50/8/8/4 ongoing), STRAWBERRY(100/10/10/4 ongoing), MELON(80/10/12/6)
- Animals: GOOSE(300/COOP/4/1/4), COW(400/PASTURE/8/2/6), SHEEP(500/PASTURE/6/3/6)
- Land: NE→SW→SE at $1000/$2000/$4000
- Hire cost: fib(n)×mult: 1,1,2,3,5,8,13,21...
- Plant→weed: consecutive_unwatered ≥ 2 at eod
- Animal escape: consecutive_unfed ≥ 2 at eod
- PLANT atomicity: if total PLANT for a crop > seeds, ALL that crop's PLANTs → PASS (L889-902)
- Built-in `random` agent NOT reproducible (L997: `random.Random()` unseeded each call)

## 7. Deviations from spec (recorded assumptions)

1. **Python 3.12** used instead of 3.11 (spec said "prefer 3.11, else 3.12"). uv had 3.12.13 cached; 3.11 would need download. 3.12 satisfies `>=3.12` and all tests pass.
2. **litellm pinned to 1.90.0** (not latest 1.93.1). Reason: litellm ≥1.93 introduces a `puccinialin` build backend that downloads the rust toolchain from `static.rust-lang.org` at install time. 1.90.0 is a pure wheel within kaggle-environments' constraint (`>=1.86.1,<1.94.0`).
3. **Commit `dfa0b96` narrative is inaccurate**: spec says it "fixes locked-tile movement in Kaggriculture", but the commit is actually "Fix flaky Quoridor test (#1384)" — a 1-file change to `tests/envs/open_spiel_env/games/quoridor/env_test.py`. The locked-tile movement behavior IS present in 1.32.3, just not from that commit. Recorded in manifest.json.
4. **uv used for dependency management** (user requirement), not raw pip.

## 8. Reliability

- Zero crashes, zero timeouts across all probes and tests.
- `uv sync` fully reproduces the environment from `pyproject.toml`.

## 9. Performance

- Contract test suite: 0.60s total for 10 tests.
- No latency concerns at this phase.

## 10. Known risks

- litellm 1.90.0 pin: if Kaggle runtime uses a different litellm version, LLM-related env features (not used by kaggriculture core) could behave differently. Kaggriculture does not import litellm at runtime for game logic, so risk is low.
- Commit `dfa0b96` mismatch: if the spec author intended a different commit, the "fixed" behavior might differ. Mitigated by testing actual installed behavior.

## 11. Next phase

**Phase 1**: Build submission-safe agent skeleton (`v000_pass`) with safety layer, packaging, and exact-parity testing.
