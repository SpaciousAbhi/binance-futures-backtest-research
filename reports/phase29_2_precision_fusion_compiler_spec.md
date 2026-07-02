# Phase 29.2 Precision Fusion Compiler Spec

PF means Precision Fusion: a reproducible router over candidate sleeves, filters, exits, and risk rules.

## Deterministic Rules

1. Sleeve configs are serialized before execution.
2. Each metric-bearing candidate must run through `MultiPositionBacktestEngine`.
3. Same-candle duplicate same-side entries are rejected unless `max_positions` explicitly allows more than one.
4. Long/short conflicts are resolved by live-known expected R, lower risk distance, fixed family priority, then earliest signal.
5. Unexecuted candidates remain registered-only and receive blank metrics.
6. Report rows, dirty trade diagnostics, and PF1.2 reconstructed trade sets are not allowed to become accepted executable benchmarks.

## Saved Config

`reports/phase29_2_precision_fusion_compiler_config.json` stores the compiler policy used for this phase.
