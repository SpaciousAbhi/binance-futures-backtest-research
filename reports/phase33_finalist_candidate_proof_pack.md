# Phase 33 Finalist Candidate Proof Pack

## best_repair_module: toxic_live_cluster_filter

- Status: EXECUTED_FILTER_REPLAY
- Family: toxic_live_cluster_filter
- Parameters: `{"max_cost_to_atr": 0.3, "min_expected_R": 1.2, "session_mode": "NO_OFF_HOURS"}`
- Net PnL: 8871.0
- Trades: 222
- PF: 1.4761
- DD: 9.8514
- Stress pass count: 9/15
- Combined adverse PnL: -12096.45
- Trade log hash: 4abfa82704ff979bda5b8be546ca2c0e1bbba4c0da87344c97b255db67d23dd7
- Live-path audit: PASS; rules use session, expected-R, cost-to-ATR, projected net-R, source family, and monthly governor state only.
- Fusion decision: Include only if it improves PF/DD/stress without making PnL collapse beyond research tolerance.

## best_individual_candidate: P33_0626

- Status: EXECUTED
- Family: low_correlation_complement
- Parameters: `see csv`
- Net PnL: 3517.69
- Trades: 62
- PF: 1.6751
- DD: 6.4164
- Stress pass count: 12/15
- Combined adverse PnL: -2696.5
- Trade log hash: 85b4c71f1ed323cbb4b7ec2700840346db1c3be3c83d2dab9e8221406f8f1755
- Live-path audit: PASS; rules use session, expected-R, cost-to-ATR, projected net-R, source family, and monthly governor state only.
- Fusion decision: Include only if it improves PF/DD/stress without making PnL collapse beyond research tolerance.

## best_fusion: multi_candidate_low_correlation_fusion

- Status: EXECUTED_SERIALIZED_FILTER_FUSION
- Family: multi_candidate_low_correlation_fusion
- Parameters: `{"cost_regime_max": null, "entry_family": "ALL", "max_cost_to_atr": 0.4, "min_expected_R": 1.4, "min_projected_net_R": null, "monthly_dd_limit": 0.015, "session_mode": "NY_ONLY", "skip_same_candle": false}`
- Net PnL: 3517.69
- Trades: 62
- PF: 1.6751
- DD: 6.4164
- Stress pass count: 12/15
- Combined adverse PnL: -2696.5
- Trade log hash: 85b4c71f1ed323cbb4b7ec2700840346db1c3be3c83d2dab9e8221406f8f1755
- Live-path audit: PASS; rules use session, expected-R, cost-to-ATR, projected net-R, source family, and monthly governor state only.
- Fusion decision: Include only if it improves PF/DD/stress without making PnL collapse beyond research tolerance.

NOT_REAL_CAPITAL_READY
