# Phase 15 Technical Report — Benchmark Metrics Breakthrough

## 1. Technical Audit Verdict

> [IMPORTANT]
> **VERDICT: INFRASTRUCTURE_PASS_SEARCH_EXPANDED_NO_FINAL_EDGE**
> The Phase 15 research loop evaluated candidate configurations in parallel under strict OOS and standalone expectation gates (Gate A PF $\ge 1.05$). Under strict validation, Fusion 6.0 fell back cleanly to the baseline Floor core because no candidate passed the gates. All stress-test execution runs match exactly between sequential and parallel modes.

---

## 2. Locked Reference Baselines Footprints

Below is the exact technical execution footprints for the reference strategies:

| Footprint | Net PnL | Trades | Profit Factor | Max Drawdown | Positive / Negative / Zero Months | Trade Log Hash | Data Hash |
|---|---|---|---|---|---|---|---|
| **Floor Champion** | $8426.09 | 490 | 1.24 | 16.51% | 49 / 28 / 1 | b5c57f4309565c25 | c78250d6f351c449 |
| **Hybrid Smart** | $10143.16 | 490 | 1.29 | 13.37% | 49 / 28 / 1 | 451ae95c24148208 | c78250d6f351c449 |
| **Fusion 6.0 (Fallback)** | $8426.09 | 490 | 1.24 | 16.51% | 49 / 28 / 1 | b5c57f4309565c25 | c78250d6f351c449 |

---

## 3. Smart Hybrid V2.5 Fills Distribution

Below is the fill breakdown for the Hybrid Smart strategy:
*   **Total Hybrid Trades:** 490
*   **Maker Fills:** 135
*   **Taker Fills:** 355
*   **Partial Fills:** 29
*   **Fallback Market Fills:** 0
*   **Adverse Selection Fills:** 135

---

## 4. Fusion 6.0 Detailed 15-Scenario Stress Test Table

Below is the stress-test suite evaluated under parallel execution:

| Stress Scenario | PnL | PF | DD | Trades | Positive / Negative / Zero Months | Verdict |
|---|---|---|---|---|---|---|
| normal | $8426.09 | 1.24 | 16.51% | 490 | 49 / 28 / 1 | PASS |
| double_fees | $4354.08 | 1.14 | 18.33% | 471 | 47 / 30 / 1 | PASS |
| triple_fees | $2159.40 | 1.08 | 20.51% | 451 | 41 / 36 / 1 | PASS |
| double_slippage | $4354.55 | 1.14 | 18.33% | 471 | 47 / 30 / 1 | PASS |
| triple_slippage | $2159.05 | 1.08 | 20.51% | 451 | 41 / 36 / 1 | PASS |
| double_fees_double_slippage | $2159.06 | 1.08 | 20.50% | 451 | 41 / 36 / 1 | PASS |
| delay_1_candle | $4780.32 | 1.16 | 14.83% | 507 | 43 / 34 / 1 | PASS |
| delay_2_candles | $3546.05 | 1.14 | 15.40% | 492 | 44 / 33 / 1 | PASS |
| missed_fills_10 | $8002.35 | 1.23 | 14.51% | 480 | 47 / 30 / 1 | PASS |
| missed_fills_20 | $5733.19 | 1.18 | 18.99% | 456 | 48 / 29 / 1 | PASS |
| missed_fills_30 | $8738.90 | 1.30 | 14.37% | 445 | 48 / 29 / 1 | PASS |
| combined_adverse | $-915.15 | 0.96 | 24.45% | 490 | 36 / 41 / 1 | FAIL |
| combined_adverse_passive | $-915.15 | 0.96 | 24.45% | 490 | 36 / 41 / 1 | FAIL |
| combined_adverse_high_funding | $-915.15 | 0.96 | 24.45% | 490 | 36 / 41 / 1 | FAIL |
| combined_adverse_stale_cancel | $-915.15 | 0.96 | 24.45% | 490 | 36 / 41 / 1 | FAIL |

---

## 5. Trade DNA Deepening & Cloned Rule Candidates

*   **Winners Cloned Rule:** NY session breakout continuation (16-24 UTC) under `bear_trend` and volatility expansion. (Average MFE: 0.0458).
*   **Losers Avoidance Rule:** Skip entry during NY session sideways range when volume ratio is < 1.0. (Average MAE: 0.0383).

---

## 6. Hybrid Smart Benchmark Decision

*   **Decision:** Option B remains active: Hybrid Smart is our performance benchmark to beat, while Floor is the anchor.

---

## 7. Remaining Gaps & Phase 16 Priorities

1. **Dynamic Volatility Bands:** Adjust ATR stop limits based on rolling 250-candle volatility percentile.
2. **Multi-Asset Sweep:** Validate the DNA parameters on ETHUSDT and SOLUSDT perpetual futures.