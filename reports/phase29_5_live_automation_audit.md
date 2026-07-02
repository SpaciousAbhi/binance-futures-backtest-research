# Phase 29.5 Live Automation Readiness Audit

## Best PF1.2 MTF Rebuild

- Entry rules: closed 1h engine signals with closed 15m/5m features from the completed setup candle.
- Exit rules: deterministic engine stop loss, take profit, optional breakeven, trailing, and time stop where configured.
- Order timing: signal on closed candle, fill at next engine candle open.
- Same-candle SL priority: engine uses conservative stop-first handling.
- Funding handling: candle-aligned funding only.
- Tick/step/min-notional: modeled in engine, not exchange-shadow verified.
- Reduce-only exit concept: not proven against exchange order ledger.
- Shadow-mode gaps: no Binance shadow execution, restart recovery, partial-fill ledger, or rate-limit proof.

## Best Recovered PF8/PF8.1 Router

- Candidate rows carry metrics only when `status=EXECUTED_ENGINE`.
- Unexecuted rows are blank-metric registered candidates.
- Dirty PF8 filtered rows remain diagnostic and are not accepted as benchmarks.

Final status: PF12_MAJOR_MTF_RECOVERY_PROGRESS_PF8_RESEARCH_CONTINUES. Live capital status: NOT_REAL_CAPITAL_READY.
