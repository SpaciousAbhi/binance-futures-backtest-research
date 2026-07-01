# Phase 22 Research Report - 10k Research & Multi-Asset Validation

## 1. Verdict

> [!IMPORTANT]
> **VERDICT: PARTIAL_PASS_REAL_SEARCH_EXPANDED_NO_STRATEGY_UPGRADE**
> **BENCHMARK OUTCOME: PRECISION_FUSION_1_2_RETAINED — NO SAFE IMPROVEMENT FOUND**
> **STATUS: LIVE_RULES_SERIALIZED_STRATEGY_BENCHMARK_VALIDATED**
> **NOT YET READY FOR REAL-CAPITAL LIVE AUTOMATION**
>
> - Candidate registry: **10,150 candidates** generated and logged.
> - Static audit: **10,150 passed / 0 rejected**.
> - Cheap scan: **125 passed / 10,025 rejected**.
> - Full backtests: **125 run / 0 accepted**.
> - Multi-asset proof: ETH, BNB, and SOL validated as **DATA_MISSING_PROVEN_BY_FILE_SCAN**.

---

## 2. Precision Fusion 1.2 Truth Lock

| Field | Value |
|---|---|
| PnL | **$21,684.99** |
| Trades | **325** |
| Profit Factor | **2.42** |
| Drawdown | **10.87%** |
| Combined Adverse Stress | **$15,922.97** |
| Trade Log Hash | `429dcb08a667976e` |
| Monthly Table Hash | `2d8aa4bbff707a09` |
| Data Hash | `64fa11db1bb59ade` |

---

## 3. Data Discovery & Multi-Asset Proof

- Scanned directories: `data/, data/processed/, data/raw/`
- Matching files found: `BTCUSDT_15m_processed.csv, BTCUSDT_1h_processed.csv, BTCUSDT_5m_processed.csv`

| Asset | Status | PnL | Trades | PF | DD |
|---|---|---|---|---|---|
| BTCUSDT | VALIDATED | $21684.99 | 325 | 2.4184 | 10.87% |
| ETHUSDT | DATA_MISSING_PROVEN_BY_FILE_SCAN | $0.00 | 0 | 0.0000 | 0.00% |
| BNBUSDT | DATA_MISSING_PROVEN_BY_FILE_SCAN | $0.00 | 0 | 0.0000 | 0.00% |
| SOLUSDT | DATA_MISSING_PROVEN_BY_FILE_SCAN | $0.00 | 0 | 0.0000 | 0.00% |

---

## 4. Search Funnel Stats

| Stage | Input Count | Output Count | Rejections / Capped | Duration |
|---|---|---|---|---|
| Registry Generation | — | 10,150 | 0 | 0.59s |
| Static Audit | 10,150 | 10,150 | 0 | 0.118s |
| Cheap Scan | 10,150 | 125 | 10,025 | 2163.976s |
| Full Backtest | 125 | 0 | Capped at 200 (ranked) / 125 failed | 142.408s |

---

## 5. Loss Bucket Analysis

| bucket_name | num_trades | total_pnl_damage | avg_R | month_contribution | repairable_live | live_known_feature_fix |
| --- | --- | --- | --- | --- | --- | --- |
| false_breakout | 30 | -4249.6500 | -1.0170 | 2020-06|2020-10|2020-11 | YES | volume_confirm |
| funding_drag | 25 | -2917.5700 | -1.0242 | 2020-01|2020-02|2020-04 | YES | funding_extreme_skip |
| trend_whipsaw | 12 | -1580.0800 | -1.0203 | 2020-02|2020-03|2020-06 | PARTIAL | volume_confirm |
| weak_continuation | 46 | -6540.7400 | -1.0197 | 2020-03|2020-05|2020-08 | PARTIAL | volume_confirm |

---

## 6. AI-Designed Families cheap scan / backtest results

| family | generated | cheap_pass | full_backtested | accepted |
| --- | --- | --- | --- | --- |
| false_breakout_rsi_filter | 350 | 0 | 0 | 0 |
| false_breakout_volume_confirm | 350 | 0 | 0 | 0 |
| chop_adx_compression_filter | 350 | 0 | 0 | 0 |
| chop_ema_slope_filter | 350 | 25 | 25 | 0 |
| whipsaw_double_retest_confirm | 350 | 0 | 0 | 0 |
| whipsaw_atr_expansion_gate | 350 | 0 | 0 | 0 |
| funding_drag_momentum_align | 350 | 0 | 0 | 0 |
| funding_drag_extreme_skip | 350 | 0 | 0 | 0 |
| weak_continuation_time_stop | 350 | 25 | 25 | 0 |
| weak_continuation_trailing_be | 350 | 25 | 25 | 0 |
| time_decay_session_exit | 350 | 0 | 0 | 0 |
| time_decay_weekend_flat | 350 | 0 | 0 | 0 |
| zero_month_inactivity_rescue | 350 | 0 | 0 | 0 |
| zero_month_low_activity_setup | 350 | 0 | 0 | 0 |
| retest_wick_rejection_only | 350 | 0 | 0 | 0 |
| retest_body_close_confirm | 350 | 0 | 0 | 0 |
| overextended_atr_distance_cap | 350 | 0 | 0 | 0 |
| session_liquidity_sweep_reclaim | 350 | 0 | 0 | 0 |
| compression_bb_squeeze_trigger | 350 | 0 | 0 | 0 |
| post_funding_volatility_cooldown | 350 | 0 | 0 | 0 |

---

## 7. 15 Stress Scenarios for Precision Fusion 1.2

| Scenario | PnL | PF | DD | Trades | Pos/Neg/Zero Months | Verdict |
|---|---|---|---|---|---|---|
| normal | $21684.99 | 2.4184 | 10.87% | 325 | 56/16/6 | PASS |
| double_fees | $19668.94 | 2.2397 | 12.94% | 325 | 56/16/6 | PASS |
| triple_fees | $17652.90 | 2.0735 | 15.06% | 325 | 56/16/6 | PASS |
| double_slippage | $19668.79 | 2.2397 | 12.94% | 325 | 56/16/6 | PASS |
| triple_slippage | $17652.60 | 2.0735 | 15.06% | 325 | 56/16/6 | PASS |
| double_fees_double_slippage | $17652.75 | 2.0735 | 15.06% | 325 | 56/16/6 | PASS |
| delay_1_candle | $21969.16 | 2.4475 | 10.36% | 325 | 56/16/6 | PASS |
| delay_2_candles | $22253.33 | 2.4770 | 9.85% | 325 | 56/16/6 | PASS |
| missed_fills_10 | $19350.89 | 2.4189 | 3.16% | 292 | 55/15/8 | PASS |
| missed_fills_20 | $16624.58 | 2.3467 | 3.16% | 260 | 52/16/10 | PASS |
| missed_fills_30 | $14897.10 | 2.4013 | 3.16% | 227 | 50/16/12 | PASS |
| combined_adverse | $15922.97 | 2.0906 | 3.71% | 292 | 55/15/8 | PASS |
| combined_adverse_passive | $17184.29 | 2.1659 | 3.57% | 299 | 57/15/6 | PASS |
| combined_adverse_high_funding | $15922.97 | 2.0906 | 3.71% | 292 | 55/15/8 | PASS |
| combined_adverse_stale_cancel | $13756.92 | 2.0444 | 3.64% | 260 | 52/16/10 | PASS |

---

## 8. Proof File Manifest

| File | Hash | Rows / Size |
|---|---|---|
| phase22_candidate_registry.csv | `233960ecf02ce92a` | 10,150 |
| phase22_candidate_results.csv | `e6a5016f5090b5e5` | 125 |
| phase22_stage_rejections.csv | `3cd17cf5869ad0d3` | 10,025 |
| phase22_runtime_log.json | `2a76e5d92af0218e` | — |
| phase22_mechanism_dataset.csv | `ed580640df49ba1b` | 325 |
| phase22_loss_bucket_report.csv | `bc4cab705588d390` | 4 |
| phase22_multi_asset_results.csv | `d35776fa7a795eca` | 4 |
| phase22_top_100_candidates.md | `PENDING` | — |
| phase22_audit_manifest.json | `C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\reports\phase22_audit_manifest.json` | — |

---

## 9. Runtime Plausibility Check

- Total runtime: 2342.327 seconds
- MP Cheap scan rate: 0.2132 seconds/candidate
- Full backtest rate: 1.1393 seconds/candidate
- All processes mapped using preloaded global variables on 12-core Windows executor.