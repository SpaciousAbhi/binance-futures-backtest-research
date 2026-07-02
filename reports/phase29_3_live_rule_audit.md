# Phase 29.3 Live Rule Audit

## Rebuilt PF1.2

- Entry timing: closed-candle only in executable rebuild.
- Exit timing: engine-managed TP/SL/time handling.
- SL/TP: deterministic signal stop and target fields.
- Trailing/breakeven/time stop: only used where engine/sleeve exposes live-known fields.
- Same-candle SL/TP priority: inherited conservative backtest engine behavior.
- Tick/step/min-notional: modeled, not exchange-shadow verified.
- Funding handling: available as candle-aligned feature; no future funding used.
- Reduce-only exit concept: not exchange-tested.
- Max concurrent positions: 1.
- Cooldown: 5 candles.
- Exchange shadow readiness: not proven.

## Best Recovered PF8 Attempt

- Candidate metrics are assigned only to engine-executed rows.
- Unexecuted candidates remain blank-metric registry rows.
- Status: NOT_REAL_CAPITAL_READY.

Final live status: `PF12_PARTIAL_EXECUTABLE_REBUILD_REQUIRES_MORE_RECOVERY` and NOT_REAL_CAPITAL_READY. No real-capital readiness exists without exchange-level shadow/live proof.
