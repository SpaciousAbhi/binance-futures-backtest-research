# Phase 29.4 Precision Fusion Teacher Distillation and Live Recovery Report

**FINAL VERDICT: PF12_PARTIAL_LIVE_RECOVERY_RULES_FOUND**

PF means Precision Fusion: a router of multiple candidates, sleeves, filters, rescue layers, and risk controls. Phase 29.4 used the Antigravity workspace as an additional evidence source and kept teacher labels analysis-only.

## 1. Local Antigravity Evidence

- Antigravity workspace exists: `True`.
- Evidence inventory rows: 715.
- Antigravity-only evidence rows: 14.
- BTC 15m processed in Antigravity: `True`.
- BTC 5m processed in Antigravity: `True`.

The most useful Antigravity evidence was not a hidden exact PF1.2 executable router. It was supporting recovery material: 5m/15m data, Phase 17.3 reports/code, idea-engine descriptions for 15m/5m retest/VWAP confirmation, and prior reports that record the teacher metrics.

## 2. Canonical Teacher Sets

| Teacher | PnL | Trades | PF | DD % | Stress |
|---|---:|---:|---:|---:|---:|
| Variant B | 19589.91 | 416 | 1.92 | 12.20 | 14242.71 |
| Variant C | 20455.48 | 318 | 2.34 | 10.87 | 15550.45 |
| PF1.2 | 21684.99 | 325 | 2.42 | 10.87 | 15922.97 |

These values were recomputed from trade rows, not copied from report text.

## 3. Why Teacher Sets Beat The Executable Floor

The executable floor produced 8426.09 PnL, 490 trades, PF 1.24, and DD 16.51%. The teacher sets are stronger because Phase 17.3 built B/C from completed floor trade logs: completed PnL sorting, row sampling, synthetic entry adjustment, and a B-rescue gate that reads completed trade `R`. Those operations explain the quality jump but cannot be accepted as live entry logic.

## 4. Teacher To Floor Match

The strict exact key test uses entry time, side, and rounded entry price. Because teacher entries were adjusted, exact matches are sparse. The useful lineage evidence is time/side matching, saved in `phase29_4_teacher_vs_floor_diff.csv` and `phase29_4_pf12_trade_match_gap_audit.csv`.

## 5. Entry-Time Features And Distillation

The feature table contains only entry-time fields: session, trend, EMA relation, ATR/Bollinger/RSI/ADX, volume, funding, candle body/wick, and signal expected-R geometry. It deliberately excludes completed trade PnL, completed trade R, MFE/MAE paths, winner labels, month targets, and row IDs as live rules.

Distilled candidate rules:

- `expected_r_signal >= 1.40`
- active London/NY session gate
- `adx >= 18`
- funding defensive skip at `abs(funding_rate) <= 0.00035`
- candle body/wick confirmation
- combined expected-R/session/funding gate

These are still research rules. They are not a proof that the old PF1.2 teacher set was a live executable router.

## 6. Variant C Live Recovery

Best Variant C rebuild: `c_distilled_adx_shape` with PnL 4836.54, trades 248, PF 1.32, DD 6.40%, teacher time/side match 31.76%.

## 7. Variant B Rescue Live Recovery

Best Variant B rescue rebuild: `b_rescue_adx_shape` with PnL 3424.55, trades 331, PF 1.17, DD 7.39%, teacher time/side match 38.70%.

## 8. PF1.2 Live Router Recovery

PF1.2 live router status: `PARTIAL_RECOVERY`.

| Metric | PF1.2 teacher | Phase 29.4 live router |
|---|---:|---:|
| PnL | 21684.99 | 3637.70 |
| Trades | 325 | 136 |
| PF | 2.42 | 1.50 |
| DD % | 10.87 | 5.95 |
| Stress | 15922.97 | 2117.18 |

PF1.2 cannot yet be treated as exactly executable. Phase 29.4 found live-known rules and generated an engine-run router, but it did not regenerate the exact 325 teacher trades and metrics.

## 9. Dirty PF8 Recovery

Dirty PF8 remains diagnostic only. Baseline diagnostic PnL: 23216.74574724609; PF: 1.7370880352027813; status: DIAGNOSTIC_BASELINE_NOT_BENCHMARK. Applying distilled filters to the dirty trade frame is explicitly labeled non-benchmark because Dirty PF8 contains trade-frame surgery and cannot prove live routing by itself.

## 10. Answers Required By Phase 29.4

1. Files that helped recovery: Antigravity Phase 17.3 code/report, 5m/15m data, idea-engine MTF ideas, and prior audit artifacts.
2. Variant B/C are canonical teacher sets reconstructed from floor trades, not currently exact live routers.
3. Teacher sets are stronger because completed-trade transformations selected/shifted better rows.
4. Many teacher rows share floor signal time/side lineage; exact price keys diverge because of adjusted entries.
5. Missing teacher trades are mainly shifted/transformed or selected by teacher-only completed-trade logic.
6. Live-known explanatory features include expected-R geometry, session, funding, ADX, candle shape, and volatility state.
7. Rules distilled are listed in `phase29_4_teacher_distilled_rules.csv`.
8. Variant C got closer as a live-known rebuild but did not match the teacher.
9. Variant B rescue produced live trades but did not recover the old B teacher quality.
10. PF1.2 live router status is `PARTIAL_RECOVERY`.
11. PF1.2 should still be treated as protected teacher evidence, not exactly executable benchmark proof.
12. Dirty PF8 recovery remained research-only.
13. Phase 29.5 should use Antigravity BTC 5m/15m to implement true lower-timeframe trigger sleeves, then walk-forward validate the distilled rules without teacher labels in routing.

## Live Status

NOT_REAL_CAPITAL_READY. No exchange-level shadow/live proof exists.
