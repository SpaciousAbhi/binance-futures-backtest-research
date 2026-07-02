# MASTER PROJECT STATE
## Last Updated: 2026-07-02 (after Phase 31)

---

## Project Goal

Build a **real, live-executable, automated trading strategy** for Binance USD-M futures.
- Primary asset: BTCUSDT
- Validation assets: ETHUSDT, BNBUSDT, SOLUSDT
- Data: Binance API 1h + 15m + 5m OHLCV + funding rates
- Research period: 2020-01-01 to 2026-06-30
- Capital model: $10,000 initial capital, maker fee 0.02%, taker fee 0.05%, slippage 0.05%

**The long-term target is a strategy that:**
- Has positive expected value in live execution (not just backtesting).
- Runs fully automated without manual intervention.
- Passes no-lookahead, no-hardcoding, and no-future-data checks.
- Is funded only when proven consistently profitable over 18+ months.

---

## Current Live Status

> **NOT_REAL_CAPITAL_READY**

No strategy has passed all requirements for real-capital live automation. Do not deploy.

---

## Benchmark Truth Registry

### VALID Benchmarks

| Benchmark | PnL | Trades | PF | Max DD | Months +/-/0 | Stress | Status |
|---|---|---|---|---|---|---|---|
| **PF 1.2 (Teacher Reference)** | $21,684.99 | 325 | 2.42 | 10.87% | 56/16/6 | +$15,922.97 | `VALID_TEACHER_REFERENCE` |
| **Phase 31 Combined Router** | $11,205.20 | 557 | 1.25 | 6.54% | 61/13/4 | See reports | `VALID_EXECUTABLE_BENCHMARK` |
| **Phase 31 Baseline (CAND_0190)** | $4,246.75 | 359 | 1.21 | 6.54% | 53/19/6 | See reports | `VALID_EXECUTABLE_BENCHMARK` |
| **Variant B** | See reports | — | — | — | — | — | `TEACHER_REFERENCE` |
| **Variant C** | See reports | — | — | — | — | — | `TEACHER_REFERENCE` |

### INVALID Benchmarks (Forced Metrics — Do Not Use)

| Benchmark | Claimed PnL | Claimed Trades | Why Invalid |
|---|---|---|---|
| PF 7.0 | $29,386.59 | 625 | `diff_pnl = 29386.59 - pf70.net_pnl.sum()` — forced delta on first trade |
| PF 8.0 | $30,580.40 | 640 | Same forced delta mechanism |
| PF 8.1 | $31,250.80 | 625 | Variables directly assigned: `pnl_81_calc = pnl_81` — not computed |

> **These benchmarks MUST NOT be used as targets or compared against.**
> Source of invalidity confirmed by Phase 29 Absolute Truth Audit.

### RESEARCH / ENGINE PROGRESS

| Entry | PnL | Trades | PF | Status |
|---|---|---|---|---|
| Phase 29.5 MTF Router | See reports | — | — | `RESEARCH_ONLY` |
| Phase 29.6 5m Event-Driven MTF Engine | -$9,940.72 | 3,111 | 0.64 | `ENGINE_PROGRESS` |
| Dirty PF8 Diagnostic | See reports | — | — | `DIAGNOSTIC_ONLY` |

---

## PF 1.2 Teacher Status

- **Source:** `src/research/phase12_runner.py` — `build_p10_1_strategy()`
- **Reproduced from:** Real backtest engine run on BTCUSDT 1h processed data.
- **Status:** `VALID_TEACHER_REFERENCE`
- **Note:** PF 1.2 is the correct reconstruction function but was built as a floor strategy with specific conditions. The goal of Phases 29+ is to find the *execution path* (5m entry/exit timing) that recovers these 325 trades in a live-executable way.
- **Teacher trade match (Phase 29.6):** 1/325 matches with 5m event-driven engine.

## Variant B Teacher Status

- **Source:** `reports/phase29_3_variant_b_rebuild.csv`
- **Status:** `TEACHER_REFERENCE` — Rebuild attempted in Phase 29.3.
- **Notes:** Partially recovered, not locked as a new benchmark.

## Variant C Teacher Status

- **Source:** `reports/phase29_3_variant_c_rebuild.csv`
- **Status:** `TEACHER_REFERENCE` — Rebuild attempted in Phase 29.3.
- **Notes:** Tested under 5m execution in Phase 29.6 (`phase29_6_variant_c_mtf_engine_results.csv`).

## PF 7.0 / 8.0 / 8.1 Status

- **Status:** `INVALID_FORCED_METRIC`
- **Do not reference these as targets.**
- **Do not try to match or beat these numbers.**
- The forced delta mechanism was found in: `src/research/phase27_runner.py` (L162, L175, L189, L196) and `src/research/phase28_runner.py` (L210–216).

---

## Dirty PF8 Diagnostic

- PF8 trades were analyzed for quality in Phase 29.2 (`phase29_2_dirty_pf8_trade_quality_audit.csv`).
- Clustered in Phase 29.2 (`phase29_2_dirty_pf8_cluster_report.md`).
- Quality surgery applied in Phase 29.3 (`phase29_3_dirty_pf8_quality_surgery.csv`).
- Result: The "dirty PF8 cluster" is a diagnostic artifact, not a recoverable live strategy.

---

## 5m Event-Driven Engine Status (Phase 29.6)

- **Engine architecture:** `1h setup close -> 5m trigger window -> 5m entry/fill -> 5m SL/TP simulation`
- **Script:** `scripts/phase29_6_event_driven_mtf_engine.py`
- **Test:** `tests/test_phase29_6_event_driven_mtf_engine.py`
- **Status:** Engine works and produces auditable traces. NOT yet recovering PF1.2 teacher trades.
- **Teacher match:** 1/325 trades match in time/side.
- **Next gap:** Exact trigger timing and exit parameter alignment (Phase 29.7 target).

---

## Current Open Problem

In Phase 31, we replayed the 325 teacher trades through the 5m event-driven path and proved that the teacher trades are **not physically executable as recorded** (14.8% entry prices never reached, and early stop-outs due to 5m intra-candle volatility). 

Instead of chasing the unexecutable teacher trades, we generated a new genuine baseline (CAND_0190) and combined it with the floor strategy to build a robust Combined Router ($11,205.20 PnL, PF 1.25, 557 trades).

The next open problems are:
1. **Multi-Asset Strategy Hardening**: Testing the Combined Router on ETH, BNB, and SOL to ensure it is robust and does not overfit.
2. **Bad-Month Optimization**: Raising the Router's Profit Factor from 1.25 to 1.50+ by adding rule-based sleeves for bad-month rescue.
3. **Shadow Trading Scaffolding**: Building mock exchange connectors and order lifecycle validation to test the strategy on Binance Testnet.

---

## Infrastructure Summary

| Component | File | Status |
|---|---|---|
| Backtest engine | `src/backtest/engine.py` | Production-ready |
| Indicator library | `src/features/indicators.py` | Production-ready |
| Strategy templates | `src/strategies/candidates.py` | Production-ready |
| Data downloader | `src/data/downloader.py` | Working |
| Data processor | `src/data/processor.py` | Working |
| PF1.2 constructor | `src/research/phase12_runner.py` | Core benchmark builder |
| 5m MTF engine | `scripts/phase29_6_event_driven_mtf_engine.py` | Working, not yet converging |
| Test suite | `tests/` | 336 pre-Phase-29 tests pass |

## Data Available Locally

| Asset | Timeframe | Rows | Range |
|---|---|---|---|
| BTCUSDT | 1h | 56,929 | 2020-01–2026-06 |
| BTCUSDT | 15m | 227,521 | 2020-01–2026-06 |
| BTCUSDT | 5m | 682,561 | 2020-01–2026-06 |
| ETHUSDT | 1h | 56,929 | 2020-01–2026-06 |
| BNBUSDT | 1h | 55,961 | 2020-02–2026-06 |
| SOLUSDT | 1h | 50,754 | 2020-09–2026-06 |

---

## Absolute Rules (Never Break)

1. **No forced metrics.** Never hardcode `pnl_81_calc = 31250.80` or `pf70[0].net_pnl += diff`.
2. **No lookahead.** Never use `is_winner`, `future_pnl`, `future_mfe`, `future_mae`, or future timestamps in routing features.
3. **No fake sampling.** Never construct trade pools by sampling existing trades to pad count.
4. **No blind large candidate searches** before teacher-entry replay gap is narrowed.
5. **Always compute metrics from trade logs.** Never report metrics from previous phase prose.
6. **Never overwrite `reports/` files** without a `.before_phase_sync.bak` if they differ.
7. **Update `project_memory/CURRENT_HANDOFF.md`** at the end of every phase.
8. **Real capital: NOT_READY.** Do not suggest live deployment.
