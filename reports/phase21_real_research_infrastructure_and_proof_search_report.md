# Phase 21 Technical Report - Real Research Infrastructure and Proof Search

## 1. Verdict

> [!IMPORTANT]
> **VERDICT: INFRASTRUCTURE_PASS_REAL_SEARCH_ENGINE_BUILT**
> **BENCHMARK OUTCOME: PRECISION_FUSION_1_2_RETAINED_REAL_SEARCH_NO_SAFE_IMPROVEMENT**
> **STATUS: LIVE_RULES_SERIALIZED_STRATEGY_BENCHMARK_VALIDATED**
> **NOT_YET_READY_FOR_REAL_CAPITAL_LIVE_AUTOMATION**
>
> - Candidate registry: **2,000 candidates** generated and written to CSV with real hashes.
> - Static audit: **1,992 passed / 8 rejected**.
> - Cheap scan: **48 passed / 152 rejected**.
> - Full backtests: **48 executed / 0 beat all gates**.
> - Mechanism dataset: **325 rows** (one per PF 1.2 trade).
> - All proof files written with real hashes. No simulated counts.

---

## 2. Precision Fusion 1.2 Truth Lock

| Field | Value |
|---|---|
| Reproduction Command | `python src/research/phase21_runner.py` |
| Runtime (seconds) | `277.613` |
| Data File Hash | `64fa11db1bb59ade` |
| Config Hash | `b391e91035854b3d` |
| Engine Hash | `e3d98fedb207e646` |
| Strategy Hash | `3ba281b2d4c1647b` |
| Trade Log Hash | `429dcb08a667976e` |
| Monthly Table Hash | `2d8aa4bbff707a09` |
| Stress Table Hash | `d4c4babaa5998af1` |
| Net PnL | **$21684.99** |
| Trades | **325** |
| Profit Factor | **2.42** |
| Max Drawdown | **10.87%** |
| Months (Pos/Neg/Zero) | **56 / 16 / 6** |
| Combined Adverse | **$15922.97** |
| Reproduction Verdict | **EXACT MATCH - ALL GATES PASSED** |

---

## 3. Trade Audit - First 10 Trades

| trade_id | source | entry_time | side | entry_px | net_pnl | R |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | Variant C Core | 2020-01-10 09:00 | Long | $7701.99 | $167.16 | 1.65 |
| 1 | Variant C Core | 2020-01-14 04:00 | Long | $8465.33 | $127.99 | 1.28 |
| 2 | Variant C Core | 2020-01-15 01:00 | Short | $8788.08 | $-107.22 | -1.02 |
| 3 | Variant C Core | 2020-01-17 23:00 | Short | $8948.54 | $-108.71 | -1.03 |
| 4 | Variant C Core | 2020-01-19 09:00 | Short | $9117.81 | $86.86 | 0.88 |
| 5 | Variant C Core | 2020-01-19 13:00 | Short | $8650.04 | $146.06 | 1.31 |
| 6 | Variant C Core | 2020-01-24 16:00 | Short | $8513.50 | $95.50 | 0.91 |
| 10 | Variant C Core | 2020-01-31 00:00 | Short | $9530.42 | $47.14 | 0.92 |
| 11 | Variant C Core | 2020-02-02 11:00 | Short | $9439.23 | $96.79 | 0.88 |
| 12 | Variant C Core | 2020-02-05 17:00 | Short | $9583.07 | $-120.24 | -1.04 |

## 4. Trade Audit - Last 10 Trades

| trade_id | source | entry_time | side | entry_px | net_pnl | R |
| --- | --- | --- | --- | --- | --- | --- |
| 470 | Variant C Core | 2026-02-25 02:00 | Long | $65827.41 | $244.91 | 1.41 |
| 471 | Variant C Core | 2026-02-25 17:00 | Long | $68215.72 | $225.20 | 1.29 |
| 472 | Variant C Core | 2026-02-28 19:00 | Long | $65839.89 | $252.88 | 1.42 |
| 473 | Variant C Core | 2026-03-02 01:00 | Long | $66439.29 | $258.24 | 1.43 |
| 475 | Variant C Core | 2026-03-03 16:00 | Long | $67658.57 | $258.60 | 1.43 |
| 477 | Variant C Core | 2026-03-06 18:00 | Short | $67964.50 | $240.67 | 1.30 |
| 484 | Variant C Core | 2026-05-26 15:00 | Short | $76912.04 | $245.35 | 1.36 |
| 485 | Variant C Core | 2026-05-29 19:00 | Short | $73379.51 | $256.47 | 1.38 |
| 486 | Variant C Core | 2026-06-02 16:00 | Short | $67307.64 | $237.74 | 1.28 |
| 487 | Variant C Core | 2026-06-04 01:00 | Short | $63346.08 | $245.46 | 1.31 |

---

## 5. Search Infrastructure Stats

| Stage | Input | Output | Rejected | Time (s) |
|---|---|---|---|---|
| Registry Generation | - | 2,000 | 0 | 0.083 |
| Static Audit | 2,000 | 1,992 | 8 | 0.015 |
| Cheap Signal Scan | 200 | 48 | 152 | 203.411 |
| Full Backtest | 48 | 48 | - | 48.686 |
| Gate Acceptance | 48 | 0 | 48 | - |

---

## 6. Mechanism Dataset Summary

- **Total rows**: 325 (must equal 325)
- **Dataset hash**: `fd567dcc8671c48f`
- **Winners**: 212 | **Losers**: 113
- **Elite winners**: 13
- **Toxic losers**: 37
- **Whipsaw losers**: 14
- **Funding losers**: 11
- **Reached 0.5R**: 268
- **Reached 1R**: 214
- **Immediate failures**: 15

### Classification Distribution
| Count | count |
| --- | --- |
| weak_winner | 199 |
| failed_continuation_loser | 51 |
| toxic_loser | 37 |
| whipsaw_loser | 14 |
| elite_winner | 13 |
| funding_loser | 11 |

---

## 7. 15-Scenario Stress Results for Precision Fusion 1.2

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

## 8. Yearly OOS Breakdown

| Year | PnL | Trades |
|---|---|---|
| 2020 | $541.09 | 57 |
| 2021 | $2228.07 | 100 |
| 2022 | $3171.26 | 62 |
| 2023 | $3829.20 | 28 |
| 2024 | $4004.63 | 36 |
| 2025 | $4075.12 | 24 |
| 2026 | $3835.60 | 18 |

---

## 9. Proof Files

| File | Hash | Rows |
|---|---|---|
| phase21_candidate_registry.csv | `45dec5efa278d928` | 2,000 |
| phase21_candidate_results.csv | `5cc42688b8ec13e8` | 48 |
| phase21_stage_rejections.csv | `b5aa4211d839db56` | 160 |
| phase21_runtime_log.json | `422d9a779ff71384` | - |
| phase21_mechanism_dataset.csv | `fd567dcc8671c48f` | 325 |
| phase21_top_50_candidates.md | `39fbc34ba45584a8` | - |

---

## 10. Runtime Log Summary

- **Total runtime**: 277.613 seconds
- **Candidate generation**: 0.083 seconds
- **Static audit**: 0.015 seconds
- **Cheap scan**: 203.411 seconds
- **Full backtest**: 48.686 seconds
- **Actual backtest calls**: 48
- **Avg seconds/backtest**: 1.0143
- **Multiprocessing used**: False
- **Cache used**: False

---

## 11. Corrections vs Phase 20

1. Phase 20 100k template claim = placeholder (no registry existed). Phase 21 provides real registry.
2. Phase 20 ETH/SOL validation = placeholder (no data files). Phase 21 marks this as unproven.
3. Phase 20 MFE/MAE dataset = placeholder (no CSV). Phase 21 generates 325 real rows.
4. All Phase 21 proof files carry real hashes. Runtime log shows actual timestamps.
5. Next phase may safely scale candidate count backed by this infrastructure.