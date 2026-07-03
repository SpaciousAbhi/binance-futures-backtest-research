# Phase 40 — Stress Harness Repair & Strategy #1.2 Final Decision Report

**Phase:** 40  
**Date:** 2026-07-03  
**Verdict:** `PHASE40_PASS_STRATEGY1_2_CONFIRMED_AND_LOCKED`

---

## 1. The Bug — What Was Wrong

The Phase 34 stress harness (`stress_trade_log`) computed fee and slippage adjustments as:

```python
# BUGGY — Phase 34 through Phase 39 (all historical stress results)
fee_adj = (fee_mult - 1.0) * TAKER_FEE * 2.0 * entry_price     # MISSING * size
slip_adj = (slip_mult - 1.0) * BASE_SLIPPAGE * entry_price      # MISSING * size
```

**The fix:**
```python
# CORRECT — Phase 40 corrected harness
fee_adj = (fee_mult - 1.0) * TAKER_FEE * 2.0 * entry_price * size   # ✅ notional
slip_adj = (slip_mult - 1.0) * BASE_SLIPPAGE * entry_price * size    # ✅ notional
```

**Quantified impact on Strategy #1.2 (340 trades, avg size=0.1862 BTC, avg price=$47299):**

| Metric | Old Harness | Corrected Harness |
|---|---|---|
| Double-fee extra penalty | $16081.56 | $2137.51 |
| Overestimation factor | 7.52× too large | 1.0× (correct) |

The old harness applied fees as if every trade had exactly 1 BTC of position size,
regardless of the actual trade size. For small-position-size candidates, this created 
a wildly exaggerated combined adverse result.

---

## 2. Stress Results — Before vs After

### Harness Comparison (All 3 Strategies)

| Strategy | Old Pass/15 | New Pass/15 | Old Combined Adverse | New Combined Adverse |
|---|---|---|---|---|
| Strategy #1 | 7/15 | 15/15 | -$39,138.38 | $811.53 |
| Strategy #1.1 | 8/15 | 15/15 | -$33,384.48 | $4767.16 |
| Strategy #1.2 | 8/15 | 15/15 | -$25,369.59 | $4323.12 |

### Strategy #1.2 Detailed Stress Scenarios (Corrected Harness)

| Scenario | Trades | Net PnL | PF | Max DD | Verdict |
|---|---|---|---|---|---|
| normal | 340 | $11431.41 | 1.4998 | 7.94% | ✅ PASS |
| double fees | 340 | $9293.90 | 1.3907 | 9.40% | ✅ PASS |
| triple fees | 340 | $7156.39 | 1.2897 | 11.65% | ✅ PASS |
| double slippage | 340 | $10362.65 | 1.4442 | 8.60% | ✅ PASS |
| triple slippage | 340 | $9293.90 | 1.3907 | 9.40% | ✅ PASS |
| double fees + double slippage | 340 | $8225.15 | 1.3392 | 10.26% | ✅ PASS |
| delay 1 candle | 340 | $10362.65 | 1.4442 | 8.60% | ✅ PASS |
| delay 2 candles | 340 | $9293.90 | 1.3907 | 9.40% | ✅ PASS |
| missed fills 10% | 306 | $8144.39 | 1.3770 | 10.88% | ✅ PASS |
| missed fills 20% | 272 | $7264.04 | 1.3789 | 11.07% | ✅ PASS |
| missed fills 30% | 238 | $6786.22 | 1.4091 | 9.32% | ✅ PASS |
| stale cancel | 323 | $11877.11 | 1.5581 | 7.73% | ✅ PASS |
| partial fill | 340 | $10574.05 | 1.4998 | 7.60% | ✅ PASS |
| high funding | 340 | $9922.14 | 1.4228 | 9.12% | ✅ PASS |
| combined adverse | 306 | $4323.12 | 1.1853 | 14.72% | ✅ PASS |

---

## 3. Promotion Gate Re-Audit — Strategy #1.2

| Track | PnL | Trades | PF | DD | Stress/Monthly | PASS? |
|---|---|---|---|---|---|---|
| A (High-PnL) | $11431.41 ❌ | 340 ❌ | 1.4998 ✅ | 7.94% ✅ | 15/15 ✅ | **❌** |
| B (Quality) | $11431.41 ✅ | 340 ❌ | 1.4998 ❌ | 7.94% ❌ | 15/15 ✅ | **❌** |
| C (Stress) | $11431.41 ✅ | 340 ✅ | 1.4998 ✅ | 7.94% ✅ | 15/15 ✅ | **✅** |
| D (Monthly) | $11431.41 ✅ | 340 ❌ | 1.4998 ✅ | 7.94% ✅ | 15/15 ✅ | **❌** |

Verified metrics (from trade log):
- PnL: $11431.41 | Trades: 340 | PF: 1.4998
- DD: 7.9380% | Neg months: 25 | Zero months: 0

---

## 4. Final Decision

**Strategy #1.2 is CONFIRMED PROMOTED.**

Passing tracks: ['C']

Strategy #1.2 (P39_CAND_0551) meets all promotion gate requirements under the corrected stress harness. 
It replaces Strategy #1.1 as the current research champion and is the best live-known executable 
candidate produced by this project to date.

**Status updated to: `CONFIRMED_PROMOTED` (NOT_REAL_CAPITAL_READY)**

---

## 5. Historical Stress Truth (All Strategies — Corrected Harness)

### Strategy #1 (Protected Baseline)
| Scenario | Trades | Net PnL | PF | Max DD | Verdict |
|---|---|---|---|---|---|
| normal | 557 | $11205.20 | 1.2522 | 16.22% | ✅ PASS |
| double fees | 557 | $6983.71 | 1.1505 | 22.23% | ✅ PASS |
| triple fees | 557 | $2762.23 | 1.0571 | 32.12% | ✅ PASS |
| double slippage | 557 | $9094.45 | 1.2002 | 19.05% | ✅ PASS |
| triple slippage | 557 | $6983.71 | 1.1505 | 22.23% | ✅ PASS |
| double fees + double slippage | 557 | $4872.97 | 1.1028 | 25.85% | ✅ PASS |
| delay 1 candle | 557 | $9094.45 | 1.2002 | 19.05% | ✅ PASS |
| delay 2 candles | 557 | $6983.71 | 1.1505 | 22.23% | ✅ PASS |
| missed fills 10% | 502 | $8383.69 | 1.2045 | 17.83% | ✅ PASS |
| missed fills 20% | 446 | $8028.78 | 1.2211 | 18.18% | ✅ PASS |
| missed fills 30% | 390 | $5141.31 | 1.1582 | 23.93% | ✅ PASS |
| stale cancel | 530 | $9384.22 | 1.2189 | 18.10% | ✅ PASS |
| partial fill | 557 | $10364.81 | 1.2522 | 15.63% | ✅ PASS |
| high funding | 557 | $8585.49 | 1.1887 | 20.03% | ✅ PASS |
| combined adverse | 502 | $811.53 | 1.0182 | 38.60% | ✅ PASS |

### Strategy #1.1 (Vaulted Champion)
| Scenario | Trades | Net PnL | PF | Max DD | Verdict |
|---|---|---|---|---|---|
| normal | 404 | $11231.08 | 1.3862 | 9.37% | ✅ PASS |
| double fees | 404 | $8819.79 | 1.2925 | 11.37% | ✅ PASS |
| triple fees | 404 | $6408.49 | 1.2052 | 13.76% | ✅ PASS |
| double slippage | 404 | $10025.43 | 1.3385 | 10.33% | ✅ PASS |
| triple slippage | 404 | $8819.79 | 1.2925 | 11.37% | ✅ PASS |
| double fees + double slippage | 404 | $7614.14 | 1.2481 | 12.51% | ✅ PASS |
| delay 1 candle | 404 | $10025.43 | 1.3385 | 10.33% | ✅ PASS |
| delay 2 candles | 404 | $8819.79 | 1.2925 | 11.37% | ✅ PASS |
| missed fills 10% | 364 | $9130.61 | 1.3434 | 12.11% | ✅ PASS |
| missed fills 20% | 324 | $9535.03 | 1.4109 | 9.10% | ✅ PASS |
| missed fills 30% | 283 | $7619.39 | 1.3711 | 11.54% | ✅ PASS |
| stale cancel | 384 | $9054.36 | 1.3222 | 13.00% | ✅ PASS |
| partial fill | 404 | $10388.75 | 1.3862 | 9.00% | ✅ PASS |
| high funding | 404 | $9171.21 | 1.3069 | 10.89% | ✅ PASS |
| combined adverse | 364 | $4767.16 | 1.1668 | 16.72% | ✅ PASS |

---

## 6. Corrected Stress Harness — Code

The corrected `stress_trade_log_FIXED` function is implemented in 
`scripts/phase40_stress_harness_repair.py`. The original `phase34_strategy_vault_and_candidate_discovery.py` 
is preserved unchanged (historical record). Future phases must use the Phase 40 corrected harness.

---

## 7. Files Generated

| File | Purpose |
|---|---|
| phase40_sync_and_safety_audit.csv | Git sync verification |
| phase40_bug_documentation.csv | Quantified bug impact |
| phase40_stress_comparison_matrix.csv | All scenarios for all strategies, both harnesses |
| phase40_strategy_summaries.csv | High-level strategy comparison |
| phase40_promotion_gate_audit.csv | Track A/B/C/D for all strategies |
| phase40_harness_before_after.csv | Before/after pass counts |
| phase40_strategy_1_fixed_stress.csv | Strategy #1 corrected stress detail |
| phase40_strategy_1_1_fixed_stress.csv | Strategy #1.1 corrected stress detail |
| phase40_strategy_1_2_fixed_stress.csv | Strategy #1.2 corrected stress detail |
| phase40_strategy1_2_final_decision.csv | Final decision record |
| phase40_audit_manifest.json | Phase 40 manifest |
| phase40_stress_harness_repair_and_strategy1_2_final_decision_report.md | This report |
