# Phase 3R.6: Causal Factorial Ablation Report

Evaluated on 8 'screen' seeds × both seats (16 matches per candidate) against `wheat_only`.

## Factorial Matrix

| Candidate | Managed Tiles | Hiring Strategy | Avg Final $ (Agent) | Avg Margin ($) | Avg Outcome | Wilson LB | Weeds | Movement % |
|---|---|---|---|---|---|---|---|---|
| **A** | 6 (block) | 0 hands (farmer only) | $19278 (min) | $15635 | 1.000 | 0.806 | 2.6 | 47.6% |
| **B** | 16 (quadrant) | 0 hands (farmer only) | $18754 (min) | $16345 | 1.000 | 0.806 | 1.2 | 56.9% |
| **C** | 6 (block) | 6 hands (blind fixed) | $19535 (min) | $15934 | 1.000 | 0.806 | 2.8 | 49.1% |
| **D** | 16 (quadrant) | 6 hands (blind fixed) | $40509 (min) | $36985 | 1.000 | 0.806 | 1.3 | 65.1% |
| **E** | 16 (quadrant) | sequential marginal | $40509 (min) | $36985 | 1.000 | 0.806 | 1.3 | 65.1% |

## Causal Interpretation

- **Tile Scaling Effect (0 hands, B - A)**: $+710 margin.
- **Hand Hiring Effect (6 tiles, C - A)**: $+299 margin.
- **Synergistic Interactive Effect (D - [A+T+H])**: $+20342 margin.
- **Marginal-Hiring vs Blind-Hiring Effect (E - D)**: $+0 margin.