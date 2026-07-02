# Phase 29.2 Precision Fusion Truth Reconstruction Report

## Executive Verdict

**FINAL VERDICT: PF12_TRADESET_RECONSTRUCTED_BUT_EXECUTABLE_FUSION_NOT_PROVEN**

PF means Precision Fusion: a router/fusion of strategy sleeves, filters, exits, and risk rules. Phase 29.2 found that PF1.2 has an exact protected reconstructed trade set, but the exact PF1.2 protected benchmark is not proven as a saved executable Precision Fusion router.

## 1. Is PF1.2 Real Executable Precision Fusion Or Only A Reconstructed Trade Set?

Current status: **PF12_TRADESET_RECONSTRUCTED_BUT_EXECUTABLE_FUSION_NOT_PROVEN**.

The executable floor fusion is `build_p10_1_strategy()`, but it does not reproduce the protected PF1.2 metrics. The protected PF1.2 metrics come from `reconstruct_pf12()`, which replays Variant C plus B rescue rows from completed trade logs.

## 2. PF1.2 Protected Metrics Vs Executable Floor

| Metric | Protected PF1.2 reconstructed | Executable floor fusion |
|---|---:|---:|
| Net PnL | 21684.99 | 8426.09 |
| Trades | 325 | 490 |
| Profit Factor | 2.42 | 1.24 |
| Max DD % | 10.87 | 16.51 |
| Months | 56/16/6 | 48/29/1 |
| Combined adverse | 15922.97 | 163.03 |

## 3. Why The Core Path Differs

The executable floor path evaluates real candle signals. The protected PF1.2 path transforms completed floor trades: it ranks completed trades by net PnL, creates Variant B and C trade frames, adjusts entry prices, and appends B-unique rows filtered by the completed trade `R` column. That explains why the executable floor can show materially weaker metrics while the protected reconstructed trade set shows the locked PF1.2 numbers.

## 4. Dirty PF8

Dirty PF8 no-forcing baseline:

| Metric | Value |
|---|---:|
| Net PnL | 23216.75 |
| Trades | 555 |
| Profit Factor | 1.74 |
| Max DD % | 15.29 |
| Combined adverse | 13281.95 |

Dirty PF8 is not production quality. It is a diagnostic trade frame with useful PnL/activity clues and timestamp/lineage contamination that prevents benchmark promotion.

## 5. Recovery Search

- Registered candidates: 1000
- Engine-executed candidates: 100
- Best recovered router: P292_0016 / vwap_reclaim_variant / PnL 180.75 / trades 3 / PF 15.29 / DD 0.12%

The best recovered router does not override PF1.2 unless it beats PF1.2 through engine-computed trades. Phase 29.2 did not prove that.

## 6. Multi-Timeframe Repair

- BTC 15m availability: YES, use status: AVAILABLE_FOR_FUTURE_CONFIRMATION_NOT_EXECUTED_IN_29_2
- BTC 5m availability: NO, use status: MISSING_NOT_USED

Because BTC 5m is missing locally and the exact PF1.2 executable router is not proven, Phase 29.2 does not claim a completed multi-timeframe PF8.1 repair.

## 7. Final Answers

1. PF1.2 is currently an exact reconstructed trade set, not an exactly proven executable Precision Fusion.
2. The lineage is Variant C reconstructed core plus B rescue rows; see `phase29_2_pf12_fusion_lineage_map.csv`.
3. The core executable path differs because it uses live candle rules, while protected PF1.2 uses completed trade-log reconstruction.
4. The exact protected PF1.2 cannot currently be reproduced from saved fusion rules alone.
5. Dirty PF8 is PF1.2 reconstructed rows plus deterministic added floor-trade material from the no-forcing recompute.
6. Dirty PF8 has useful high-activity diagnostics but toxic and timestamp-shifted rows; see the dirty cluster report.
7. Dirty PF8 was not improved to PF8.1 quality without forcing in this phase.
8. The best real recovered router is recorded in the candidate and recovered-router files.
9. It does not beat PF1.2 unless `beats_pf12` says YES in `phase29_2_candidate_results.csv`.
10. The exact gap is saved in `phase29_2_pf12_trade_diff_audit.csv`.
11. Phase 29.3 should rebuild PF1.2 from first-principles live-known rules, starting with Variant C and B rescue signals as real strategies rather than completed-trade transformations.

## Required Proof Files

All required Phase 29.2 files are listed and hashed in `phase29_2_audit_manifest.json`.
