# Phase 38 — Strategy Improvement Map

This document outlines the trade-by-trade improvement map for Strategy #1 (Combined Router v1) and Strategy #1.1 (P37_CAND_0357) based on the deep trade intelligence audit of their 557 and 404 historical trades.

---

## 1. Core Findings from Trade Diagnostics

From the [phase38_trade_cluster_diagnostics.csv](file:///C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest/reports/phase38_trade_cluster_diagnostics.csv) log, we observe the following:

- **Friction Reduction**: Strategy #1.1 reduced high-friction trades from **129** (in Strategy #1) down to **31**. This is a **75.9% reduction in high friction**, directly attributable to the `max_cost_to_risk` guard of `0.12` and the `min_projected_net_R` threshold.
- **Drawdown Contribution**: Average drawdown contribution per losing trade was reduced from **0.4628%** to **0.4586%**, keeping maximum drawdown at **9.37%** (compared to 16.22% for Strategy #1).
- **Losing Cluster Trades**: Dropped from **230** down to **157** due to session and sleeve gating.

---

## 2. Answers to Strategy Improvement Map Questions

### Q1: What types of trades should be preserved?
- **High-Momentum Breakouts**: Bollinger Band Expansion Long and ATR Expansion Short trades during high-volatility environments should be preserved. These represent the core statistical edge of the strategy.
- **New York Session Trades**: Trades executing during New York session hours are the cleanest and should be fully preserved.

### Q2: What types of trades should be reduced?
- **Off-Hours Choppy Trades**: Whipsaws during low-volume hours (especially transition periods between Asian close and London open) must be minimized.
- **Low-Activity Filler Longs**: Low-Activity Filler Long trades are highly unprofitable (cumulative -$812.15 in Strategy #1) and should be suppressed.

### Q3: What types of trades need better TP/SL?
- **Same-Candle Ambiguous Trades**: Exits that occur on the same candle as entry are vulnerable to execution order. They need tighter 5m-candle trigger confirmations to prevent entry on exhaustive wicks.
- **Low R-Multiple Trades**: Setups with projected R-multiple below 0.82 tend to decay into losses and require wider targets or tighter stops to improve the reward-to-risk ratio.

### Q4: What trades caused the largest drawdowns?
- **Consecutive stop-outs** during the consolidation periods of mid-2024 and early-2025. These are characterized by rapid trend-reversal sweeps that hit Bollinger limits but immediately reverse.

### Q5: What trades caused worst months?
- Negative months like April 2026 (-$718.58) and May 2025 (-$678.18) were caused by a high concentration of low-activity filler long trades firing during bear market expansions. Suppressing these long signals in bearish regimes directly repairs these months.

### Q6: Which sleeves deserve more weight?
- **BB Expansion Long** (net PnL +$4,900.85) and **ATR Expansion Short** (net PnL +$1,583.78) are the strongest sleeves.

### Q7: Which sleeves deserve less weight?
- **Low-Activity Filler Long** deserves zero weight (full suppression).
- **Funding Reversal Short** (net PnL +$927.92 across 110 trades, mean PnL $8.44) has a very low average trade expectancy and should be constrained.

### Q8: Which sessions are strongest?
- **New York Session** is the strongest session, generating **$9,755.21** of the net PnL in Strategy #1.

### Q9: Which sessions are weakest?
- **London Session** ($287.53) and **Off-Hours** ($1,162.46) are the weakest, showing high trade counts but very low net returns.

### Q10: Which live-known filters could improve results?
- **Max Cost-to-Risk Cap**: Restricting trades when transaction fees and slippage exceed 12% of the stop distance.
- **Min Projected Net R**: Filtering trades where the expected R-multiple minus friction is below 0.82.
- **ADX Filter**: Requiring ADX > 12 to ensure the entry occurs in a trending market.

### Q11: Which filters would hurt trade count too much?
- Fully suppressing the **Off-Hours** session would remove 203 trades, which severely degrades the statistical sample size and hurts overall returns.

### Q12: Which rules might improve stress?
- Executing entry signals using **limit orders on 5m wick pullbacks** instead of market orders. This would bypass taker fees (0.05%) in favor of maker fees (0.02%) and positive slippage.

### Q13: Which rules might improve monthly consistency?
- Implementing an **MTD drawdown circuit breaker** that halts the strategy if closed monthly losses exceed 3.0% of capital, resetting on the 1st of the next month.

### Q14: Which rules might improve PF?
- Requiring a minimum ATR percentile (e.g. `min_atr_pct >= 0.3`) to prevent breakout trades in extremely narrow, compressed ranges that lack follow-through.

### Q15: Which rules might reduce DD?
- Reducing position sizes dynamically when the strategy enters a drawdown phase (e.g., halving the risk-per-trade from 1% to 0.5% after 2 consecutive losses).
