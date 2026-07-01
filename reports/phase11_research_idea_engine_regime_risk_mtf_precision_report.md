# Phase 11 — Research Lab Intelligence Upgrade Report

**Compiled At:** 2026-06-30 13:31:47 UTC
**Project:** binance_futures_backtest
**Symbol:** BTCUSDT Perpetual Futures (Binance USD-M)
**Primary frame:** 1h (56,881 candles)

## Executive Verdict

> [!IMPORTANT]
> **VERDICT: FAIL_NO_STRATEGY_FOUND**
> **Selected Champion:** FoF_Champion_P10.1
> - Net PnL: **$9400.70** (vs Floor $10,535.14)
> - Win Rate: **52.49%**
> - Profit Factor: **1.30** (vs Floor 1.28)
> - Max Drawdown: **12.96%** (vs Floor 14.89%)
> - Total Trades: **461** (vs Floor 493)
> - Months: **48 / 29 / 1** +/-/0
> - Combined OOS PnL: **$4936.86** (vs Floor $4,878.89)

## 1. Phase 10.1 Quality Floor Reproduction
| Metric | Floor | Reproduced |
|---|---|---|
| Net PnL | $10,535.14 | $9400.70 |
| PF | 1.28 | 1.30 |
| DD | 14.89% | 12.96% |
| Trades | 493 | 461 |
| +/-/0 | 49/28/1 | 48/29/1 |
| Floor OK | — | WARNING |

## 2. ResearchIdeaEngine Summary
- Total ideas generated: **11**
- Idea categories covered:
  - false_breakout: 24 idea(s)
  - chop: 3 idea(s)
  - cost_erosion: 2 idea(s)
- Full idea registry: [research_ideas.json](reports/research_ideas.json)
- Ranked leaderboard: [research_ideas_leaderboard.md](reports/research_ideas_leaderboard.md)

## 3. New Candidate Families
| Candidate | Template | Net PnL ($) | Trades | PF | DD | +/-/0 |
|---|---|---|---|---|---|---|
| EMA_Reclaim | trend_pullback_ema_reclaim | -404.55 | 4 | 0.00 | 4.05% | 0/4/74 |
| VWAP_Reclaim | vwap_reclaim_continuation | -8316.62 | 1329 | 0.82 | 84.26% | 27/51/0 |
| Vol_Compress_Release | volatility_compression_release | -8144.17 | 1509 | 0.84 | 83.80% | 28/50/0 |
| ADX_Momentum | adx_slope_momentum_continuation | -8013.82 | 1798 | 0.88 | 82.49% | 32/46/0 |
| Range_Failure | range_failure_reversal | -7663.09 | 542 | 0.69 | 78.37% | 24/54/0 |

## 4. Regime Risk Sizing Results
| Mode | Net PnL ($) | PF | DD | Trades | +/-/0 |
|---|---|---|---|---|---|
| no_throttle | 9400.70 | 1.30 | 12.96% | 461 | 48/29/1 |
| monthly_dd_halved | 8184.49 | 1.29 | 12.26% | 409 | 44/33/1 |
| consec_loss_half | 9400.70 | 1.30 | 12.96% | 461 | 48/29/1 |
| emergency_pause_1pct | 9226.48 | 1.44 | 8.00% | 300 | 35/42/1 |

Best Risk Mode: **no_throttle**

## 5. 5m MTF Entry Research
| Config | Net PnL ($) | Trades | PF | DD | +/-/0 |
|---|---|---|---|---|---|
| bb_expansion_refined_adx3_vol14 | 4341.17 | 298 | 1.23 | 13.14% | 43/24/11 |
| bb_expansion_vol_adx_filtered | 3658.23 | 313 | 1.19 | 13.16% | 43/25/10 |

## 6. Negative-Month Forensics
- Total FoF Champion negative months: **29**
- Failure category breakdown:
  - false_breakout: 24 month(s)
  - chop: 3 month(s)
  - cost_erosion: 2 month(s)

Best Anti-FalseBreakout Config: adx_slope_thresh=0.0 | vol_thresh=1.2
  PnL=$5008.69 trades=326 PF=1.23 DD=14.55% +/-/0=44/24/10

## 7. Zero-Month Elimination
- Zero months in FoF Champion: **1**
- VWAP Reclaim (standalone): PnL=$-8316.62 trades=1329 PF=0.82 DD=84.26% +/-/0=27/51/0
- FoF + VWAP Rescue: PnL=$8010.10 trades=546 PF=1.21 DD=12.99% +/-/0=43/35/0
  - Zero month delta: -1

## 8. FoF Evolution — Finalist Comparison
| System | IS PnL ($) | OOS PnL ($) | PF | DD | +/-/0 |
|---|---|---|---|---|---|
| FoF_Champion_P10.1 | 9400.70 | 4936.86 | 1.30 | 12.96% | 48/29/1 |
| FoF_VWAP_Rescue | 8010.10 | 3259.74 | 1.21 | 12.99% | 43/35/0 |
| FoF_AntiFB_Refined | 9419.18 | 4650.12 | 1.27 | 16.99% | 46/31/1 |
| FoF_ADX_Momentum | -2373.97 | -3525.43 | 0.96 | 55.42% | 22/56/0 |

**Selected:** FoF_Champion_P10.1

**Why selected:**
- Highest composite score: IS PnL + 0.5x OOS PnL - 100x neg months - 500x zero months
- Preserves quality floor metrics while improving on monthly distribution

## 9. Anti-Overfitting Audit
- IS/OOS Ratio: 1.90x (threshold: < 5.0x)
- Parameter Stability (adx_thresh ±5): PnL std=$0.00
- No overfitting warnings detected.

## 10. Walk-Forward OOS Validation
- **Combined OOS PnL:** $4936.86

| Period | PnL ($) | Trades | PF | DD |
|---|---|---|---|---|
| 2022 | 1635.12 | 69 | 1.45 | 6.21% |
| 2023 | 2085.93 | 47 | 1.99 | 2.19% |
| 2024 | -105.77 | 71 | 0.97 | 11.39% |
| 2025+ | 1321.59 | 83 | 1.28 | 7.03% |

## 11. Stress Testing Results
| Scenario | PnL ($) | DD | +/-/0 | Verdict |
|---|---|---|---|---|
| normal | 9400.70 | 12.96% | 48/29/1 | **PASS** |
| double_fees | 5602.35 | 15.43% | 46/31/1 | **PASS** |
| triple_fees | 2508.91 | 17.35% | 44/33/1 | **PASS** |
| double_slippage | 9400.70 | 12.96% | 48/29/1 | **PASS** |
| triple_slippage | 9400.70 | 12.96% | 48/29/1 | **PASS** |
| double_fees_double_slippage | 5602.35 | 15.43% | 46/31/1 | **PASS** |
| delay_1_candle | 6287.14 | 10.96% | 44/33/1 | **PASS** |
| delay_2_candles | 3692.80 | 14.25% | 42/35/1 | **PASS** |
| missed_fills_10 | 6229.05 | 15.56% | 46/31/1 | **PASS** |
| missed_fills_20 | 2768.68 | 18.57% | 40/37/1 | **PASS** |
| missed_fills_30 | 4327.53 | 14.25% | 46/31/1 | **PASS** |
| combined_adverse | 2228.14 | 14.80% | 40/37/1 | **PASS** |

## 12. Champion Month-by-Month Table
| Month | Trades | Wins | Losses | Win Rate | Net PnL ($) | Drawdown | Status |
|---|---|---|---|---|---|---|---|
| 2020-01 | 10 | 5 | 5 | 50.00% | 22.01 | 3.06% | Positive |
| 2020-02 | 9 | 3 | 6 | 33.33% | -355.38 | 4.48% | Negative |
| 2020-03 | 11 | 8 | 3 | 72.73% | 646.34 | 2.05% | Positive |
| 2020-04 | 6 | 6 | 0 | 100.00% | 760.00 | 0.00% | Positive |
| 2020-05 | 5 | 1 | 4 | 20.00% | -370.51 | 4.24% | Negative |
| 2020-06 | 3 | 1 | 2 | 33.33% | -51.02 | 2.13% | Negative |
| 2020-07 | 4 | 2 | 2 | 50.00% | 39.89 | 2.06% | Positive |
| 2020-08 | 3 | 0 | 3 | 0.00% | -313.31 | 2.93% | Negative |
| 2020-09 | 4 | 3 | 1 | 75.00% | 219.70 | 1.03% | Positive |
| 2020-10 | 4 | 2 | 2 | 50.00% | -16.70 | 1.51% | Negative |
| 2020-11 | 10 | 6 | 4 | 60.00% | 282.31 | 2.16% | Positive |
| 2020-12 | 3 | 0 | 3 | 0.00% | -286.93 | 2.64% | Negative |
| 2021-01 | 19 | 8 | 11 | 42.11% | -318.36 | 5.83% | Negative |
| 2021-02 | 5 | 1 | 4 | 20.00% | -265.54 | 3.51% | Negative |
| 2021-03 | 3 | 0 | 3 | 0.00% | -265.08 | 2.65% | Negative |
| 2021-04 | 12 | 9 | 3 | 75.00% | 667.79 | 2.00% | Positive |
| 2021-05 | 19 | 14 | 5 | 73.68% | 1244.06 | 2.07% | Positive |
| 2021-06 | 10 | 5 | 5 | 50.00% | 167.76 | 2.10% | Positive |
| 2021-07 | 3 | 1 | 2 | 33.33% | -100.72 | 1.09% | Negative |
| 2021-08 | 5 | 1 | 4 | 20.00% | -346.19 | 3.18% | Negative |
| 2021-09 | 7 | 3 | 4 | 42.86% | -67.44 | 2.07% | Negative |
| 2021-10 | 11 | 9 | 2 | 81.82% | 909.94 | 1.05% | Positive |
| 2021-11 | 14 | 7 | 7 | 50.00% | -89.31 | 3.21% | Negative |
| 2021-12 | 4 | 2 | 2 | 50.00% | 99.27 | 1.09% | Positive |
| 2022-01 | 6 | 4 | 2 | 66.67% | 413.10 | 1.06% | Positive |
| 2022-02 | 9 | 6 | 3 | 66.67% | 657.18 | 2.11% | Positive |
| 2022-03 | 6 | 2 | 4 | 33.33% | -231.52 | 3.22% | Negative |
| 2022-04 | 3 | 0 | 3 | 0.00% | -417.31 | 3.20% | Negative |
| 2022-05 | 6 | 4 | 2 | 66.67% | 260.60 | 2.06% | Positive |
| 2022-06 | 10 | 5 | 5 | 50.00% | 201.45 | 3.05% | Positive |
| 2022-07 | 8 | 4 | 4 | 50.00% | 151.86 | 2.11% | Positive |
| 2022-08 | 5 | 3 | 2 | 60.00% | 199.01 | 2.14% | Positive |
| 2022-09 | 8 | 3 | 5 | 37.50% | -172.90 | 4.18% | Negative |
| 2022-10 | 3 | 2 | 1 | 66.67% | 148.23 | 1.12% | Positive |
| 2022-11 | 5 | 3 | 2 | 60.00% | 164.99 | 1.08% | Positive |
| 2022-12 | 2 | 2 | 0 | 100.00% | 432.54 | 0.00% | Positive |
| 2023-01 | 6 | 3 | 3 | 50.00% | 121.93 | 2.11% | Positive |
| 2023-02 | 4 | 2 | 2 | 50.00% | 91.58 | 2.15% | Positive |
| 2023-03 | 8 | 5 | 3 | 62.50% | 492.36 | 2.08% | Positive |
| 2023-04 | 5 | 3 | 2 | 60.00% | 290.19 | 2.14% | Positive |
| 2023-05 | 2 | 2 | 0 | 100.00% | 463.67 | 0.00% | Positive |
| 2023-06 | 6 | 3 | 3 | 50.00% | 98.44 | 2.19% | Positive |
| 2023-07 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2023-08 | 4 | 3 | 1 | 75.00% | 533.05 | 1.05% | Positive |
| 2023-09 | 2 | 2 | 0 | 100.00% | 436.96 | 0.00% | Positive |
| 2023-10 | 2 | 1 | 1 | 50.00% | 42.00 | 1.07% | Positive |
| 2023-11 | 2 | 1 | 1 | 50.00% | 53.73 | 1.08% | Positive |
| 2023-12 | 6 | 4 | 2 | 66.67% | 285.84 | 1.31% | Positive |
| 2024-01 | 9 | 5 | 4 | 55.56% | 373.83 | 3.14% | Positive |
| 2024-02 | 11 | 5 | 6 | 45.45% | -92.61 | 2.12% | Negative |
| 2024-03 | 16 | 7 | 9 | 43.75% | -421.74 | 4.27% | Negative |
| 2024-04 | 4 | 4 | 0 | 100.00% | 767.43 | 0.00% | Positive |
| 2024-05 | 3 | 1 | 2 | 33.33% | -153.81 | 1.10% | Negative |
| 2024-06 | 4 | 1 | 3 | 25.00% | -334.22 | 3.32% | Negative |
| 2024-07 | 3 | 0 | 3 | 0.00% | -543.43 | 3.18% | Negative |
| 2024-08 | 7 | 3 | 4 | 42.86% | -161.44 | 3.25% | Negative |
| 2024-09 | 2 | 0 | 2 | 0.00% | -358.52 | 2.19% | Negative |
| 2024-10 | 2 | 0 | 2 | 0.00% | -271.06 | 1.69% | Negative |
| 2024-11 | 9 | 5 | 4 | 55.56% | 425.56 | 2.08% | Positive |
| 2024-12 | 6 | 4 | 2 | 66.67% | 454.34 | 1.58% | Positive |
| 2025-01 | 6 | 3 | 3 | 50.00% | 152.12 | 2.11% | Positive |
| 2025-02 | 6 | 3 | 3 | 50.00% | 164.96 | 2.10% | Positive |
| 2025-03 | 7 | 4 | 3 | 57.14% | 426.13 | 2.10% | Positive |
| 2025-04 | 6 | 4 | 2 | 66.67% | 586.16 | 2.09% | Positive |
| 2025-05 | 3 | 0 | 3 | 0.00% | -579.97 | 3.23% | Negative |
| 2025-06 | 2 | 1 | 1 | 50.00% | 195.24 | 0.29% | Positive |
| 2025-07 | 4 | 3 | 1 | 75.00% | 662.96 | 0.28% | Positive |
| 2025-08 | 2 | 2 | 0 | 100.00% | 553.41 | 0.00% | Positive |
| 2025-09 | 4 | 1 | 3 | 25.00% | -568.69 | 3.03% | Negative |
| 2025-10 | 3 | 1 | 2 | 33.33% | -178.09 | 1.14% | Negative |
| 2025-11 | 2 | 1 | 1 | 50.00% | 41.72 | 1.08% | Positive |
| 2025-12 | 8 | 3 | 5 | 37.50% | -294.60 | 4.79% | Negative |
| 2026-01 | 7 | 4 | 3 | 57.14% | 339.13 | 1.66% | Positive |
| 2026-02 | 6 | 4 | 2 | 66.67% | 592.92 | 1.11% | Positive |
| 2026-03 | 6 | 4 | 2 | 66.67% | 654.18 | 1.08% | Positive |
| 2026-04 | 3 | 0 | 3 | 0.00% | -632.73 | 3.27% | Negative |
| 2026-05 | 3 | 2 | 1 | 66.67% | 313.55 | 1.12% | Positive |
| 2026-06 | 5 | 3 | 2 | 60.00% | 358.40 | 2.13% | Positive |

## 13. Compliance Audits
- **signal_audit:** PASS
- **trade_audit:** PASS
- **no_fake_audit:** PASS

## 14. Remaining Gap & Phase 12 Recommendations
- Remaining negative months: **29** (target: 0, gap: 29)
- Remaining zero months: **1** (target: 0, gap: 1)
- Trade count gap to target (780): **319**

**Phase 12 Recommendations:**
1. Deep multi-objective optimization: sweep new P11 templates jointly with FoF parameters
2. Live-regime-aligned filler with stricter activity criteria
3. Ensemble diversification: add orthogonal strategy (e.g. funding + session range)
4. Dynamic risk matrix: regime + ADX + funding state composite
5. Asymmetric TP/SL: tighter stops on false-breakout-prone regimes

---
*Report generated by Phase 11 Research Lab in 372s. ResearchIdeaEngine v1.0. 11 ideas generated.*