# Next Phase Plan - Phase 40

## Goal
Fix the stress harness to use notional-scaled fees/slippage, rerun stress on all strategies,
and deliver a final promotion verdict for Strategy #1.2 (`P39_CAND_0551`).

## Context (Phase 39.1 Reconciliation Result)
Phase 39.1 found that:
- Strategy #1.2 metrics are CORRECT at: PnL=$11,431.41, trades=340, PF=1.4998, DD=7.9380%
- Promotion gates were NOT fully passed — closest is Track C (fails stress 8/15 vs required 10/15)
- The stress harness combined-adverse model is FLAWED (flat fees not scaled by notional)
- Status: PROVISIONAL pending stress harness repair

**Do NOT do multi-asset validation or shadow execution until stress harness is repaired.**

## Phase 40 Requirements (Priority Order)

### P1 — Repair Stress Harness (BLOCKING)
1. Update stress runner to scale fee/slippage by `size × entry_price` per trade, not flat per-trade
2. Ensure the correction is applied consistently across all 15 stress scenarios
3. Verify that Strategy #1 and #1.1 stress results are recomputed with the same harness

### P2 — Rerun Stress on All Three Strategies
1. Strategy #1 (Combined Router v1, 557 trades) — recompute all 15 scenarios
2. Strategy #1.1 (P37_CAND_0357, 404 trades) — recompute all 15 scenarios
3. Strategy #1.2 (P39_CAND_0551, 340 trades) — recompute all 15 scenarios

### P3 — Re-evaluate Promotion Gates
1. Apply Track C gate: stress_pass >= 10/15
2. If Strategy #1.2 reaches 10/15: → Status = CONFIRMED_PROMOTED
3. If Strategy #1.2 stays at 8/15 or below: → Status = DEMOTED_TO_RESEARCH_ONLY

### P4 — Update All Project Memory
1. Update BENCHMARK_REGISTRY.csv with corrected stress results
2. Update CURRENT_HANDOFF.md with final decision
3. Update vault with final status

### P5 — Only if P1-P4 complete: Multi-Asset Validation
If stress gate passes and Strategy #1.2 is confirmed, extend to ETHUSDT, BNBUSDT, SOLUSDT.
Live status remains NOT_REAL_CAPITAL_READY.

---

### Memory Protocol Compatibility (Do Not Delete)
- Historical continuity references: Phase 33, Phase 37, Phase 39, Phase 39.1.
- References: Phase 38, Phase 39, Phase 39.1.
