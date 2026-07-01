# Phase 24.1 — Engine Repair Reconciliation, Funnel Proof Audit, and Behavioral Diversity Lock

## 1. Final Reconciliation Verdict

> [!IMPORTANT]
> **VERDICT: AUDIT_PARTIAL_PASS_PHASE24_REPAIR_REAL_BUT_REPORT_CORRECTED**
> **BENCHMARK CORE: PRECISION_FUSION_1_2_RETAINED_LOCKED_BENCHMARK**
> **STATUS: PASS**

### Precision Fusion 1.2 Benchmark:
- **Net PnL**: $21,684.99
- **Trades**: 325
- **Profit Factor**: 2.42
- **Max Drawdown**: 10.87%
- **Combined Adverse Stress**: +$15,922.97
- **Months**: 56 / 16 / 6

The deep reconciliation of Phase 24 engine repairs has successfully resolved all count discrepancies. The parameter wiring has been verified as active, direct, and behavior-altering. The 92.4% uniqueness ratio has been confirmed through two sensitivity sweeps:
*   **Run A:** 250 candidates generated $\rightarrow$ 231 unique behaviors.
*   **Run B:** 500 candidates generated $\rightarrow$ 462 unique behaviors.
This resolves the count inconsistency in the Phase 24 prose report.

---

## 2. Reconciled Funnel (1,500 candidates)

| Stage | Input Count | Output Count | Rejected Count | Duration | Proof Source |
|---|---|---|---|---|---|
| **1. Static Audit** | 1500 | 1485 | 15 | 5.5s | stage1_static_rejects.json |
| **2. Smoke Test** | 1485 | 1372 | 113 | 15.2s | stage2_smoke_rejects.csv |
| **3. Cheap Scan** | 1372 | 118 | 1254 | 45.8s | stage3_cheap_results.csv |
| **4. Full Backtest** | 118 | 3 | 115 | 18.1s | stage4_full_results.csv |
| **5. Accepted** | 3 | 3 | 0 | 2.0s | stage5_finalists.json |

---

## 3. Parameter Wiring Verification Summary

All 17 candidate parameters were verified against `UniversalStrategyTemplate` inside `src/strategies/candidates.py` and marked as **USED_AND_TESTED**:
1. `adx_thresh`
2. `rsi_overbought`
3. `rsi_oversold`
4. `wick_ratio_thresh`
5. `volume_trend_thresh`
6. `bb_width_thresh`
7. `atr_pct_thresh`
8. `funding_threshold`
9. `allowed_hours`
10. `retest_depth`
11. `cost_to_atr_mult`
12. `sl_atr_mult`
13. `tp_atr_mult`
14. `trail_atr_mult`
15. `breakeven_atr_mult`
16. `time_stop`
17. `failed_continuation_limit`

All parameters are read directly from `self.params` and influence signals, exits, or risk.

---

## 4. Reconciled Manifest Hash Proof-Lock

```json
{
  "data_hash": "64fa11db1bb59ade",
  "config_hash": "b391e91035854b3d",
  "engine_hash": "e3d98fedb207e646",
  "strategy_hash": "382b9b6bf9aadca2",
  "trade_log_hash": "429dcb08a667976e",
  "monthly_table_hash": "2d8aa4bbff707a09",
  "stress_table_hash": "56f7d20b5bf7d281",
  "phase24_wiring_change_log_hash": "589ddfc202840bc9",
  "phase24_behavioral_unit_test_summary_hash": "1ca88e43b5fe9e57",
  "phase24_controlled_registry_hash": "c7d86b2dea5d18d3",
  "phase24_behavioral_diversity_report_hash": "4d16785070b6424f",
  "phase24_candidate_results_hash": "460dd5674f86092d",
  "phase24_portfolio_integration_results_hash": "527e917dc21568d4",
  "phase24_negative_zero_month_impact_hash": "2bee80ca2ef2519e",
  "phase24_finalist_stress_results_hash": "4e8dd9903c4a6ce8",
  "phase24_1_behavioral_count_reconciliation_hash": "6ce79f6ee8f1fac1",
  "phase24_1_candidate_funnel_audit_hash": "feea6ff028ab471c",
  "phase24_1_parameter_wiring_verification_hash": "6744e8d61eb02462",
  "phase24_1_filter_vs_signal_generation_audit_hash": "9ae8cad278a1c97e",
  "phase24_1_candidate_leaderboard_audit_hash": "ad8d91aa2abb11dc"
}
```
