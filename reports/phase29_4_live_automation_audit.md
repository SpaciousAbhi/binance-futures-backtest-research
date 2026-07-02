# Phase 29.4 Live Automation Audit

Phase 29.4 rebuilds are backtest-only research artifacts.

## PF1.2 Distilled Live Router

- Entry timing: closed-candle signal evaluation through the existing backtest engine.
- Exit timing: deterministic engine TP/SL handling.
- SL/TP: signal stop and target are generated before trade entry.
- Router: Variant C core priority; Variant B rescue fallback only if no C signal is accepted.
- Duplicate control: engine max positions is one; same-position overlap is not exchange-tested.
- Funding handling: candle-aligned funding feature only; no later funding values are used for signal generation.
- Tick/step/min-notional: not exchange-shadow verified in this phase.
- Reduce-only exits: concept only; no exchange order lifecycle proof exists.
- Exchange shadow status: no Binance shadow/live execution ledger was produced.

Final live status: NOT_REAL_CAPITAL_READY.
