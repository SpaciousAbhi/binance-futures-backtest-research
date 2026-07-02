# Phase 29.6 Live Automation Readiness Audit

## Rebuilt PF1.2 MTF Engine

- Entry timing: 1h closed setup, then 5m closed trigger, then next 5m open or retest fill.
- Exit timing: 5m SL/TP/path simulation with conservative same-candle SL_FIRST priority.
- Stop loss and take profit: serialized per trade in `phase29_6_pf12_mtf_trade_log.csv`.
- Breakeven, trailing, and time stop: supported by config and recorded through exit reason/path fields.
- Funding: only candle-aligned `fundingRate` available at or before the simulated event is used.
- Tick/step/min-notional: modeled with deterministic local rounding; not exchange-shadow verified.
- Reduce-only exits: concept recovered from old operating docs, but no exchange order ledger exists.
- Shadow-mode gaps: partial fills, API retries, exchange rejection handling, restart recovery, and rate limits remain unproven.

Best engine-generated system in this phase: pf12_event_driven_mtf_router, PnL -9940.722026670763, trades 3111, PF 0.6441043118089674.

Final live status: NOT_REAL_CAPITAL_READY.
