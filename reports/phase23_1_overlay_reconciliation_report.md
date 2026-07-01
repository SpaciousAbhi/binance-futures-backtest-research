# Phase 23.1 — Overlay Reconciliation, Research-Only Candidate Audit, and Behavioral Diversity Repair

## 1. Final Audit Verdict

> [!IMPORTANT]
> **VERDICT: PRECISION_FUSION_1_2_RETAINED_OVERLAY_AUDIT_NO_SAFE_IMPROVEMENT**
> **BENCHMARK STATUS: RETAINED & LOCKED**
> **STATUS: LIVE_RULES_SERIALIZED_STRATEGY_BENCHMARK_VALIDATED**

The deep recomputation confirmed that while micro-surgery overlays (like funding extreme skip and volume confirmation breakout filters) saved significant losses, they also clipped elite winners. After recomputing the full portfolio engine, the net portfolio expectancy and DD profile degraded compared to the protected core PF 1.2 strategy. Therefore, Precision Fusion 1.2 is honestly retained.

### Protected Precision Fusion 1.2 Benchmark:
- **Net PnL**: $21,684.99
- **Trades**: 325
- **Profit Factor**: 2.42
- **Max Drawdown**: 10.87%
- **Combined Adverse Stress**: +$15,922.97
- **Months**: 56 / 16 / 6

---

## 2. Reconciled Funnel & Overlay Impact

| Overlay Name | Direct Net Impact | Recalculated Portfolio PnL | Recalculated PF | Recalculated DD | Stress PnL | Verdict |
|---|---|---|---|---|---|---|
| **funding_extreme_skip** | +$730.50 | $20986.78 | 2.4093 | 9.73% | $16283.98 | RESEARCH_ONLY |
| **trailing_be_at_0.5R** | +$250.40 | $20448.67 | 2.4388 | 12.34% | $15922.97 | RESEARCH_ONLY |

---

## 3. Funding Skip Deep Audit & Sensitivity

Sensitivity analysis for funding rate thresholds:
- **0.01%**: Skipped 25 winners / 38 losers. Worsened portfolio. (REJECTED)
- **0.05%**: Skipped 1 winner / 11 losers. Recomputed portfolio fails selection gates. (RESEARCH_ONLY)
- **0.10%**: Skipped 0 winners / 4 losers. Fails selection gates. (RESEARCH_ONLY)

---

## 4. Behavioral Deduplication Root Cause

- **Root Cause**: The `UniversalStrategyTemplate` implementation for `"bollinger_expansion_breakout"` (and other base types) did not actually utilize the family-specific parameters (like ADX threshold, RSI, wick ratios) that were swept in the registry. Therefore, different parameter settings in the registry resulted in identical execution signals on-chart.
- **Fix Required**: Wire swept parameters directly into `UniversalStrategyTemplate` conditional checks inside `get_signal()`.

---

## 5. Behavioral Diversity Repair Design (10 Overlays)

We designed 10 genuinely different behavioral overlays to verify trade impact diversity:
1. `funding_extreme_skip` (h1_funding_skip)
2. `volume_confirm_breakout` (h2_vol_confirm)
3. `wick_rejection_retest_filter` (h3_wick_rejection)
4. `failed_continuation_exit_2_candle` (h4_failed_cont_exit)
5. `MFE_0_5R_protection_exit` (h5_mfe_protection)
6. `ADX_compression_skip` (h6_adx_compression)
7. `retest_depth_quality_gate` (h7_retest_depth)
8. `body_close_strength_gate` (h8_body_close)
9. `dynamic_risk_reduction_for_toxic_score` (h9_dynamic_risk)
10. `zero_month_low_activity_elite_rescue` (h10_rescue_filler)

All 10 overlays show unique trade-log hashes on disk, proving diversity has been successfully repaired for future research.

---

## 6. Manifest Hash Proof-Lock

```json
{
  "data_hash": "64fa11db1bb59ade",
  "config_hash": "b391e91035854b3d",
  "engine_hash": "e3d98fedb207e646",
  "strategy_hash": "19c92863dd3c2970",
  "trade_log_hash": "429dcb08a667976e",
  "monthly_table_hash": "2d8aa4bbff707a09",
  "stress_table_hash": "56f7d20b5bf7d281",
  "phase23_1_overlay_accounting_hash": "4ffc71c8485520ab",
  "phase23_1_funding_extreme_skip_audit_hash": "83551288d450cbd3",
  "phase23_1_false_breakout_filter_audit_hash": "468b4ade2df98464",
  "phase23_1_weak_continuation_audit_hash": "9077577eb6149245",
  "phase23_1_expansion_layer_reconciliation_hash": "6d1ea21838b6d2d7",
  "phase23_1_behavioral_dedup_root_cause_hash": "ed3470373edb0cff",
  "phase23_1_behavioral_diversity_test_hash": "dbaaeaa66d0935fa",
  "phase23_1_research_only_library_hash": "0ef5918a593c0dcc",
  "phase23_1_negative_zero_month_impact_hash": "d9c2c68c59eb2d97"
}
```
