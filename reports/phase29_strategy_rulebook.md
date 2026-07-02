# Phase 29 Strategy Rulebook

## Verified Executable Strategy Surface

The only executable strategy object behind the latest benchmark runners is `build_p10_1_strategy()` in `src/research/phase12_runner.py`.
It creates a `FusionOfFusionsStrategy` with four sub-portfolios:

| Portfolio | Members | Routing Notes |
|---|---|---|
| quality_core | CAND_C, CAND_F, CAND_G, CAND_D | union mode, conflict cancel, zero-month rescue enabled |
| activity | CAND_A, CAND_C, CAND_F | union mode, conflict cancel, inactive after monthly trade count reaches 5 |
| defensive | CAND_C, CAND_G, CAND_D | active when monthly drawdown >= 1.5% |
| zero_rescue | CAND_D, CAND_G | active after day 10 with 0 trades or day 15 with fewer than 6 trades |

## Entry Rule Table

| Template | Timeframe | Long / Short Logic | Filters |
|---|---|---|---|
| CAND_A bollinger_expansion_breakout | 1h | BB expansion breakout direction | no regime filter, RSI thresholds, ADX threshold, bb_width_thresh |
| CAND_C bollinger_expansion_breakout | 1h | Same family as CAND_A | strict regime filter, wider RSI allowance |
| CAND_D low_activity_filler | 1h | low-activity filler logic inside UniversalStrategyTemplate | activated only through zero-month rescue routing |
| CAND_F atr_volatility_expansion | 1h | volatility expansion continuation | strict regime filter |
| CAND_G funding_extreme_reversal | 1h | funding extreme reversal | strict regime filter, funding threshold logic |

PF 7.0, PF 8.0, and PF 8.1 claimed sleeves are not implemented as standalone live strategy classes in the audited code. Their latest runners synthesize or hardcode benchmark outputs.

## Exit Rules

The backtest engine exits on SL/TP, with SL priority when both SL and TP are touched in the same candle. It supports trailing stop, breakeven, time stop, failed-continuation exit, force close at end of test, funding debits at 8-hour boundaries, and market slippage on exits.

## Risk Rules

| Rule | Verified Code Behavior |
|---|---|
| Initial capital | 10000.0 |
| Maker fee | 0.0002 |
| Taker fee | 0.0005 |
| Slippage | 0.0005 |
| Max positions | 1 |
| Cooldown candles | 5 |
| Risk per trade | engine uses 1% of current capital before dynamic throttles |
| Leverage cap | position notional capped at 5x capital |
| Min notional | engine boosts to $100 notional where needed |
| Size rounding | round(size, 3) |
| Price rounding | round(entry_price, 1) |
| Monthly risk config | {'risk_limit_pct': 1.0, 'monthly_risk_limit': 0.025, 'risk_throttle_mode': 'no_throttle', 'emergency_pause_threshold': 0.025} |

## Live-Known Feature Matrix

| Feature | Status |
|---|---|
| Closed-candle signal generation | Present in backtest logic |
| Binance exchange connector | Missing |
| Real order placement | Missing |
| Shadow exchange order lifecycle | Report-only / simulated |
| Restart recovery | Missing |
| API retry and rate-limit handling for live trading | Missing |
| Kill switch / daily loss guard / position guard | Missing |
