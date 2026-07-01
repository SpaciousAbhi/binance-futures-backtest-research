# Rules and Regulations

This document defines the strict operational rules and regulations for the strategy research and backtesting engine. All strategies, pipelines, and portfolio models must comply with these guidelines.

---

## 1. Data Integrity and Sourcing
* **No Fake Data**: All simulations must run on real historical market data sourced from Binance USD-M Perpetual Futures REST API. Synthetic or generated price series are forbidden as evidence of success.
* **No Fake Candles**: No candles may be altered, inserted, or manually deleted. The original chronological order and raw values (Open, High, Low, Close, Volume) must be preserved.
* **No Future Candles**: Strategies are forbidden from accessing any index `i + k` when processing bar `i`.
* **No Future Funding**: The funding rate at candle `i` must correspond to historical rate limits active at or before the candle's open timestamp.
* **No Lookahead Bias**: No indicators, indicators calculations, or signals may look forward in the dataframe.

---

## 2. Trading and Simulation Rules
* **No Fake Trades**: All trades must be simulated on closed candles and execute at next-candle open prices, incorporating taker/maker transaction costs, slippage, and funding.
* **No Fake PnL**: PnL calculations must reflect actual simulated executions. Removing losing trades, inserting fake wins, or overriding execution outcomes is strictly prohibited.
* **Closed-Candle-Only Rule**: Trading signals must be calculated using only information up to the closed bar `i`.
* **Next-Candle Execution Rule**: Execution of entry and exit orders must occur on the next candle's open (`i + 1`) or at realistic execution offsets (delay candles). Immediate same-bar execution is banned.
* **Deterministic Live-Compatible Signals**: Signals must be generated using logic that is fully compatible with live trading environments (no post-hoc fitting).
* **Deterministic SL/TP/Risk Rule**: Every trade must have a fixed, predefined Stop Loss, Take Profit, and risk sizing model defined at entry.

---

## 3. Anti-Curve-Fitting Controls
* **No Hardcoded Dates**: Hardcoding date or time windows inside strategy classes to block entries or bypass historical drawdowns is forbidden.
* **No Hardcoded Months**: Strategy rules must not check calendar month strings or month numbers (e.g. `if month == 12: exit_position`).
* **No Trade-ID Filters**: Banning specific trades by trade IDs or index offsets is prohibited.
* **No Signal-ID Filters**: Banning specific signals by signal IDs is prohibited.
* **No Outcome-Based Filtering**: Filtering trades post-backtest based on outcome (e.g. deleting losing trades) to boost statistics is illegal.
* **Calendar Strings Forbidden in Logic**: Date/month names or numbers are allowed only in reporting formatters, never within strategy signal logic.
