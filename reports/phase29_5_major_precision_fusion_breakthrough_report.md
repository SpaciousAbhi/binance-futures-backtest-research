# Phase 29.5 Major Precision Fusion Breakthrough Report

**FINAL VERDICT: PF12_MAJOR_MTF_RECOVERY_PROGRESS_PF8_RESEARCH_CONTINUES**

PF means Precision Fusion: a live-known router over candidate sleeves, filters, rescue layers, and risk controls. Phase 29.5 used Antigravity BTC 15m/5m data for recovery evidence, but accepted metrics only from engine-executed strategies.

## Local Evidence Re-Scan

Evidence rows mapped: 716. Antigravity provided useful 15m/5m data and lower-timeframe research artifacts, but still no hidden exact PF1.2 executable router.

## MTF Data Alignment

MTF audit status rows are saved in `phase29_5_mtf_data_alignment_audit.csv`. The cross-timeframe rule is: setup candle closes first, then lower-timeframe trigger windows start at or after the setup close. Engine MTF gates only use lower-timeframe candles inside already-closed 1h setup candles.

## PF1.2 Teacher-to-MTF Trigger Match

Trigger category counts: `{'exact_live_trigger_found': 321, 'nearby_trigger_found': 4}`. These categories explain teacher rows as research diagnostics only; no teacher row ID or teacher label is used by the live router.

## Variant C MTF Rebuild

Best C MTF rebuild: `c_mtf_trade_count` with PnL 4198.29, trades 199, PF 1.35, DD 6.60%, teacher time/side match 26.10%.

## Variant B Rescue MTF Rebuild

Best B rescue MTF rebuild: `b_rescue_mtf_vwap` with PnL 3467.68, trades 243, PF 1.25, DD 11.38%, teacher time/side match 26.68%.

## PF1.2 Executable Router Recovery

PF1.2 MTF router status: `PARTIAL_RECOVERY`.

| Metric | PF1.2 teacher target | Best Phase 29.5 PF1.2 MTF router |
|---|---:|---:|
| PnL | 21684.99 | 3737.24 |
| Trades | 325 | 278 |
| PF | 2.42 | 1.22 |
| DD % | 10.87 | 12.07 |
| Stress | 15922.97 | -202.57 |
| Teacher time/side match | 100.00% | 28.00% |

This is not exact PF1.2 executable proof unless `pf12_recovery_status` is `EXACT_MATCH`.

## Dirty PF8 Upgrade

Dirty PF8 remains diagnostic. Rows in `phase29_5_dirty_pf8_upgrade_results.csv` show baseline, MTF diagnostic filtering, and the best engine-executed recovered PF8/PF8.1 candidate where available.

## Large Candidate Search

- Registered candidates: 5000
- Engine-executed candidates: 300
- Execution limit: 300
- Best engine candidate: P295_00045 / second_retest / PnL -487.68 / trades 2333 / PF 0.48
- Unexecuted candidates have blank metrics by design.

## Benchmark Stack

The stack comparison is saved in `phase29_5_benchmark_stack_comparison.csv`. Any system marked `TEACHER_REFERENCE` is not an executable live proof.

## Final Answers

- PF1.2 executable recovery got to PnL 3737.24, 278 trades, PF 1.22, status `PARTIAL_RECOVERY`.
- MTF triggers explain a subset of teacher trades, but they do not fully regenerate the teacher set.
- Variant C and B now have live-known MTF rebuild candidates, but neither exactly reproduces the teacher set.
- Dirty PF8 quality improved only as diagnostics unless an engine-executed candidate row beats the teacher target.
- No real router beats the PF1.2 teacher unless `beats_pf12_teacher=YES` in `phase29_5_candidate_results.csv`.
- Next step: build a true event-driven 5m execution engine so 1h setup plus post-close 5m trigger entries can be backtested without compressing trigger evidence into 1h rows.

## Live Status

NOT_REAL_CAPITAL_READY. No exchange-level shadow proof exists.
