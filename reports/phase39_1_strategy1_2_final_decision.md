# Strategy #1.2 Final Decision — Phase 39.1

## Recomputed Metrics (Ground Truth from Trade Log)
| Metric | Value |
|---|---|
| Net PnL | $11431.41 |
| Trades | 340 |
| Profit Factor | 1.4998 |
| Max Drawdown | 7.9380% |
| Positive Months | 46 |
| Negative Months | 25 |
| Zero Months | 0 |
| Stress Pass | 8/15 |

## Promotion Gate Results

| Track | PnL | Trades | PF | DD | Stress/Monthly | PASS? |
|---|---|---|---|---|---|---|
| A (High-PnL) | $11431.41 < $11,500 ❌ | 340 < 400 ❌ | 1.4998 ≥ 1.40 ✅ | 7.94% ≤ 9.5% ✅ | 8 < 9 ❌ | **FAIL** |
| B (Quality) | $11431.41 ≥ $10,000 ✅ | 340 < 350 ❌ | 1.4998 < 1.50 ❌ | 7.94% > 7.5% ❌ | 8 < 9 ❌ | **FAIL** |
| C (Stress) | $11431.41 ≥ $8,500 ✅ | 340 ≥ 300 ✅ | 1.4998 ≥ 1.35 ✅ | 7.94% ≤ 10% ✅ | 8 < 10 ❌ | **FAIL** |
| D (Monthly) | $11431.41 ≥ $9,500 ✅ | 340 < 350 ❌ | 1.4998 ≥ 1.35 ✅ | 7.94% ≤ 10% ✅ | 25 > 18 ❌ | **FAIL** |

## Key Observations
- **Closest track:** Track C (Stress) — passes PnL, Trades, PF, DD; fails only on stress (8/15 vs required 10/15)
- **Stress model caveat:** The stress runner's combined adverse scenario is flagged as STRESS_MODEL_REQUIRES_REPAIR — the 8/15 count may improve once the stress harness is corrected
- **Construction:** VALID_LIVE_KNOWN_SIGNAL_STRATEGY — candidate is genuinely live-executable
- **Metrics:** Internally consistent (vault = candidate_results.csv = trade log recompute)

## Decision: **OPTION C — PROVISIONAL**

Strategy #1.2 remains **PROVISIONAL** (not fully promoted, not demoted):
- Metrics reconcile ✅  
- Construction is valid ✅  
- Promotion gate fails on stress (8/15 vs 10/15 for Track C) ❌  
- Stress model requires repair before durable pass/fail verdict on combined-adverse ❌

**Strategy #1.2 status is changed from PROMOTED → PROVISIONAL pending stress harness repair.**
