# Phase 12.1 Audit Report — Correction and Fusion Failure Forensic Analysis

**Completed:** 2026-06-30 20:45:00 UTC  
**Verdict:** **INFRASTRUCTURE_PROGRESS_READY_FOR_PHASE12_2**

---

## 1. Technical Audit Verdict

> [!IMPORTANT]
> **VERDICT: INFRASTRUCTURE_PROGRESS_READY_FOR_PHASE12_2**
> The infrastructure, including the upgraded backtest engine and limit order tracking, is fully functional (PASS). The system is now ready for Phase 12.2 filtered orthogonal alpha research. Strategy discovery for raw candidates failed under Fusion V2, but the pipeline has been corrected, verified, and reconciled for the next phase.

---

## 2. Reconcile Quality Floor Drift

We resolved the trade count drift between the Phase 11.1 locked floor and the previous Phase 12 report:

*   **Phase 11.1 Locked Floor:** Net PnL of **$8,426.09**, **490 trades**, Profit Factor of **1.24**, Max Drawdown of **16.51%**, Monthly count: **49 / 28 / 1**.
*   **Previous Phase 12 Report:** Claimed Net PnL of **$8,774.57**, **547 trades**, Profit Factor of **1.22**, Max Drawdown of **15.18%**.
*   **Drift Explanation:** 
    *   **Root Cause:** The previous Phase 12 runner was executed without compatibly routing the `"activity"` sub-portfolio in the upgraded `FusionOfFusionsStrategy.get_signal` rules. Since `"activity"` was unrecognized, its trades were dropped or bypassed, changing position overlaps and cooldown states.
    *   **Resolution:** After restoring the `"activity"` compatibility gate in `portfolio.py`, the reproduced floor champion trade log matches the Phase 11.1 locked floor **exactly** (490 trades, $8,426.09 PnL).
    *   **hashes:**
        *   **Data File:** `data/processed/BTCUSDT_1h_processed.csv` (Row Count: 56,881) | Hash: `353b5577fbe863330549a4dcd88a28567237cb484310676caff1475267d23329`
        *   **Engine Hash:** `437e3b53be98e36e` (with exit slippage applied correctly)
        *   **Config Hash:** `7133cc0be2e8111e` (risk settings matching Phase 11.1 exactly)

---

## 3. Hybrid Smart Execution Validation

We ran a full validation of the Hybrid Smart execution model on the floor strategy:

### Fill Quality Statistics
*   **Total Trades:** 490
*   **Maker Fills (Passive Limit):** 8 (1.6%)
*   **Taker Fills (Market):** 482 (98.4%)
    *   *Of which Fallback-to-Market:* 0
*   **Partial Fills:** 4
*   **Adverse Selection Fills (Exceeded limit price):** 8
*   **Queue Touch Fills (Touched exactly):** 0
*   **Net PnL:** $8,449.93 (+$23.84 improvement over taker market)
*   **Profit Factor:** 1.24
*   **Max Drawdown:** 16.43%

### Yearly Performance
*   **2020:** PnL = $801.66 | 73 trades
*   **2021:** PnL = $2,395.20 | 131 trades
*   **2022:** PnL = $2,938.74 | 72 trades
*   **2023:** PnL = $2,433.27 | 50 trades
*   **2024:** PnL = -$1,806.07 | 76 trades
*   **2025:** PnL = $48.02 | 55 trades
*   **2026:** PnL = $1,639.12 | 33 trades

### Stress Audits
*   **Normal:** PnL = $8,250.58 | DD = 16.41% | **PASS**
*   **Double Fees:** PnL = $4,522.67 | DD = 18.35% | **PASS**
*   **Double Slippage:** PnL = $4,556.99 | DD = 18.32% | **PASS**
*   **Delay 1 Candle:** PnL = $4,694.80 | DD = 14.89% | **PASS**
*   **Missed Fills 10%:** PnL = $7,367.82 | DD = 16.78% | **PASS**
*   **Combined Adverse (Fees x2 + Slip x2 + Delay 1):** PnL = -$565.76 | DD = 24.25% | **FAIL**

> [!NOTE]
> **Why are Maker fills so low?**
> The Hybrid model uses `order_is_limit = (atr_pct_val < 0.03)`. In the technical indicator library, `atr_pct` is the **ATR Percentile Rank** (0.0 to 1.0). A threshold of `0.03` means limit orders are only placed when volatility is in the lowest 3% percentile. Breakouts, by definition, occur during high volatility, so almost all trades execute as market orders.

---

## 4. Fusion V2 Failure Forensics

### Key Findings
1.  **Toxic Standalone Expectancy:** All 19 new orthogonal candidates had standalone Profit Factors < 1.0 on BTCUSDT. Fusing them using a simple union allowed toxic strategies to take trades continuously.
2.  **Damaged Months:** Significant drawdowns occurred in high-trend months (such as late 2020 and 2021) where counter-trend mean reversion got overrun by trend expansions.
3.  **Toxicity Throttle Limit:** The streak-based toxicity gates successfully halved risk sizes but did not halt trading soon enough to prevent the cumulative decay from 847 trades.
4.  **Correlation vs. Quality:** Uncorrelated negative-expectancy strategies do not hedge each other; they simply diversify and guarantee losses.

### Lock the Fusion Rule
> [!IMPORTANT]
> **No candidate with standalone PF < 1.05 may enter final fusion unless it is explicitly proven to improve negative months without damaging total PF.**

---

## 5. Summary Dashboard

*   **Infrastructure progress:** PASS
*   **Orthogonal alpha bank:** FAIL
*   **Fusion V2:** FAIL
*   **Hybrid execution:** PROMISING_RESEARCH
*   **Final strategy:** NOT FOUND
*   **Live deployment readiness:** NO

---

## 6. Phase 12.2 Direction
1.  **Filtered Mean Reversion:** Restrict all mean reversion templates with strict trend filters (e.g. EMA 200, MACD, or ADX trend direction).
2.  **Regime Gating:** Restrict liquidity sweeps to low-volatility range regimes only.
3.  **Trend Pullbacks:** Focus on trend-confirmed pullbacks rather than raw breakouts.
4.  **Tighter Gating:** Enforce the new standalone PF >= 1.05 gate before candidates are allowed into the fusion portfolio.
