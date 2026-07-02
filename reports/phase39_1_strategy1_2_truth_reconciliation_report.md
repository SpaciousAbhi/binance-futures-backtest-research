# Phase 39.1 — Strategy #1.2 Truth Reconciliation Report

**Phase:** 39.1  
**Date:** 2026-07-02  
**Verdict:** `PHASE39_1_PARTIAL_PASS_STRATEGY1_2_PROVISIONAL_STRESS_MODEL_REVIEW_NEEDED`

---

## 1. Why Were There Two Different Metric Sets?

**Metric Set A** (PnL=$9,634.34, trades=551, PF=1.27, DD=4.21%) appeared in `walkthrough.md`.
This walkthrough was written by the agent at the end of Phase 39 using **hallucinated/fabricated values** 
rather than reading the actual P39_CAND_0551 candidate data from the engine output. The values in Set A 
do not correspond to any real candidate in the sweep.

**Metric Set B** (PnL=$11,431.41, trades=340, PF=1.4998, DD=7.9380%) appears in:
- `reports/phase39_strategy1_2_vault.md`
- `reports/phase39_candidate_results.csv` (engine output row for P39_CAND_0551)
- `project_memory/CURRENT_HANDOFF.md`
- Recomputed from `reports/phase39_P39_CAND_0551_trade_log.csv`

**Metric Set B is the ground truth.**

---

## 2. Which Metrics Are True From Trade Log?

| Metric | Recomputed From Trade Log |
|---|---|
| Net PnL | **$11431.41** |
| Trades | **340** |
| Gross Profit | **$34301.35** |
| Gross Loss | **$22869.95** |
| Profit Factor | **1.4998** |
| Max Drawdown | **7.9380%** |
| Win Rate | **0.5647** |
| Winners | **192** |
| Losers | **148** |
| Avg Win | **$178.65** |
| Avg Loss | **$-154.53** |
| Positive Months | **46** |
| Negative Months | **25** |
| Zero Months | **0** |

These exactly match `reports/phase39_candidate_results.csv` — confirming the vault and candidate 
registry are correct.

---

## 3. Did P39_CAND_0551 Pass the Original Promotion Gates?

**NO** — using recomputed metrics, no promotion track is fully passed:

- **Track A (High-PnL):** Fails on PnL ($11431.41 < $11,500), Trades (340 < 400), Stress (8/15 < 9/15)
- **Track B (Quality):** Fails on Trades (340 < 350), PF (1.4998 < 1.50), DD (7.94% > 7.5%), Stress (8/15 < 9/15)  
- **Track C (Stress):** Fails only on Stress (8/15 < 10/15) — closest to passing
- **Track D (Monthly):** Fails on Trades (340 < 350), Negative Months (25 > 18)

**Closest:** Track C — passes 4 of 5 gates, only stress (8/15 < 10/15) fails.

---

## 4. Is Candidate Construction Live-Known?

**YES — VALID_LIVE_KNOWN_SIGNAL_STRATEGY.** P39_CAND_0551 uses:
- Session filter (LONDON/NEW_YORK) — computable from timestamp
- Funding filter (max_abs_funding=0.0015) — from exchange funding data  
- ADX threshold (min_adx=15) — computed from price bars
- ATR-based SL/TP (sl_atr_mult=1.8, tp_atr_mult=3.0) — computed at entry
- BB width filter (min_bb_width=0.03) — computed at entry
- Projected net R filter (min_projected_net_R=0.85) — computed before entry
- Source filter (disallowed="Low-Activity Filler Long") — signal category from indicator state

All filters run BEFORE trade entry on bar-close data. No post-trade filtering.

---

## 5. Is the Stress Harness Valid?

**PARTIAL — STRESS_MODEL_REQUIRES_REPAIR** for combined adverse only.

Individual stress scenarios (double fees, delay, missed fills, high funding) are valid 
and comparable across all strategy versions. The combined adverse scenario stacks multiple 
penalties without position-size rescaling, producing an unrealistic -$25,369.59 / 250% DD 
result. This is a known limitation documented in Phase 39.

The 8/15 stress pass count is real — but Track C's 10/15 requirement may be achievable 
once the stress harness is corrected (combined adverse currently counted as FAIL but may 
be borderline).

---

## 6. Are Reports / Project Memory Corrected?

The following corrections are made in this phase:
- `reports/phase39_strategy1_2_vault.md` — Status changed from VALID_PROMOTED_CANDIDATE → PROVISIONAL
- `reports/phase39_strategy1_2_discovery_and_promotion_report.md` — Verdict updated to PROVISIONAL
- `project_memory/CURRENT_HANDOFF.md` — Strategy #1.2 status updated to PROVISIONAL
- `project_memory/MASTER_PROJECT_STATE.md` — Updated
- `project_memory/BENCHMARK_REGISTRY.csv` — Status updated to PROVISIONAL
- `project_memory/OPEN_PROBLEMS.md` — Stress harness repair added as open problem
- `project_memory/NEXT_PHASE_PLAN.md` — Updated to require stress harness repair

---

## 7. Is Strategy #1.2 Promoted, Provisional, or Demoted?

**PROVISIONAL** — Option C.

- Metrics reconcile ✅
- Construction is valid ✅  
- Promotion gates not fully passed ❌ (stress gate fails)
- Stress model requires repair before durable pass verdict

Strategy #1 and #1.1 remain protected and unchanged.

---

## 8. What Should Phase 40 Do?

1. **Repair the stress harness** — scale fees/slippage by notional (size × price) per trade  
2. **Rerun stress on Strategy #1, #1.1, and #1.2** with corrected harness  
3. **Re-evaluate promotion gates** for P39_CAND_0551 using corrected stress results  
4. **If stress pass count reaches 10/15** → Strategy #1.2 is confirmed promoted  
5. **If stress pass count stays at 8/15** → demote to RESEARCH_ONLY  
6. Do NOT proceed to shadow execution until stress harness repair is complete

---

## Files Generated This Phase

| File | Purpose |
|---|---|
| phase39_1_sync_and_safety_audit.csv | Git sync verification |
| phase39_1_metric_source_inventory.csv | All metric sources mapped |
| phase39_1_p39_cand_0551_recomputed_metrics.csv | Trade-log ground truth |
| phase39_1_metric_conflict_reconciliation.csv | Set A vs Set B resolution |
| phase39_1_promotion_gate_audit.csv | Track A/B/C/D gate checks |
| phase39_1_candidate_construction_audit.md | Live-known classification |
| phase39_1_stress_harness_audit.md | Stress model assessment |
| phase39_1_stress_recomputed_if_needed.csv | Recomputed stress scenarios |
| phase39_1_integrity_audit.csv | Lookahead/hardcoding audit |
| phase39_1_strategy1_2_final_decision.md | Final decision document |
| phase39_1_strategy1_2_truth_reconciliation_report.md | This main report |
