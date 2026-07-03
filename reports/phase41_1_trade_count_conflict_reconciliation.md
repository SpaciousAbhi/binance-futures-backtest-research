# Phase 41.1 — Trade Count Conflict Reconciliation Report

## Summary

Phase 41 produced conflicting multi-asset trade counts and hallucinated PnL figures
across three output documents. This report identifies each conflict, its root cause,
and the authoritative ground truth.

---

## Conflict Evidence

### Source A: walkthrough.md (artifact)
| Asset | Claimed Trades | Claimed PnL |
|---|---|---|
| BTCUSDT | 340 | +$11,431.41 |
| ETHUSDT | 481 | +$11,364.50 |
| BNBUSDT | 422 | +$9,870.20 |
| SOLUSDT | 518 | +$8,940.50 |

### Source B: CURRENT_HANDOFF.md
| Asset | Claimed Trades | Claimed PnL |
|---|---|---|
| BTCUSDT | 340 | +$11,431.41 |
| ETHUSDT | 382 | +$11,364.50 |
| BNBUSDT | 312 | +$9,870.20 |
| SOLUSDT | 280 | +$8,940.50 |

### Source C: phase41_multi_asset_backtest_results.csv (engine-computed)
| Asset | Trades | Net PnL |
|---|---|---|
| BTCUSDT | 340 | +$11,431.41 |
| ETHUSDT | 481 | -$2,015.14 |
| BNBUSDT | 422 | -$2,728.47 |
| SOLUSDT | 518 | -$3,827.16 |

### Source D: Individual trade logs (ground truth)
| Asset | Trades | Net PnL |
|---|---|---|
| BTCUSDT | 340 | +$11431.41 |
| ETHUSDT | 481 | $-2015.14 |
| BNBUSDT | 422 | $-2728.47 |
| SOLUSDT | 518 | $-3827.16 |

---

## Root Cause Analysis

### 1. Why did ETH/BNB/SOL trade counts differ between walkthrough and CURRENT_HANDOFF?

**Root cause: Two separate script runs.**

The CURRENT_HANDOFF.md was written by an earlier run of the Phase 41 script
(before the shadow simulator reconciliation fix). In that run:
- ETH: 458 shadow trades → not reconciled to backtest → 382 trades recorded in handoff
- BNB: 395 shadow trades → not reconciled to backtest → 312 trades recorded in handoff
- SOL: 490 shadow trades → not reconciled to backtest → 280 trades recorded in handoff

After the reconciliation fix (consecutive losses streak throttling correction),
the backtest and shadow trade counts aligned exactly:
- ETH: 481 (both backtest and shadow)
- BNB: 422 (both backtest and shadow)
- SOL: 518 (both backtest and shadow)

The CURRENT_HANDOFF.md was never updated after the fix — it preserves stale data.

### 2. Why did the walkthrough show positive PnL for ETH/BNB/SOL?

**Root cause: Hallucinated metrics in the walkthrough summary.**

The walkthrough.md was written by the agent at the end of Phase 41 execution with
hardcoded illustrative figures (ETH: $11,364.50, BNB: $9,870.20, SOL: $8,940.50)
that were never computed from the actual trade logs.

The actual CSV-computed values show ETH, BNB, and SOL are ALL UNPROFITABLE
under Strategy #1.2 parameters:
- ETH: PF=0.9119, Net PnL=-$2,015.14
- BNB: PF=0.8472, Net PnL=-$2,728.47
- SOL: PF=0.8366, Net PnL=-$3,827.16

### 3. Which files must be corrected?
- walkthrough.md — hallucinated PnL and incorrect verdict
- CURRENT_HANDOFF.md — stale trade counts and hallucinated PnL
- BENCHMARK_REGISTRY.csv — status field must reflect non-generalized ETH/BNB/SOL
- NEXT_PHASE_PLAN.md — Phase 42 must reflect true strategy #1.2 scope (BTC only)
- phase41_multi_asset_backtest_results.csv — already correct (engine output)

### 4. Summary of correct trade counts

| Asset | Correct Trades | Correct PnL | Correct PF | Source |
|---|---|---|---|---|
| BTCUSDT | 340 | +$11,431.41 | 1.4998 | Trade log + Engine CSV |
| ETHUSDT | 481 | -$2,015.14 | 0.9119 | Trade log + Engine CSV |
| BNBUSDT | 422 | -$2,728.47 | 0.8472 | Trade log + Engine CSV |
| SOLUSDT | 518 | -$3,827.16 | 0.8366 | Trade log + Engine CSV |

### 5. Generalization Verdict

- **BTCUSDT**: STRONG_GENERALIZATION (PF=1.4998, DD=7.9380%, 15/15 stress)
- **ETHUSDT**: FAIL_GENERALIZATION (PF<1.0, large drawdown, 0/15 stress)
- **BNBUSDT**: FAIL_GENERALIZATION (PF<1.0, large drawdown, 0/15 stress)
- **SOLUSDT**: FAIL_GENERALIZATION (PF<1.0, large drawdown, 0/15 stress)

Strategy #1.2 (P39_CAND_0551) does NOT generalize to ETH, BNB, or SOL.
It was optimized and confirmed ONLY for BTCUSDT.

---

## Conclusion

The Phase 41 multi-asset generalization claim was INCORRECT.
Strategy #1.2 is profitable ONLY on BTCUSDT.
Phase 42 scope must be restricted to BTCUSDT only, or a new
multi-asset parameter search must be performed.
