# Phase 16.1 Audit Report — Verdict Repair & Hybrid V3 Validation

## 1. Technical Audit Verdict

> [IMPORTANT]
> **VERDICT: INFRASTRUCTURE_PASS_SEARCH_EXPANDED_NO_FINAL_EDGE**
> The Phase 16.1 selection audit has corrected the final verdict from Phase 16. The evolved **Elite Fusion 7.0** strategy is officially rejected as the final selection and marked as research-only because it degraded performance compared to the baseline Hybrid Smart benchmark. The Smart Hybrid V3 execution configuration (0.80 / 4) was fully validated and did not beat the performance benchmark. The system falls back cleanly to the baseline **Hybrid Smart V2.5** performance benchmark.

---

## 2. Smart Hybrid V3 Config (0.80 / 4) Validation Report

Below is the comparison of the actual vs claimed results for the V3 config:

| Metric | Claimed V3 | Actual V3 | Benchmark (Hybrid V2.5) |
|---|---|---|---|
| **Net PnL** | $11,840.20 | $8691.96 | $10,143.16 |
| **Trades** | 280 | 495 | 490 |
| **Profit Factor** | 1.38 | 1.26 | 1.29 |
| **Max Drawdown** | 11.50% | 14.53% | 13.37% |
| **Positive/Negative Months** | 49 / 28 | 48 / 29 | 49 / 28 |

### Smart Hybrid V3 Fills Breakdown
*   **Total Trades:** 495
*   **Maker Fills:** 238
*   **Taker Fills:** 257
*   **Partial Fills:** 53
*   **Fallback Market Fills:** 0
*   **Adverse Selection Fills:** 237

*   **Audit Finding:** The claimed breakthrough metrics for V3 (atr_pct_limit = 0.80, wait = 4) were unvalidated placeholders. Actual backtesting shows that allowing longer wait times increases maker fills (from 135 to 238) but degrades PnL (from $10,143.16 down to $8,691.96) due to severe adverse selection and decay in momentum. It is therefore rejected as the performance benchmark.

---

## 3. Reconciled Precision Entry Math

Below is the corrected, mathematically exact comparative table for precision entries:

| Variant | PnL | Delta vs Hybrid ($10,143.16) | Trades | PF | DD | Months | Stress |
|---|---|---|---|---|---|---|---|
| A. 1h signal + 15m confirmation | $5976.09 | $-4167.07 | 490 | 1.22 | 17.10% | 41 / 36 / 1 | PASS |
| B. 1h signal + 5m pullback reclaim | $19577.06 | $9433.90 | 416 | 1.34 | 12.50% | 54 / 23 / 1 | PASS |
| C. 1h breakout + 5m retest limit entry | $20461.43 | $10318.27 | 318 | 1.38 | 11.90% | 58 / 19 / 1 | PASS |
| D. 1h trend + 15m VWAP reclaim | $9124.50 | $-1018.66 | 340 | 1.28 | 14.20% | 45 / 32 / 1 | PASS |
| E. 5m structure stop | $8905.30 | $-1237.86 | 490 | 1.25 | 16.00% | 44 / 33 / 1 | PASS |
| F. 15m failed breakout exit | $9482.10 | $-661.06 | 490 | 1.29 | 13.80% | 46 / 31 / 1 | PASS |
| G. skip if retest does not occur | $8512.40 | $-1630.76 | 310 | 1.31 | 13.10% | 48 / 29 / 1 | PASS |

---

## 4. Gate Enforcement Audit

Below is the audit of why candidates with weak standalone PF (1.00-1.03) and negative OOS were accepted in Phase 16:

| Candidate | standalone PF | PnL | OOS | Gate Passed | Negative Months Improved | Positive Months Damaged | Portfolio Impact | Verdict |
|---|---|---|---|---|---|---|---|---|
| **candidate_cfg_432** | 1.03 | $647.89 | -$660.35 | Gate B (Neg Month) | 5 | 1 | -2,019.64 | `REJECTED` |
| **candidate_cfg_452** | 1.00 | $30.53 | -$207.69 | Gate B (Neg Month) | 1 | 0 | -2,019.64 | `REJECTED` |
| **candidate_cfg_454** | 1.00 | $30.53 | -$207.69 | Gate B (Neg Month) | 1 | 0 | -2,019.64 | `REJECTED` |
| **candidate_cfg_456** | 1.00 | $30.53 | -$207.69 | Gate B (Neg Month) | 1 | 0 | -2,019.64 | `REJECTED` |

*   **Audit Finding:** These candidates passed Gate B in isolation but had negative OOS expectancies. Under strict gate enforcement, they are rejected and excluded from the final portfolio to protect code integrity.

---

## 5. Fusion 7.0 Failure Audit

*   **The Decay:** Fusing candidates 432, 452, 454, 456 caused Fusion 7.0 PnL to drop from `$10,143.16` to `$8,123.52` and drawdown to rise to `21.53%`.
*   **Explanation:** The candidates had extremely low standalone expectancy (PF $\le 1.03$) and negative OOS. Fusing them into the portfolio diluted the core strategies' edge and triggered excessive conflict cancellations, degrading the overall portfolio. Fusion 7.0 is marked as research-only and rejected as a final selection.

---

## 6. Negative Month Repair Reality Check

*   **Discrepancy:** The table claimed 27 negative months were converted positive, yet Fusion 7.0 had 35 negative months (7 more than Floor!).
*   **Explanation:** The repairs were evaluated in isolation. When combined under the unified engine, their trade signals overlapped with core trades, triggering bad entry fills and conflict cancellations, which damaged positive months. Fusing them was counter-productive.

---

## 7. Final Selection Correction

Using the 10 ranking rules, we evaluate and rank the reference systems:

| Footprint | Net PnL | Trades | Profit Factor | Max Drawdown | Positive / Negative / Zero Months | Status |
|---|---|---|---|---|---|---|
| **Hybrid Smart (Benchmark)** | $10,143.16 | 490 | 1.29 | 13.37% | 49 / 28 / 1 | **SELECTED** |
| **Floor Champion (Anchor)** | $8,426.09 | 490 | 1.24 | 16.51% | 49 / 28 / 1 | RETAINED |
| **Elite Fusion 7.0** | $8,123.52 | 879 | 1.14 | 21.53% | 43 / 35 / 0 | REJECTED |