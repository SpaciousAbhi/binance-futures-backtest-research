# Phase 30.1 — Reusable Research Idea Library

This library contains 15 structured strategy hypotheses representing the key research families required to address Precision Fusion goals.

## Summary of Families
The following families are mapped out with all 24 required audit and logic parameters:

1. **IDEA_001**: Teacher Trade Replay & Path Verification (PF1.2 teacher replay diagnostics)
2. **IDEA_002**: Strict Regime Breakout Live Compiler (Variant C live rebuild)
3. **IDEA_003**: Variant B Broad-Capture Recovery (Variant B rescue rebuild)
4. **IDEA_004**: Multi-Timeframe Breakout Confirmation (MTF retest confirmation)
5. **IDEA_005**: VWAP Band Reclaim Strategy (VWAP reclaim)
6. **IDEA_006**: Double Retest Confirmation Filter (second retest)
7. **IDEA_007**: Extreme Funding Defensive Skip (funding defensive skip)
8. **IDEA_008**: New York Session Liquidity Filter (NY low-liquidity hardening)
9. **IDEA_009**: Weak Momentum Early Exit (weak continuation exits)
10. **IDEA_010**: Dynamic Breakeven & Time Exit (breakeven/trailing/time-stop)
11. **IDEA_011**: Dirty PF8 Core Cleansing (Dirty PF8 quality surgery)
12. **IDEA_012**: Liquidity Gap Defensive Gate (session/liquidity filters)
13. **IDEA_013**: Bollinger Band Width Squeeze Filter (volatility expansion/compression)
14. **IDEA_014**: Dynamic Expected R-Multiple Gate (expected-R dynamic gates)
15. **IDEA_015**: Cross-Asset Volatility Porting (cross-asset generalization)

## Top Ranked Ideas

### 1. IDEA_001 — Teacher Trade Replay & Path Verification
- **Family:** PF1.2 teacher replay diagnostics
- **Hypothesis:** Replaying original 325 teacher trades at 5m resolution isolates candle-structure assumptions from physical price execution.
- **Target Problem:** PF1.2 5m engine trade log mismatch (3,111 trades, PF 0.64).
- **Expected Live-Known Features:** `candle_open_time, index_in_hour, close_to_atr_ratio`
- **Required Data:** BTCUSDT 5m OHLCV, phase12_runner.py trade logs
- **Entry/Exit:** Execute entry at the exact timestamp recorded in the 1h teacher log. / Simulate stop-loss (1.8x ATR) and take-profit (2.5x ATR) using 5m high/low paths.
- **Complexity / Priority:** Medium / High (Priority 1)
- **Why it might work / fail:** Accurately maps which teacher trades are stopped out before target, validating the engine path. / If teacher entries were based on hindsight indices not present in live data.
- **Lookahead / Hardcoding Risk:** None (replay is diagnostic only). / High if used directly for live trading; low if used as a diagnostic.
- **Success / Kill Criteria:** Accurate tracking of every teacher trade survival status with path logs. / If 100% of trades are instantly stopped out due to data alignment gaps.

### 2. IDEA_004 — Multi-Timeframe Breakout Confirmation
- **Family:** MTF retest confirmation
- **Hypothesis:** Requiring a 5m wick retest confirmation of a 1h breakout level improves entry precision.
- **Target Problem:** High slippage and execution decay of 1h breakout entries.
- **Expected Live-Known Features:** `is_1h_breakout, has_5m_retest, distance_to_breakout`
- **Required Data:** BTCUSDT 1h + 5m processed data
- **Entry/Exit:** 1h candle closes in breakout; entry is placed on limit order at the 1h breakout level during next 1h. / SL/TP managed at 5m resolution based on 1h ATR.
- **Complexity / Priority:** High / High
- **Why it might work / fail:** Enables limit order execution (maker fees) instead of market orders (taker fees). / Missing high-momentum breakouts that never retest the level.
- **Lookahead / Hardcoding Risk:** Low (1h closes first, then 5m limits are evaluated). / None.
- **Success / Kill Criteria:** Maker entry execution with positive PnL in backtest. / If match rate with teacher trades falls below 10%.

### 3. IDEA_010 — Dynamic Breakeven & Time Exit
- **Family:** breakeven/trailing/time-stop
- **Hypothesis:** Moving stop-loss to breakeven after price reaches 1.0x ATR profit protects open equity.
- **Target Problem:** Winning trades turning into complete losers due to quick market reversals.
- **Expected Live-Known Features:** `max_unrealized_pnl, atr_at_entry`
- **Required Data:** BTCUSDT 5m processed OHLCV
- **Entry/Exit:** No change to entry. / Adjust SL to entry price once unrealized PnL exceeds 1.0x ATR. Add 48-candle hard time limit.
- **Complexity / Priority:** Medium / High
- **Why it might work / fail:** Locks in protection and prevents capital drag from stagnant positions. / Prematurely stops out trades that retest the entry level before moving to target.
- **Lookahead / Hardcoding Risk:** None. / None.
- **Success / Kill Criteria:** Reduces max DD by at least 15% without reducing net PnL by more than 10%. / If the number of breakeven stopped trades exceeds 60% of all trades.

### 4. IDEA_013 — Bollinger Band Width Squeeze Filter
- **Family:** volatility expansion/compression
- **Hypothesis:** Requiring a period of volatility compression (Bollinger Band width < threshold) before entering a breakout increases success rate.
- **Target Problem:** Chop losses caused by entering breakouts during wide, choppy volatility ranges.
- **Expected Live-Known Features:** `bb_width, rolling_volatility_compression`
- **Required Data:** BTCUSDT 1h processed data with Bollinger Bands
- **Entry/Exit:** Only enter breakout if Bollinger Band width was in the lowest 25% of the last 100 candles. / Standard ATR TP/SL.
- **Complexity / Priority:** Medium / High
- **Why it might work / fail:** Filters out late trend-continuation entries, catching moves at start of expansion. / Slow consolidation periods can lead to false breakouts that resolve in opposite directions.
- **Lookahead / Hardcoding Risk:** None. / None.
- **Success / Kill Criteria:** Breakout win rate increases from 45% to 52%. / If total net PnL is lower than baseline PF 1.2.