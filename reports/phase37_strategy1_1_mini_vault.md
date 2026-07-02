# Phase 37 Strategy #1.1 Mini Vault

## Identity

- Candidate: `P37_CAND_0357`
- Promotion reason: `HIGH_PNL_PROMOTION`
- Status: BACKTEST_VERIFIED_NOT_SHADOWED / NOT_REAL_CAPITAL_READY

## Metrics

- PnL: 11231.08
- Trades: 404
- PF: 1.3862
- DD: 9.3716%
- Stress pass: 8/15
- Combined adverse PnL: -33384.48

## Rules

Parameters: `{"allowed_sessions": ["LONDON", "NEW_YORK", "OFF_HOURS"], "allowed_sources": ["BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short", "Funding Reversal Short"], "disallowed_sources": [], "max_abs_funding": 0.0015, "max_cost_to_risk": 0.12, "min_adx": 12, "min_atr_pct": 0.3, "min_bb_width": 0.03, "min_projected_net_R": 0.82, "min_stop_atr": 0.0, "off_hours_min_expected_R": 0.0}`

Code path: `scripts/phase37_strategy1_1_second_stage_optimization.py::CachedSignalStrategy`.
Trade log: `reports/phase37_strategy1_1_trade_log.csv`
Trade log hash: `3a8be9b7a2041fec997496d5f7d931b824cb0676cf88c6670ecabb09ad57bfc4`

## Live Automation

Rules are closed-candle Strategy #1 signals plus live-known guards. This remains `NOT_REAL_CAPITAL_READY` without exchange shadow proof.
