# Phase 29.3 Precision Fusion Lineage Recovery and PF8 Rebuild Report

**FINAL VERDICT: PF12_PARTIAL_EXECUTABLE_REBUILD_REQUIRES_MORE_RECOVERY**

PF means Precision Fusion: a router of candidates, sleeves, filters, rescue layers, and risk rules. This phase is recovery-focused: it preserves old B/C/PF1.2 work as teacher evidence while rebuilding live-known executable approximations through the engine.

## Phase 1 to Phase 29 Historical Recovery Map

| Phase Area | Claim / Workstream | Current Recovery Classification | Evidence |
|---|---|---|---|
| Phase 10-12 | Fusion-of-fusions floor using A/C/D/F/G candidates | Real executable floor, but not PF1.2 exact | `src/research/phase12_runner.py` |
| Phase 17.3 | Variant B, Variant C, PF1.2 B/C fusion | Reconstructed teacher trade sets; useful but not live-executable proof | `src/research/phase17_3_runner.py` |
| Phase 18-24 | Repair/search attempts around PF1.2 | Mostly research infrastructure and report comparisons | phase reports/tests |
| Phase 21-22 | Candidate registries and mechanism dataset | Real registry infrastructure; PF1.2 still reconstructed | `phase21_candidate_registry.csv` |
| Phase 25-28 | PF7/PF8/PF8.1 growth claims | Invalid as benchmarks because forced/synthetic metrics appear | Phase 29 audits |
| Phase 29-29.2 | Truth reset | PF1.2 exact as trade-set; executable exact fusion not proven | Phase 29.2 proof files |


## Variant B Recovery

Variant B first appears as the consistency benchmark in the Phase 17.3 B/C fusion repair path. The protected B result is a reconstructed teacher trade set, not a saved live executable strategy.

| Metric | Protected B teacher | Live-known B proxy |
|---|---:|---:|
| PnL | 19589.91 | 2663.80 |
| Trades | 416 | 336 |
| PF | 1.92 | 1.13 |
| DD % | 12.20 | 9.35 |
| Stress | 14242.71 | -1729.31 |

## Variant C Recovery

Variant C was the quality core teacher set. The live-known proxy uses the C candidate config from Phase 12, but it does not exactly regenerate the reconstructed C teacher rows.

| Metric | Protected C teacher | Live-known C proxy |
|---|---:|---:|
| PnL | 20455.48 | 3032.90 |
| Trades | 318 | 253 |
| PF | 2.34 | 1.20 |
| DD % | 10.87 | 11.20 |
| Stress | 15550.45 | 806.34 |

## How Variant C + Variant B Became PF1.2

The recovered source trail shows Variant C as the 318-trade quality teacher set. PF1.2 then adds a small B-rescue overlay selected from B-unique teacher rows. The historical implementation used completed trade transformations and completed trade `R`, so it is teacher evidence rather than live-safe executable proof.

## PF1.2 Executable Fusion Rebuild

Status: `PF12_PARTIAL_EXECUTABLE_REBUILD_REQUIRES_MORE_RECOVERY`.

| Metric | Protected PF1.2 teacher | Rebuilt executable PF1.2 |
|---|---:|---:|
| PnL | 21684.99 | 5052.75 |
| Trades | 325 | 250 |
| PF | 2.42 | 1.32 |
| DD % | 10.87 | 6.40 |
| Stress | 15922.97 | 1119.19 |

## Why $8426 vs $21684 Happens

The executable floor path evaluates live candle signals and accepts 490 raw engine trades. The protected PF1.2 teacher path removes many completed low-quality floor trades, reconstructs Variant B and C from completed trade logs, shifts entries, and adds only a small B-rescue set. That selection uses information available only after trade completion, so it explains the quality jump but cannot be used directly in live routing.

## Dirty PF8 Surgery

Dirty PF8 is retained as research material only. It is audited trade by trade in `phase29_3_dirty_pf8_quality_surgery.csv`. The goal is to learn live-known filters, not to remove historical losing rows by hindsight.

## Real PF7/PF8/PF8.1 Recovery Attempt

Registered candidates: 1000. Engine-executed candidates: 100. Best engine-executed recovery attempt: P292_0016 / vwap_reclaim_variant / PnL 180.75 / trades 3 / PF 15.29. It does not supersede protected PF1.2 unless the candidate table says `beats_pf12=YES`.

## Multi-Timeframe Recovery

BTC 5m availability: NO. If missing, 5m trigger proof remains blocked. BTC 15m is audited in the multi-timeframe table and can be used in a later rebuild.

## What Was Reusable vs Not Live-Safe

Reusable: closed-candle candidate configs, FusionOfFusions routing concepts, expected-R gates, session/funding filters, VWAP/retest/breakout sleeves, deterministic compiler outputs.

Not live-safe as strategy logic: completed trade PnL ranking, completed trade `R` selection, synthetic entry shifting, report-only PF7/PF8/PF8.1 constants, and any forced metric assignment.

## Phase 29.4 Work

Rebuild Variant C and B rescue from first-principles candle features instead of teacher trade transformations. Use BTC 15m confirmation where available, regenerate BTC 5m if the downloader supports it, and train live-known filters against teacher clusters without using outcome labels in the final router.
