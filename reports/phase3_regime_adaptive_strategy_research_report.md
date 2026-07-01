# Phase 3 Strategy Research Report

**Date:** 2026-06-29 08:53:24 UTC
**Verifying Symbol:** BTCUSDT perpetual futures (Binance USD-M)

## EXECUTIVE VERDICT

> [!CAUTION]
> **VERDICT: FAIL_NO_STRATEGY_FOUND**
> None of the candidate strategies or portfolio combinations met the strict criteria of 100% positive months (0 negative, 0 zero months) over the full history.
>
> **Reasons for Verdict:**
> - Portfolio Negative Months: 1 (target: 0)
> - Portfolio Zero Months: 77 (target: 0)
> - Portfolio Total Trades: 5 (target: >= 780)

## 1. INFRASTRUCTURE & BACKTESTING UPGRADES
- **Multi-Position Backtester**: Implemented a concurrent position-management engine managing concurrent trades, risk sizing, cooldown limits, and capital drawdown limits.
- **Regime Classification**: Developed a robust, timezone-safe market state classifier calculating bull trend, bear trend, range, vol compression, expansion, sweep zones, extreme funding, and chop zones.
- **Deduplication**: Implemented parameter and trade list exit signature checks to guarantee only unique candidates enter the leaderboard.

## 2. PHASE 1 CANDIDATE RESULTS RERUN
| Strategy | Trades | Win Rate | Net PnL ($) | Profit Factor | Max DD | +/-/0 Months |
|---|---|---|---|---|---|---|
| VolatilitySqueezeBreakout | 488 | 40.37% | -5687.42 | 0.79 | 60.72% | 33 / 45 / 0 |
| VWAPMeanReversionFunding | 34 | 32.35% | -908.07 | 0.62 | 13.58% | 6 / 12 / 60 |
| MultiTimeframeTrendPullback | 5 | 60.00% | 286.55 | 2.20 | 1.20% | 3 / 2 / 73 |
| SessionRangeBreakout | 1835 | 37.17% | -9754.54 | 0.74 | 97.62% | 13 / 65 / 0 |
| LiquiditySweepFundingReversal | 498 | 32.13% | -7343.15 | 0.71 | 74.42% | 23 / 55 / 0 |

## 3. STAGED SEARCH & PRUNING
- Evaluated **4000** configurations from a parameter space of over 1.9 million configs.
- **Stage 1 Pruned (Subperiod Sanity)**: 3840
- **Stage 2 Pruned (Multi-Regime Survival)**: 155
- **Stage 3 Pruned (Monthly Consistency)**: 5
- **Stage 4 Pruned (Walk-Forward OOS)**: 0

## 4. LEADERBOARD (OOS-First Promotion)
| Strategy Class | Config Details | OOS PnL ($) | Full PnL ($) | Win Rate | Max DD | +/-/0 Months |
|---|---|---|---|---|---|---|

## 5. MULTI-STRATEGY PORTFOLIO COMBINATION
- **Combined Strategies**: ['RegimeAdaptiveStrategySystem', 'UniversalStrategyTemplate', 'UniversalStrategyTemplate']
- **Total Trades**: 5
- **Net PnL**: $-601.45
- **Max Drawdown**: 6.01%
- **Profit Factor**: 0.00
- **Win Rate**: 0.00%

### Portfolio Month-by-Month Table
| Month | Net PnL ($) | Status |
|---|---|---|
| 2020-01 | -601.45 | Negative |
| 2020-02 | 0.00 | Zero |
| 2020-03 | 0.00 | Zero |
| 2020-04 | 0.00 | Zero |
| 2020-05 | 0.00 | Zero |
| 2020-06 | 0.00 | Zero |
| 2020-07 | 0.00 | Zero |
| 2020-08 | 0.00 | Zero |
| 2020-09 | 0.00 | Zero |
| 2020-10 | 0.00 | Zero |
| 2020-11 | 0.00 | Zero |
| 2020-12 | 0.00 | Zero |
| 2021-01 | 0.00 | Zero |
| 2021-02 | 0.00 | Zero |
| 2021-03 | 0.00 | Zero |
| 2021-04 | 0.00 | Zero |
| 2021-05 | 0.00 | Zero |
| 2021-06 | 0.00 | Zero |
| 2021-07 | 0.00 | Zero |
| 2021-08 | 0.00 | Zero |
| 2021-09 | 0.00 | Zero |
| 2021-10 | 0.00 | Zero |
| 2021-11 | 0.00 | Zero |
| 2021-12 | 0.00 | Zero |
| 2022-01 | 0.00 | Zero |
| 2022-02 | 0.00 | Zero |
| 2022-03 | 0.00 | Zero |
| 2022-04 | 0.00 | Zero |
| 2022-05 | 0.00 | Zero |
| 2022-06 | 0.00 | Zero |
| 2022-07 | 0.00 | Zero |
| 2022-08 | 0.00 | Zero |
| 2022-09 | 0.00 | Zero |
| 2022-10 | 0.00 | Zero |
| 2022-11 | 0.00 | Zero |
| 2022-12 | 0.00 | Zero |
| 2023-01 | 0.00 | Zero |
| 2023-02 | 0.00 | Zero |
| 2023-03 | 0.00 | Zero |
| 2023-04 | 0.00 | Zero |
| 2023-05 | 0.00 | Zero |
| 2023-06 | 0.00 | Zero |
| 2023-07 | 0.00 | Zero |
| 2023-08 | 0.00 | Zero |
| 2023-09 | 0.00 | Zero |
| 2023-10 | 0.00 | Zero |
| 2023-11 | 0.00 | Zero |
| 2023-12 | 0.00 | Zero |
| 2024-01 | 0.00 | Zero |
| 2024-02 | 0.00 | Zero |
| 2024-03 | 0.00 | Zero |
| 2024-04 | 0.00 | Zero |
| 2024-05 | 0.00 | Zero |
| 2024-06 | 0.00 | Zero |
| 2024-07 | 0.00 | Zero |
| 2024-08 | 0.00 | Zero |
| 2024-09 | 0.00 | Zero |
| 2024-10 | 0.00 | Zero |
| 2024-11 | 0.00 | Zero |
| 2024-12 | 0.00 | Zero |
| 2025-01 | 0.00 | Zero |
| 2025-02 | 0.00 | Zero |
| 2025-03 | 0.00 | Zero |
| 2025-04 | 0.00 | Zero |
| 2025-05 | 0.00 | Zero |
| 2025-06 | 0.00 | Zero |
| 2025-07 | 0.00 | Zero |
| 2025-08 | 0.00 | Zero |
| 2025-09 | 0.00 | Zero |
| 2025-10 | 0.00 | Zero |
| 2025-11 | 0.00 | Zero |
| 2025-12 | 0.00 | Zero |
| 2026-01 | 0.00 | Zero |
| 2026-02 | 0.00 | Zero |
| 2026-03 | 0.00 | Zero |
| 2026-04 | 0.00 | Zero |
| 2026-05 | 0.00 | Zero |
| 2026-06 | 0.00 | Zero |

## 6. STRESS TESTING RESULTS
| Scenario | Trades | Win Rate | PnL ($) | Max DD | +/-/0 Months | Verdict |
|---|---|---|---|---|---|---|
| normal | 5 | 0.00% | -601.45 | 6.01% | 0 / 1 / 77 | **FAIL** |
| double_fees | 5 | 0.00% | -674.11 | 6.74% | 0 / 1 / 77 | **FAIL** |
| triple_fees | 3 | 0.00% | -515.35 | 5.15% | 0 / 1 / 77 | **FAIL** |
| double_slippage | 5 | 0.00% | -637.88 | 6.38% | 0 / 1 / 77 | **FAIL** |
| triple_slippage | 5 | 0.00% | -674.20 | 6.74% | 0 / 1 / 77 | **FAIL** |
| double_fees_double_slippage | 5 | 0.00% | -710.34 | 7.10% | 0 / 1 / 77 | **FAIL** |
| delay_5m | 5 | 0.00% | -601.45 | 6.01% | 0 / 1 / 77 | **FAIL** |
| stale_skip_15m | 5 | 0.00% | -601.45 | 6.01% | 0 / 1 / 77 | **FAIL** |
| delay_1_candle | 5 | 0.00% | -601.45 | 6.01% | 0 / 1 / 77 | **FAIL** |
| delay_2_candles | 5 | 0.00% | -601.45 | 6.01% | 0 / 1 / 77 | **FAIL** |
| missed_fills_10 | 5 | 0.00% | -601.45 | 6.01% | 0 / 1 / 77 | **FAIL** |
| missed_fills_20 | 5 | 0.00% | -601.45 | 6.01% | 0 / 1 / 77 | **FAIL** |
| missed_fills_30 | 5 | 0.00% | -601.45 | 6.01% | 0 / 1 / 77 | **FAIL** |
| combined_adverse | 5 | 0.00% | -710.34 | 7.10% | 0 / 1 / 77 | **FAIL** |

## 7. COMPLIANCE & LOOKAHEAD AUDITS
- **Data Audit**: **PASS**
- **Signal Audit**: **PASS**
- **Trade Audit**: **PASS**
- **No-Fake Audit**: **PASS**

---
*Compiled by Antigravity Phase 3 Trading Research Agent.*