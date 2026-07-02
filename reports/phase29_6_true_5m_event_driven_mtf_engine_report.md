# Phase 29.6 True 5m Event-Driven MTF Engine Report

## Executive Verdict

Final verdict: `PF12_MTF_ENGINE_MAJOR_PROGRESS_BUT_NOT_RECOVERED`.

The 5m event-driven engine was built and produced a real PF1.2 MTF trade log from live-known setup, trigger, fill, and exit rules. It did not exactly recover the PF1.2 teacher benchmark. The result is a reproducible engineering advance, not a new locked benchmark.

## Execution Rule Recovery

Recovered rule rows: 31. The old files did contain useful execution rules: closed-candle operation, ATR stop/target, SL-first same-candle ambiguity handling, breakeven after favorable movement, time stop, funding filters, fee/slippage assumptions, tick/step rounding, and reduce-only exit concepts.

Conflicts found: Phase 28 text says BTC tick 0.01, while the current engine family has used coarser BTC rounding. Phase 29.6 documents that and uses deterministic local rounding without claiming exchange parity.

## MTF Alignment

Dataset audit:

| Timeframe | Rows | Status | Start | End |
| --- | ---: | --- | --- | --- |
| 1h | 56929 | PASS | 2020-01-01 00:00:00+00:00 | 2026-06-30 00:00:00+00:00 |
| 15m | 227521 | PASS | 2020-01-01 00:00:00+00:00 | 2026-06-28 00:00:00+00:00 |
| 5m | 682561 | PASS | 2020-01-01 00:00:00+00:00 | 2026-06-28 00:00:00+00:00 |

Every emitted PF1.2 trade records setup close, trigger, entry, and exit timestamps. Tests verify setup close precedes the trigger, entry is at or after trigger close, and exit is at or after entry.

## Engine Design

The engine runs:

`1h setup close -> 5m trigger window -> 5m entry/fill -> 5m SL/TP/path simulation -> final trade log`.

It supports market-next-open, limit retest, VWAP reclaim, wick rejection, second retest, breakeven, trailing ATR, time stop, missed fill stress, stale cancel stress, partial-fill stress, and deterministic router conflicts.

## PF1.2 MTF Retest

Best PF1.2 event-driven row:

| Metric | Value |
| --- | ---: |
| Net PnL | -9940.72 |
| Trades | 3111 |
| PF | 0.64 |
| Max DD % | 99.41 |
| Combined adverse | -24422.06 |
| Teacher time/side matches | 1 |

This is closer to the actual execution question because the lower-timeframe path now controls entries and exits. It is still not exact PF1.2 executable recovery.

## PF7/PF8/PF8.1 Sleeve Retest

Best PF8-family event-driven row:

| Metric | Value |
| --- | ---: |
| Net PnL | -9945.87 |
| Trades | 2468 |
| PF | 0.45 |
| Max DD % | 99.46 |
| Combined adverse | -19849.76 |

The old forced PF7/PF8/PF8.1 metrics remain invalid. The sleeves tested here are real event-driven hypotheses.

## Final Answers

1. Old execution rules recovered: closed-candle entries, ATR SL/TP, SL-first same-candle priority, breakeven, trailing/time-stop concepts, funding filters, fee/slippage settings, rounding, reduce-only concept, and shadow-only status.
2. The old files contained useful entry/exit/TP/SL logic, but not a hidden exact PF1.2 live router.
3. The 5m event-driven engine is working and emits auditable setup/trigger/entry/exit traces.
4. The alignment tests confirm no trigger occurs before setup close.
5. Variant C was retested under true 5m execution; see `phase29_6_variant_c_mtf_engine_results.csv`.
6. Variant B rescue was retested under true 5m execution; see `phase29_6_variant_b_mtf_engine_results.csv`.
7. PF1.2 did not exactly recover to the teacher benchmark.
8. PF7/PF8/PF8.1 ideas are stronger as testable sleeves than report metrics, but they are still research-only.
9. The best real engine-generated system is recorded in `phase29_6_pf8_sleeve_results.csv` and `phase29_6_benchmark`-style rows inside the report files.
10. The remaining gap is exact routing lineage: which live-known trigger/exit parameters reproduce the teacher entries without completed-trade transformations.

Next phase should use the 29.6 trace log to compare teacher entries against the exact 5m trigger and exit path, then optimize only live-known trigger timing and exit parameters.
