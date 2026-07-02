# Phase 29.3 Precision Fusion Compiler Spec

PF means Precision Fusion: a deterministic compiler/router over multiple live-known sleeves.

## Required Behavior

- Accept multiple sleeve configs with explicit priority.
- Compute live-known expected R from current signal stop/target distance.
- Reject rescue signals below their expected-R gate.
- Resolve same-candle conflicts by expected R, fixed priority, then lower stop distance.
- Keep max concurrent positions controlled by `MultiPositionBacktestEngine(max_positions=1)`.
- Emit final trade log, rejected signal table, conflict table, monthly table, stress table, and manifest hash.
- Never convert teacher/reconstructed trade sets into executable proof.

## Phase 29.3 Compiler Instance

- Sleeve 1: `variant_c_core_live_proxy`, priority 1, expected-R gate 1.15.
- Sleeve 2: `variant_b_rescue_live_proxy`, priority 2, expected-R gate 1.40.
- Engine: `MultiPositionBacktestEngine`, max positions 1, cooldown 5.
