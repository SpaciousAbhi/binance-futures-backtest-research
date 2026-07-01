# Phase 8 -- Alpha Distillation, Multi-Candidate Fusion,
## Dynamic Exits, and Bad-Month Conversion Research

**Date:** 2026-06-30 06:11:16 UTC
**Symbol:** BTCUSDT USD-M Perpetual Futures (Binance)
**Data range:** 2020-01-01 -> 2026-06-28
**Primary eval frame:** 1h (56,881 candles) -- matches Phase 4-7 baseline evaluation

---
## EXECUTIVE VERDICT

> [!CAUTION]
> **VERDICT: FAIL_NO_STRATEGY_FOUND**
> Best system: F-E: Top-3 + Filler (zero-rescue) (no_throttle)
> - Negative months: 39 (target: 0)
> - Zero months:     2 (target: 0)
> - Total trades:    768 (target: >=780)

> [!IMPORTANT]
> **Root cause of Phase 8 initial regression**: Phase 8 originally ran on the 5m MTF-aligned frame.
> On 5m data, bb_width > 0.06 fires only ~293 raw signals over 6.5 years,
> yielding 181 trades and -$3,915 PnL -- a false regression vs Phase 7.
> Phase 7 Baseline A (731 trades, +$6,577) was evaluated on the 1h frame
> where bb_width > 0.06 hits 8,415 candles (14.8%) -- matching the trade count.
> Phase 8 corrected to use 1h as primary evaluation frame.

## 1. LOCKED CHAMPION CANDIDATE BANK (1h evaluation, Reproducibility Check)
| Candidate | Role | Net PnL ($) | DD | PF | Trades | +/-/0 Months |
|---|---|---|---|---|---|---|
| A | Phase 6 Portfolio (Activity Champion) | 5760.09 | 23.10% | 1.14 | 738 | 33/37/8 |
| C | Phase-5 Single (PF/DD Champion) | 6872.29 | 6.96% | 1.35 | 295 | 44/26/8 |
| D | Range Reclaim Filler (Zero-Month Rescue) | 150.38 | 14.33% | 1.03 | 82 | 23/28/27 |
| E | Delay-1 Variant (Confirmation) | 1712.98 | 13.04% | 1.07 | 362 | 33/37/8 |

## 2. MONTHLY COMPLEMENT MATRIX
_(i_helps_j = months candidate i is positive when j is negative)_
| | A | C | D | E |
|---|---|---|---|---|
| **A** | -- | i_helps=4, both_neg=22 | i_helps=11, both_neg=14 | i_helps=10, both_neg=27 |
| **C** | i_helps=15, both_neg=22 | -- | i_helps=14, both_neg=11 | i_helps=16, both_neg=21 |
| **D** | i_helps=9, both_neg=14 | i_helps=5, both_neg=11 | -- | i_helps=10, both_neg=15 |
| **E** | i_helps=10, both_neg=27 | i_helps=5, both_neg=21 | i_helps=10, both_neg=15 | -- |

## 3. DYNAMIC EXIT VARIANT RESULTS
| Exit Mode | Net PnL ($) | PF | DD | Trades | +/-/0 Months | Score |
|---|---|---|---|---|---|---|
| * Static SL/TP | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |
| Trail 1.5 ATR | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |
| Trail 2.0 ATR | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |
| Trail 2.5 ATR | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |
| Breakeven 1.0 ATR | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |
| Breakeven 1.5 ATR | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |
| Trail+BE 1.5/1.0 | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |
| Trail+BE 2.0/1.0 | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |
| Trail+BE 2.5/1.5 | 4503.91 | 1.18 | 9.70% | 376 | 43/27/8 | -51793.05 |

## 4. FUSION MODEL RESULTS
| Rank | Model | Net PnL ($) | PF | DD | Trades | +/-/0 Months | Score |
|---|---|---|---|---|---|---|---|
| 1 | * F-E: Top-3 + Filler (zero-rescue) | 5677.97 | 1.12 | 24.62% | 768 | 37/39/2 | -15268.28 |
| 2 | F-F: Top-3 + Filler + Regime Switch | 5677.97 | 1.12 | 24.62% | 768 | 37/39/2 | -15268.28 |
| 3 | F-A: Top-3 Union (cancel) | 5760.09 | 1.14 | 23.10% | 738 | 33/37/8 | -17470.87 |
| 4 | F-B: Top-3 Union (long-priority) | 5760.09 | 1.14 | 23.10% | 738 | 33/37/8 | -17470.87 |
| 5 | F-C: Intersection >=2 | 5760.09 | 1.14 | 23.10% | 738 | 33/37/8 | -17470.87 |
| 6 | F-D: Regime Switching Top-3 | 5760.09 | 1.14 | 23.10% | 738 | 33/37/8 | -17470.87 |
| 7 | F-G: Single C + Filler | 5503.60 | 1.18 | 23.29% | 438 | 39/37/2 | -44829.33 |

## 5. MTD THROTTLE OPTIMIZATION
| Mode | Net PnL ($) | PF | DD | Trades | +/-/0 Months | Score |
|---|---|---|---|---|---|---|
| * no_throttle | 5677.97 | 1.12 | 24.62% | 768 | 37/39/2 | -15268.28 |
| emergency_pause | 5677.97 | 1.12 | 24.62% | 768 | 37/39/2 | -15268.28 |
| medium | 5261.92 | 1.12 | 25.33% | 760 | 35/41/2 | -17091.39 |
| soft | 5451.29 | 1.12 | 25.42% | 755 | 35/41/2 | -17152.88 |
| hard | 4086.35 | 1.09 | 27.06% | 790 | 35/41/2 | -17284.26 |

## 6. CHOSEN PHASE 8 SYSTEM
**System:** F-E: Top-3 + Filler (zero-rescue) (no_throttle)
- Net PnL: **$5677.97**
- Win Rate: 50.00%
- Profit Factor: 1.12
- Max Drawdown: 24.62%
- Total Trades: 768
- +/-/0 Months: 37 / 39 / 2
- Score: -15268.28
- Best Month: $2021.99  /  Worst Month: $-907.75
- Avg Winner: $135.07  /  Avg Loser: $-120.28
- Avg R: 0.17  /  Avg Hold Candles: 15.1

## 7. CHOSEN SYSTEM -- MONTH-BY-MONTH BREAKDOWN
| Month | Trades | Wins | Losses | Win Rate | Net PnL ($) | DD | Status |
|---|---|---|---|---|---|---|---|
| 2020-01 | 10 | 6 | 4 | 60.00% | 382.48 | 3.45% | Positive |
| 2020-02 | 5 | 0 | 5 | 0.00% | -382.15 | 3.68% | Negative |
| 2020-03 | 30 | 18 | 12 | 60.00% | 553.50 | 9.01% | Positive |
| 2020-04 | 18 | 14 | 4 | 77.78% | 1552.67 | 2.15% | Positive |
| 2020-05 | 3 | 0 | 3 | 0.00% | -409.62 | 3.38% | Negative |
| 2020-06 | 6 | 0 | 6 | 0.00% | -373.51 | 3.19% | Negative |
| 2020-07 | 4 | 4 | 0 | 100.00% | 275.74 | 0.00% | Positive |
| 2020-08 | 7 | 0 | 7 | 0.00% | -393.83 | 3.40% | Negative |
| 2020-09 | 6 | 3 | 3 | 50.00% | -319.47 | 3.10% | Negative |
| 2020-10 | 6 | 4 | 2 | 66.67% | 478.48 | 1.08% | Positive |
| 2020-11 | 18 | 9 | 9 | 50.00% | -229.62 | 5.75% | Negative |
| 2020-12 | 3 | 0 | 3 | 0.00% | -355.18 | 3.16% | Negative |
| 2021-01 | 55 | 30 | 25 | 54.55% | 892.66 | 10.65% | Positive |
| 2021-02 | 6 | 0 | 6 | 0.00% | -303.49 | 2.60% | Negative |
| 2021-03 | 33 | 14 | 19 | 42.42% | -369.25 | 6.57% | Negative |
| 2021-04 | 17 | 11 | 6 | 64.71% | 918.48 | 2.16% | Positive |
| 2021-05 | 47 | 23 | 24 | 48.94% | 857.43 | 7.99% | Positive |
| 2021-06 | 12 | 6 | 6 | 50.00% | -407.95 | 3.19% | Negative |
| 2021-07 | 11 | 7 | 4 | 63.64% | 747.38 | 2.11% | Positive |
| 2021-08 | 16 | 9 | 7 | 56.25% | 180.94 | 4.13% | Positive |
| 2021-09 | 14 | 5 | 9 | 35.71% | 148.25 | 5.36% | Positive |
| 2021-10 | 15 | 11 | 4 | 73.33% | 1035.57 | 3.89% | Positive |
| 2021-11 | 17 | 8 | 9 | 47.06% | -335.92 | 5.96% | Negative |
| 2021-12 | 14 | 11 | 3 | 78.57% | 1434.68 | 2.64% | Positive |
| 2022-01 | 3 | 0 | 3 | 0.00% | -495.86 | 3.18% | Negative |
| 2022-02 | 21 | 14 | 7 | 66.67% | 1176.88 | 5.25% | Positive |
| 2022-03 | 12 | 8 | 4 | 66.67% | 693.19 | 4.26% | Positive |
| 2022-04 | 3 | 0 | 3 | 0.00% | -551.66 | 3.25% | Negative |
| 2022-05 | 22 | 10 | 12 | 45.45% | 45.45 | 9.05% | Positive |
| 2022-06 | 9 | 3 | 6 | 33.33% | -907.75 | 6.44% | Negative |
| 2022-07 | 9 | 3 | 6 | 33.33% | -592.51 | 3.81% | Negative |
| 2022-08 | 6 | 3 | 3 | 50.00% | 45.48 | 1.63% | Positive |
| 2022-09 | 3 | 0 | 3 | 0.00% | -484.48 | 3.23% | Negative |
| 2022-10 | 4 | 1 | 3 | 25.00% | 114.96 | 0.84% | Positive |
| 2022-11 | 9 | 3 | 6 | 33.33% | -144.43 | 1.61% | Negative |
| 2022-12 | 3 | 1 | 2 | 33.33% | -80.68 | 2.24% | Negative |
| 2023-01 | 9 | 3 | 6 | 33.33% | -470.21 | 3.27% | Negative |
| 2023-02 | 6 | 4 | 2 | 66.67% | 184.17 | 2.12% | Positive |
| 2023-03 | 21 | 16 | 5 | 76.19% | 2021.99 | 3.39% | Positive |
| 2023-04 | 5 | 2 | 3 | 40.00% | -131.35 | 3.27% | Negative |
| 2023-05 | 1 | 1 | 0 | 100.00% | 261.07 | 0.00% | Positive |
| 2023-06 | 3 | 0 | 3 | 0.00% | -542.80 | 3.34% | Negative |
| 2023-07 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2023-08 | 7 | 4 | 3 | 57.14% | 307.01 | 1.58% | Positive |
| 2023-09 | 3 | 3 | 0 | 100.00% | 155.97 | 0.00% | Positive |
| 2023-10 | 3 | 3 | 0 | 100.00% | 649.37 | 0.00% | Positive |
| 2023-11 | 3 | 0 | 3 | 0.00% | -546.98 | 3.25% | Negative |
| 2023-12 | 8 | 3 | 5 | 37.50% | -424.26 | 4.41% | Negative |
| 2024-01 | 6 | 0 | 6 | 0.00% | -771.88 | 4.87% | Negative |
| 2024-02 | 9 | 9 | 0 | 100.00% | 1401.51 | 0.00% | Positive |
| 2024-03 | 16 | 6 | 10 | 37.50% | -499.06 | 7.15% | Negative |
| 2024-04 | 11 | 6 | 5 | 54.55% | 248.83 | 3.18% | Positive |
| 2024-05 | 11 | 5 | 6 | 45.45% | 24.56 | 3.29% | Positive |
| 2024-06 | 5 | 0 | 5 | 0.00% | -516.99 | 3.18% | Negative |
| 2024-07 | 6 | 0 | 6 | 0.00% | -412.81 | 2.62% | Negative |
| 2024-08 | 14 | 11 | 3 | 78.57% | 857.15 | 3.24% | Positive |
| 2024-09 | 5 | 0 | 5 | 0.00% | -607.05 | 3.75% | Negative |
| 2024-10 | 3 | 0 | 3 | 0.00% | -526.06 | 3.38% | Negative |
| 2024-11 | 11 | 8 | 3 | 72.73% | 792.02 | 3.20% | Positive |
| 2024-12 | 12 | 6 | 6 | 50.00% | -414.39 | 4.49% | Negative |
| 2025-01 | 11 | 5 | 6 | 45.45% | 303.06 | 4.25% | Positive |
| 2025-02 | 3 | 0 | 3 | 0.00% | -495.09 | 3.15% | Negative |
| 2025-03 | 17 | 8 | 9 | 47.06% | -515.79 | 4.96% | Negative |
| 2025-04 | 9 | 3 | 6 | 33.33% | -649.55 | 6.23% | Negative |
| 2025-05 | 5 | 2 | 3 | 40.00% | 108.41 | 1.65% | Positive |
| 2025-06 | 1 | 0 | 1 | 0.00% | -163.60 | 1.15% | Negative |
| 2025-07 | 4 | 3 | 1 | 75.00% | -23.82 | 1.11% | Negative |
| 2025-08 | 1 | 1 | 0 | 100.00% | 115.14 | 0.00% | Positive |
| 2025-09 | 4 | 1 | 3 | 25.00% | -316.88 | 3.77% | Negative |
| 2025-10 | 4 | 3 | 1 | 75.00% | 107.44 | 1.14% | Positive |
| 2025-11 | 3 | 0 | 3 | 0.00% | -446.11 | 3.21% | Negative |
| 2025-12 | 9 | 6 | 3 | 66.67% | 326.98 | 3.29% | Positive |
| 2026-01 | 6 | 6 | 0 | 100.00% | 1101.18 | 0.00% | Positive |
| 2026-02 | 15 | 11 | 4 | 73.33% | 1244.98 | 2.23% | Positive |
| 2026-03 | 3 | 0 | 3 | 0.00% | -516.36 | 3.20% | Negative |
| 2026-04 | 6 | 0 | 6 | 0.00% | -381.21 | 2.44% | Negative |
| 2026-05 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2026-06 | 12 | 6 | 6 | 50.00% | 442.49 | 4.72% | Positive |

## 8. WALK-FORWARD OOS VALIDATION
- **OOS Verdict:** PASS
- **Combined OOS PnL:** $1799.11
- **Combined OOS Trades:** 378

| Period | PnL ($) | Trades | PF | DD |
|---|---|---|---|---|
| 2022-01-01->2022-12-31 | -258.37 | 113 | 0.95 | 20.73% |
| 2023-01-01->2023-12-31 | 1001.48 | 63 | 1.34 | 6.47% |
| 2024-01-01->2024-12-31 | 1146.78 | 110 | 1.21 | 14.34% |
| 2025-01-01->2026-06-28 | -90.78 | 92 | 0.98 | 14.93% |

## 9. STRESS TESTING RESULTS
| Scenario | PnL ($) | Trades | DD | +/-/0 Months | Verdict |
|---|---|---|---|---|---|
| normal | 5677.97 | 768 | 24.62% | 37/39/2 | **PASS** |
| double_fees | 2771.98 | 762 | 29.30% | 35/41/2 | **PASS** |
| triple_fees | -195.50 | 747 | 38.04% | 35/41/2 | **FAIL** |
| double_slippage | 4441.99 | 765 | 25.10% | 35/41/2 | **PASS** |
| triple_slippage | 2770.10 | 762 | 29.30% | 35/41/2 | **PASS** |
| double_fees_double_slippage | 1354.25 | 748 | 33.35% | 35/41/2 | **PASS** |
| delay_5m | 4480.19 | 839 | 23.00% | 36/40/2 | **PASS** |
| stale_skip_15m | 5677.97 | 768 | 24.62% | 37/39/2 | **PASS** |
| delay_1_candle | 4480.19 | 839 | 23.00% | 36/40/2 | **PASS** |
| delay_2_candles | 1499.16 | 824 | 17.36% | 37/39/2 | **PASS** |
| missed_fills_10 | 2420.06 | 704 | 22.56% | 34/42/2 | **PASS** |
| missed_fills_20 | 1809.01 | 698 | 33.73% | 34/41/3 | **PASS** |
| missed_fills_30 | 6196.31 | 667 | 20.94% | 39/34/5 | **PASS** |
| combined_adverse | 1227.93 | 747 | 27.44% | 36/40/2 | **PASS** |

## 10. REGIME PnL ATTRIBUTION (Candidate A)
| Regime | Net PnL ($) |
|---|---|
| regime_bull_trend | 5170.34 |
| regime_bear_trend | 1358.71 |
| regime_vol_expansion | 811.58 |
| regime_sideways_range | 0.00 |
| regime_toxic_chop | 0.00 |
| regime_funding_extreme | -25.10 |
| unknown | -238.84 |
| regime_vol_compression | -1316.61 |

## 11. COMPLIANCE & LOOKAHEAD AUDITS
- **signal_audit:** PASS
- **trade_audit:** PASS
- **no_fake_audit:** PASS

---
*Compiled by Antigravity Phase 8 Strategy Research System.*