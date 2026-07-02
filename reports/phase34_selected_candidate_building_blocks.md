# Phase 34 Selected Candidate Building Blocks

## Strategy #2 Candidate: P34_0217

- Family/template: high_pf_low_frequency
- Parameters: `{"family": "high_pf_low_frequency", "max_cost_to_risk": 0.1, "min_expected_R": null, "min_hold_candles": null, "min_projected_net_R": null, "session_mode": "NO_OFF_HOURS", "skip_same_candle": false, "source_mode": "ALL"}`
- Net PnL: 9273.69
- Trades: 338
- PF: 1.3505
- DD: 9.2091%
- Stress pass count: 9/15
- Combined adverse: -23544.77
- Trade log: `reports/phase34_candidate_P34_0217_trade_log.csv`
- Trade log hash: `8770fd4760ef73c62d1a32ee9cb3d801aaf8a832bfa90b5aacd02058dbfd2195`
- Code path: Phase 34 deterministic candidate gate over Strategy #1 engine-generated trade stream.
- No-lookahead status: PASS_ACTIVE_FILTERS_ONLY.
- Hardcoding status: PASS_NO_OUTCOME_IDS_OR_MONTHS.
- Live execution status: BACKTEST_VERIFIED_NOT_SHADOWED.
- Reason selected: balanced score across PnL, PF, DD, trade count, stress, and uniqueness.
- Weakness: not yet a standalone signal generator; must be implemented signal-level before benchmark promotion.

## Strategy #3 Candidate: P34_0007

- Family/template: high_pf_low_frequency
- Parameters: `{"family": "high_pf_low_frequency", "max_cost_to_risk": 0.1, "min_expected_R": null, "min_hold_candles": null, "min_projected_net_R": 0.9, "session_mode": "NO_OFF_HOURS", "skip_same_candle": false, "source_mode": "ALL"}`
- Net PnL: 8797.20
- Trades: 277
- PF: 1.3938
- DD: 10.2819%
- Stress pass count: 9/15
- Combined adverse: -17230.72
- Trade log: `reports/phase34_candidate_P34_0007_trade_log.csv`
- Trade log hash: `ad5faa4bd7953b4c78c45f7fdddf24a2df328fe302e32de848a865d1fc9c894e`
- Code path: Phase 34 deterministic candidate gate over Strategy #1 engine-generated trade stream.
- No-lookahead status: PASS_ACTIVE_FILTERS_ONLY.
- Hardcoding status: PASS_NO_OUTCOME_IDS_OR_MONTHS.
- Live execution status: BACKTEST_VERIFIED_NOT_SHADOWED.
- Reason selected: balanced score across PnL, PF, DD, trade count, stress, and uniqueness.
- Weakness: not yet a standalone signal generator; must be implemented signal-level before benchmark promotion.

## Strategy #4 Candidate: P34_0219

- Family/template: balanced_activity
- Parameters: `{"family": "balanced_activity", "max_cost_to_risk": 0.1, "min_expected_R": 1.1, "min_hold_candles": null, "min_projected_net_R": 0.7, "session_mode": "NO_OFF_HOURS", "skip_same_candle": false, "source_mode": "ALL"}`
- Net PnL: 8509.13
- Trades: 214
- PF: 1.4746
- DD: 10.0440%
- Stress pass count: 9/15
- Combined adverse: -13623.84
- Trade log: `reports/phase34_candidate_P34_0219_trade_log.csv`
- Trade log hash: `3fb1d1af3f87889363b6605320444a6614b171a3265b2698b56a06c0c4496d61`
- Code path: Phase 34 deterministic candidate gate over Strategy #1 engine-generated trade stream.
- No-lookahead status: PASS_ACTIVE_FILTERS_ONLY.
- Hardcoding status: PASS_NO_OUTCOME_IDS_OR_MONTHS.
- Live execution status: BACKTEST_VERIFIED_NOT_SHADOWED.
- Reason selected: balanced score across PnL, PF, DD, trade count, stress, and uniqueness.
- Weakness: not yet a standalone signal generator; must be implemented signal-level before benchmark promotion.

## Strategy #5 Candidate: P34_0218

- Family/template: stress_hardened
- Parameters: `{"family": "stress_hardened", "max_cost_to_risk": 0.1, "min_expected_R": 1.0, "min_hold_candles": null, "min_projected_net_R": null, "session_mode": "NO_OFF_HOURS", "skip_same_candle": false, "source_mode": "ALL"}`
- Net PnL: 8439.85
- Trades: 271
- PF: 1.3793
- DD: 10.4791%
- Stress pass count: 9/15
- Combined adverse: -18189.50
- Trade log: `reports/phase34_candidate_P34_0218_trade_log.csv`
- Trade log hash: `f20126ff3edf206e75d56c923387ec7b86252534bf654a2c0c454803c6421bce`
- Code path: Phase 34 deterministic candidate gate over Strategy #1 engine-generated trade stream.
- No-lookahead status: PASS_ACTIVE_FILTERS_ONLY.
- Hardcoding status: PASS_NO_OUTCOME_IDS_OR_MONTHS.
- Live execution status: BACKTEST_VERIFIED_NOT_SHADOWED.
- Reason selected: balanced score across PnL, PF, DD, trade count, stress, and uniqueness.
- Weakness: not yet a standalone signal generator; must be implemented signal-level before benchmark promotion.

## Strategy #6 Candidate: P34_0002

- Family/template: low_r_filtered
- Parameters: `{"family": "low_r_filtered", "max_cost_to_risk": null, "min_expected_R": 1.1, "min_hold_candles": null, "min_projected_net_R": null, "session_mode": "ALL", "skip_same_candle": false, "source_mode": "ALL"}`
- Net PnL: 8998.42
- Trades: 349
- PF: 1.2926
- DD: 15.1980%
- Stress pass count: 9/15
- Combined adverse: -22897.88
- Trade log: `reports/phase34_candidate_P34_0002_trade_log.csv`
- Trade log hash: `a0eed28f98fa3db8eceda79f5b5c3f073e4ae7302de4a4cdb358a33333fda6a7`
- Code path: Phase 34 deterministic candidate gate over Strategy #1 engine-generated trade stream.
- No-lookahead status: PASS_ACTIVE_FILTERS_ONLY.
- Hardcoding status: PASS_NO_OUTCOME_IDS_OR_MONTHS.
- Live execution status: BACKTEST_VERIFIED_NOT_SHADOWED.
- Reason selected: balanced score across PnL, PF, DD, trade count, stress, and uniqueness.
- Weakness: not yet a standalone signal generator; must be implemented signal-level before benchmark promotion.

