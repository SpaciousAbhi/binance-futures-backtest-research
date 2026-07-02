# Phase 33 Repair Module Design

All modules are live-known filters over the existing executable Combined Router signal stream.

Modules tested:
- Minimum expected-R gates: 1.0, 1.2, 1.4, 1.6, 1.8, 2.0.
- Cost-to-ATR gates: friction must be small relative to initial risk distance.
- Minimum projected net-R gates: expected R minus estimated friction R.
- Session hardening: off-hours skip, London/NY only, London only.
- Source sleeve rebalance: floor low-activity only, BB expansion only.
- Same-candle ambiguity hardening: skip same-candle-prone entries.
- Monthly risk governor: pause after live-known monthly loss thresholds.
- Toxic cluster blacklist: live-known session/R/cost/source clusters only.

No trade IDs, months, future outcomes, teacher labels, or forced metrics are used in live filter rules.
