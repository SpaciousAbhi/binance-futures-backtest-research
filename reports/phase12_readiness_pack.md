# Phase 12 Readiness Pack — Binance Futures Strategy Research

This readiness pack outlines the strategy's quality floor, key performance gaps, and the Phase 12 plan for building orthogonal, live-ready trading modules.

## 1. Present Quality Floor (Slippage-Repaired)

Following the honest slippage repair in Phase 11.1 (where exit slippage is now correctly applied to all Stop-Loss and Take-Profit exits), the performance metrics of our champion systems have stabilized at a realistic level:

### Phase 10.1 original champion (Phase10_1_FoF_4Subportfolio)
*   **Net PnL:** $8,135.53 (Reduced from $10,535.14 due to exit slippage drag)
*   **Total Trades:** 490
*   **Profit Factor:** 1.23
*   **Max Drawdown:** 18.73%
*   **Monthly Count (+ / - / 0):** 47 / 31 / 1
*   **Trade Log Hash:** `4e2cda96366cc6df`

### Phase 11 reproduced champion (Phase11_FoF_2Subportfolio)
*   **Net PnL:** $7,306.71 (Reduced from $9,400.70 due to exit slippage drag)
*   **Total Trades:** 449
*   **Profit Factor:** 1.24
*   **Max Drawdown:** 14.42%
*   **Monthly Count (+ / - / 0):** 47 / 30 / 1
*   **Trade Log Hash:** `6b9d16d752656ada`

> [!IMPORTANT]
> The PnL reduction is a direct consequence of realistic transaction costs. This is the correct, honest baseline from which Phase 12 will build.

---

## 2. Key Gaps & Failure Modes

Forensic analysis of the backtest results under the stress engine has revealed several critical areas of improvement:

1.  **High Slippage Sensitivity & Stress Failure (Cost Erosion):**
    *   Slippage accounts for a significant portion of gross profit erosion.
    *   In the double/triple slippage stress tests, net PnL declines significantly, proving that the breakout strategy's reliance on taker/market orders is a major vulnerability.
    *   **Stress Failure:** Both champion configurations fail the combined adverse stress scenario (fees + slippage + execution delay combined), yielding net losses of -$915.15 and -$723.25, respectively. This shows the system is not yet robust enough for final live deployment.
2.  **Bollinger Parameter Sensitivity:**
    *   Varying the Bollinger Band width threshold (`bb_width_thresh`) from 0.04 to 0.08 results in significant swings in trade counts and PnL.
    *   This indicates that the exact threshold of 0.06 is highly calibrated to historical data, suggesting potential overfitting.
3.  **Low-Activity Sideways Regimes (Zero-Trade Months):**
    *   Months like 2023-07 continue to produce zero trades or very small net PnL, indicating that our trend breakout models are inactive during low-volatility periods.
    *   To achieve the negative-month breakthrough, we need orthogonal mean-reversion/range strategies that operate when trend systems are idle.

---

## 3. Orthogonal Strategy Hypotheses (Phase 12-Ready)

To solve these gaps, the ResearchIdeaEngine has generated 11 orthogonal strategy hypotheses that do not depend on Bollinger Band breakout setups:

| ID | Name | Category | Priority | Complexity | Overfit Risk | Live Compat | Status |
|---|---|---|---|---|---|---|---|
| ORTH_001 | Session Range Mean Reversion | Mean Reversion | 9.0 | 3.5 | 2.5 | 4.5 | **DEFERRED_TO_PHASE_12** |
| ORTH_002 | Session Range Failure Reversal | Reversal | 8.5 | 3.8 | 3.0 | 4.2 | **DEFERRED_TO_PHASE_12** |
| ORTH_003 | Funding Exhaustion Reversal | Reversal | 8.0 | 3.0 | 2.0 | 4.8 | **DEFERRED_TO_PHASE_12** |
| ORTH_004 | Low-Volatility Range Scalping | Mean Reversion | 7.5 | 4.0 | 3.5 | 3.5 | **DEFERRED_TO_PHASE_12** |
| ORTH_005 | Liquidity Sweep with Reclaim | Reversal | 9.2 | 3.2 | 2.2 | 4.6 | **DEFERRED_TO_PHASE_12** |
| ORTH_006 | Order-Flow Proxy Volume Impulse | Momentum | 7.0 | 2.5 | 1.5 | 4.9 | **DEFERRED_TO_PHASE_12** |
| ORTH_007 | VWAP Anchored Reclaim | Trend Following | 8.7 | 3.0 | 2.0 | 4.7 | **DEFERRED_TO_PHASE_12** |
| ORTH_008 | Trend Pullback Continuation | Trend Following | 9.5 | 2.8 | 2.2 | 4.8 | **DEFERRED_TO_PHASE_12** |
| ORTH_009 | Volatility Exhaustion Reversal | Reversal | 7.8 | 3.4 | 2.8 | 4.1 | **DEFERRED_TO_PHASE_12** |
| ORTH_010 | Calendar-Session Volatility Behavior | Time Gating | 6.5 | 2.0 | 1.5 | 5.0 | **DEFERRED_TO_PHASE_12** |
| ORTH_011 | 5m Microstructure Trigger | Execution | 8.9 | 4.2 | 2.8 | 4.0 | **DEFERRED_TO_PHASE_12** |

---

## 4. Phase 12 Search Plan

The search plan for Phase 12 is structured as follows:

1.  **Phase 12.1: Orthogonal Strategy Implementation**
    *   Build and backtest the new templates (specifically targeting `Session Range Mean Reversion`, `Liquidity Sweep`, and `Trend Pullback Continuation`).
    *   Verify that these strategies have a low trade-overlap correlation (< 15%) with the Bollinger breakout systems.
2.  **Phase 12.2: Limit Order & Passive Execution Simulation**
    *   Modify `BacktestEngine` to support passive limit order entries and exits.
    *   passive execution will eliminate taker fees (earning maker rebates or paying lower maker fees) and eliminate exit slippage, directly resolving the cost erosion gap.
3.  **Phase 12.3: Multi-Strategy Portfolio Optimization**
    *   Use walk-forward optimization to find the best risk-allocation weights for the combined trend-following and mean-reversion portfolios.
    *   Target zero negative months across the entire 6.5-year backtest duration.
