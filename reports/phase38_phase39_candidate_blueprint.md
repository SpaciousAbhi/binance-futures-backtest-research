# Phase 39 Candidate Discovery Blueprint

This document defines the strategy candidates, parameter grids, search space, and execution gates for **Phase 39 Strategy Recovery & Hardening**.

---

## 1. Top 20 Candidate Families to Test

Based on the [phase38_idea_engine_library.csv](file:///C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest/reports/phase38_idea_engine_library.csv) and the trade audit, we will test the following 20 families in Phase 39:

1. **`NY_Breakout_ADX20`**: Bollinger expansion breakouts strictly in New York hours with ADX > 20.
2. **`OffHours_MeanReversion_R1.5`**: Bollinger reversion during off-hours requiring a minimum projected R-multiple of 1.5.
3. **`LowActivity_Suppressed_Long`**: Breakout strategy with low-activity long filler trades entirely deactivated.
4. **`CostToRisk_Capped_0.10`**: Cap trades where transaction cost/slippage exceeds 10% of stop distance.
5. **`ATR_Percentile_Squeeze_0.35`**: Bollinger expansion breakouts only when 20-day ATR is in the lowest 35% percentile.
6. **`VWAP_Reclaim_NY_Only`**: Intraday mean reversion targeting VWAP band reclaims exclusively during NY session.
7. **`Funding_Filtered_Shorts`**: Suppression of funding reversal shorts if funding rate is below +0.02%.
8. **`Leverage_Drawdown_Throttle`**: Half risk-per-trade when capital drawdown exceeds 5.0%.
9. **`RSI_Strict_OB75`**: Breakout strategy requiring RSI < 75 for longs to avoid buying exhaustive tops.
10. **`Wick_Ratio_Rejection`**: Reversion entry only when candle lower/upper wick represents 50%+ of total range.
11. **`Multi_Asset_Fusion_BNB`**: Validation and parameter fitting for BNBUSDT.
12. **`Multi_Asset_Fusion_ETH`**: Validation and parameter fitting for ETHUSDT.
13. **`EMA50_Pullback_Trend`**: Pullback entries near 1h EMA 50 when ADX shows strong trend slope.
14. **`Double_ATR_TakeProfit`**: Breakout candidate with fixed take-profit target at 2.5x ATR.
15. **`Tighter_ATR_StopLoss`**: Bollinger breakout with tight stop-loss at 1.4x ATR.
16. **`MTD_Drawdown_CircuitBreaker`**: Terminate all trading for the month if closed monthly losses exceed 3.0%.
17. **`SameCandle_Wick_Delay`**: Entry confirmation requires a 5m pullback to prevent same-candle slippage stop-out.
18. **`ADX_Slope_Trend_Confirmation`**: Breakout entry only when ADX is rising over 3 consecutive 1h bars.
19. **`Volatility_Expansion_Weighted`**: Position sizing proportional to Bollinger Band width expansion rate.
20. **`Conservative_Fusion_Ensemble`**: Portfolio union router requiring agreement of at least two independent sleeves.

---

## 2. Parameter Grid & Search Space

We will sweep a total of 1,000 parameter combinations:

- `tp_atr_mult`: `[2.0, 2.5, 3.0]`
- `sl_atr_mult`: `[1.2, 1.4, 1.6, 1.8]`
- `adx_thresh`: `[12, 15, 20, 25]`
- `max_cost_to_risk`: `[0.08, 0.10, 0.12, 0.15]`
- `min_projected_net_R`: `[0.80, 0.82, 0.85]`
- `regime_filter_mode`: `["soft", "strict"]`

---

## 3. Promotion & Quality Gates

A candidate will be promoted to **Strategy #1.2** in Phase 39 only if it satisfies all of the following:

| Metric | Threshold Gate | Baseline (Strategy #1) |
|---|---|---|
| **Net PnL** | >= $11,500.00 | $11,205.20 |
| **Trade Count** | >= 400 | 557 |
| **Profit Factor** | >= 1.40 | 1.2522 |
| **Max Drawdown** | <= 9.0% | 16.2186% |
| **Stress Audit** | >= 9/15 Scenario PASS | 7/15 Scenario PASS |
| **Monthly Consistency** | <= 18 negative months | 25 negative months |
| **Combined Adverse PnL** | > $0.00 (Positive expected value) | -$39,138.38 |
| **Lookahead Audit** | 0 violations (Hard gate) | 0 violations |
