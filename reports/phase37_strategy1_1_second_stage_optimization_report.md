# Phase 37 - Strategy #1.1 Second-Stage Optimization Report

## Final Verdict

`PHASE37_PASS_STRATEGY1_1_PROMOTED`

## Strategy #1 Reproduction

Strategy #1 reproduced exactly before optimization. See `reports/phase37_strategy1_reproduction_lock.csv`.

## Search Scope

- Registered candidates: at least 3,000.
- Engine-executed candidates: 500.
- Search was focused on Phase 36 live-known levers: projected net-R, cost-to-risk, off-hours hardening, Low-Activity Filler suppression, BB/ATR source preservation, ADX/ATR/BB-width filters, and funding caps.
- Unexecuted candidates have blank metrics.

## Best Candidates By Objective

- Best high-PnL row: P37_CAND_0357 | PnL 11231.08 | PF 1.3862 | DD 9.3716 | stress 8/15
- Best PF/DD quality row: P37_CAND_0413 | PnL 9428.93 | PF 1.5168 | DD 5.8088 | stress 8/15
- Best stress row: P37_CAND_0203 | PnL 3930.56 | PF 1.4146 | DD 12.1365 | stress 8/15

## Strategy #1.1 Selection

Selected Strategy #1.1: `P37_CAND_0357`.

Promotion reason: `HIGH_PNL_PROMOTION`.

## Research Candidates Preserved

none

## Integrity

Top candidates were audited for trade log existence, metrics-from-log, live-known rule construction, timestamp order, and source hash. Live status remains `NOT_REAL_CAPITAL_READY`.

## Required Answers

1. Strategy #1 reproduced: yes.
2. Candidates registered: see `phase37_candidate_registry.csv`.
3. Candidates executed: 500.
4. Levers that worked: projected net-R, Low-Activity Filler suppression, cost-to-risk/off-hours combinations.
5. Best PnL candidate: P37_CAND_0357 | PnL 11231.08 | PF 1.3862 | DD 9.3716 | stress 8/15.
6. Best PF/DD candidate: P37_CAND_0413 | PnL 9428.93 | PF 1.5168 | DD 5.8088 | stress 8/15.
7. Best stress candidate: P37_CAND_0203 | PnL 3930.56 | PF 1.4146 | DD 12.1365 | stress 8/15.
8. Strategy #1.1 promoted: yes.
9. Promotion reason: HIGH_PNL_PROMOTION.
10. Non-promotion reason: not applicable.
11. Phase 38: vault Strategy #1.1 and validate multi-asset robustness.
12. GitHub/project memory: updated before final push.
