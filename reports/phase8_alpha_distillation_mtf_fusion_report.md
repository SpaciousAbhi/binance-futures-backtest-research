# Phase 8 -- Alpha Distillation, Multi-Candidate Fusion,
## Dynamic Exits, and Bad-Month Conversion Research

**Date:** 2026-06-30 07:53:31 UTC
**Symbol:** BTCUSDT USD-M Perpetual Futures (Binance)
**Data range:** 2020-01-01 -> 2026-06-28
**Primary eval frame:** 5m MTF aligned frame df_tf (682,561 candles)

---
## EXECUTIVE VERDICT

> [!CAUTION]
> **VERDICT: FAIL_NO_STRATEGY_FOUND**
> Best system: Candidate A Baseline (Phase 6 Portfolio, no_throttle)
> - Negative months: 39 (target: 0)
> - Zero months:     9 (target: 0)
> - Total trades:    878 (target: >=780)

> [!IMPORTANT]
> **Root cause of Phase 8 initial regression**: Phase 8 originally ran on the 5m MTF-aligned frame.
> On 5m data, bb_width > 0.06 fires only ~293 raw signals over 6.5 years,
> yielding 181 trades and -$3,915 PnL -- a false regression vs Phase 7.
> Phase 7 Baseline A (731 trades, +$6,577) was evaluated on the 1h frame
> where bb_width > 0.06 hits 8,415 candles (14.8%) -- matching the trade count.
> Phase 8 corrected to use 1h as primary evaluation frame.

## 1. LOCKED CHAMPION CANDIDATE BANK (df_tf evaluation, Reproducibility Check)
| Candidate | Role | Net PnL ($) | DD | PF | Trades | +/-/0 Months |
|---|---|---|---|---|---|---|
| A | Phase 6 Portfolio (Activity Champion) | 13989.44 | 22.54% | 1.25 | 878 | 30/39/9 |
| C | Phase-5 Single (PF/DD Champion) | 6467.76 | 9.81% | 1.29 | 331 | 39/31/8 |
| D | Range Reclaim Filler (Zero-Month Rescue) | 91.57 | 16.22% | 1.02 | 85 | 24/27/27 |
| E | Delay-1 Variant (Confirmation) | 7191.70 | 13.26% | 1.24 | 420 | 44/26/8 |

## 2. MONTHLY COMPLEMENT MATRIX
_(i_helps_j = months candidate i is positive when j is negative)_
| | A | C | D | E |
|---|---|---|---|---|
| **A** | -- | i_helps=3, both_neg=28 | i_helps=10, both_neg=14 | i_helps=1, both_neg=25 |
| **C** | i_helps=11, both_neg=28 | -- | i_helps=13, both_neg=11 | i_helps=4, both_neg=22 |
| **D** | i_helps=10, both_neg=14 | i_helps=8, both_neg=11 | -- | i_helps=9, both_neg=10 |
| **E** | i_helps=14, both_neg=25 | i_helps=9, both_neg=22 | i_helps=14, both_neg=10 | -- |

## 3. DYNAMIC EXIT VARIANT RESULTS
| Exit Mode | Net PnL ($) | PF | DD | Trades | +/-/0 Months | Score |
|---|---|---|---|---|---|---|
| * Static SL/TP | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |
| Trail 1.5 ATR | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |
| Trail 2.0 ATR | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |
| Trail 2.5 ATR | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |
| Breakeven 1.0 ATR | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |
| Breakeven 1.5 ATR | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |
| Trail+BE 1.5/1.0 | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |
| Trail+BE 2.0/1.0 | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |
| Trail+BE 2.5/1.5 | 5236.09 | 1.19 | 13.81% | 422 | 42/28/8 | -44702.04 |

## 4. FUSION MODEL RESULTS
| Rank | Model | Net PnL ($) | PF | DD | Trades | +/-/0 Months | Score |
|---|---|---|---|---|---|---|---|
| 1 | * F-A: Top-3 Union (cancel) | 13989.44 | 1.25 | 22.54% | 878 | 30/39/9 | -8435.96 |
| 2 | F-B: Top-3 Union (long-priority) | 13989.44 | 1.25 | 22.54% | 878 | 30/39/9 | -8435.96 |
| 3 | F-C: Intersection >=2 | 13989.44 | 1.25 | 22.54% | 878 | 30/39/9 | -8435.96 |
| 4 | F-D: Regime Switching Top-3 | 13989.44 | 1.25 | 22.54% | 878 | 30/39/9 | -8435.96 |
| 5 | F-E: Top-3 + Filler (zero-rescue) | 10883.22 | 1.19 | 24.41% | 903 | 33/43/2 | -11460.84 |
| 6 | F-F: Top-3 + Filler + Regime Switch | 10883.22 | 1.19 | 24.41% | 903 | 33/43/2 | -11460.84 |
| 7 | F-G: Single C + Filler | 9009.94 | 1.22 | 24.99% | 497 | 40/36/2 | -31990.01 |

## 5. MTD THROTTLE OPTIMIZATION
| Mode | Net PnL ($) | PF | DD | Trades | +/-/0 Months | Score |
|---|---|---|---|---|---|---|
| * no_throttle | 10883.22 | 1.19 | 24.41% | 903 | 33/43/2 | -11460.84 |
| emergency_pause | 10883.22 | 1.19 | 24.41% | 903 | 33/43/2 | -11460.84 |
| soft | 10265.10 | 1.19 | 24.44% | 896 | 30/45/3 | -13379.31 |
| hard | 9693.93 | 1.20 | 25.07% | 884 | 30/45/3 | -13956.77 |
| medium | 8368.87 | 1.18 | 23.88% | 859 | 29/46/3 | -15769.93 |

## 6. CHOSEN PHASE 8 SYSTEM
**System:** Candidate A Baseline (Phase 6 Portfolio, no_throttle)
- Net PnL: **$13989.44**
- Win Rate: 52.05%
- Profit Factor: 1.25
- Max Drawdown: 22.54%
- Total Trades: 878
- +/-/0 Months: 30 / 39 / 9
- Score: -8435.96
- Best Month: $3829.78  /  Worst Month: $-1203.06
- Avg Winner: $152.09  /  Avg Loser: $-131.87
- Avg R: 0.22  /  Avg Hold Candles: 199.6

## 7. CHOSEN SYSTEM -- MONTH-BY-MONTH BREAKDOWN
| Month | Trades | Wins | Losses | Win Rate | Net PnL ($) | DD | Status |
|---|---|---|---|---|---|---|---|
| 2020-01 | 17 | 7 | 10 | 41.18% | -308.17 | 5.48% | Negative |
| 2020-02 | 5 | 0 | 5 | 0.00% | -356.65 | 3.68% | Negative |
| 2020-03 | 44 | 26 | 18 | 59.09% | 758.79 | 6.56% | Positive |
| 2020-04 | 27 | 21 | 6 | 77.78% | 2075.95 | 2.15% | Positive |
| 2020-05 | 3 | 0 | 3 | 0.00% | -411.44 | 3.38% | Negative |
| 2020-06 | 6 | 0 | 6 | 0.00% | -375.68 | 3.19% | Negative |
| 2020-07 | 6 | 3 | 3 | 50.00% | -250.08 | 3.15% | Negative |
| 2020-08 | 7 | 0 | 7 | 0.00% | -242.45 | 2.18% | Negative |
| 2020-09 | 15 | 12 | 3 | 80.00% | 777.82 | 3.10% | Positive |
| 2020-10 | 8 | 3 | 5 | 37.50% | -403.17 | 5.30% | Negative |
| 2020-11 | 8 | 3 | 5 | 37.50% | -396.49 | 5.37% | Negative |
| 2020-12 | 23 | 8 | 15 | 34.78% | -78.78 | 5.36% | Negative |
| 2021-01 | 12 | 6 | 6 | 50.00% | -505.07 | 5.63% | Negative |
| 2021-02 | 6 | 0 | 6 | 0.00% | -268.69 | 2.61% | Negative |
| 2021-03 | 4 | 1 | 3 | 25.00% | -303.84 | 3.19% | Negative |
| 2021-04 | 19 | 14 | 5 | 73.68% | 1104.81 | 2.55% | Positive |
| 2021-05 | 62 | 32 | 30 | 51.61% | 1089.65 | 8.01% | Positive |
| 2021-06 | 53 | 26 | 27 | 49.06% | -244.17 | 10.44% | Negative |
| 2021-07 | 9 | 7 | 2 | 77.78% | 892.15 | 1.08% | Positive |
| 2021-08 | 22 | 14 | 8 | 63.64% | 889.98 | 4.11% | Positive |
| 2021-09 | 17 | 8 | 9 | 47.06% | 720.36 | 5.35% | Positive |
| 2021-10 | 21 | 14 | 7 | 66.67% | 1354.63 | 5.91% | Positive |
| 2021-11 | 22 | 13 | 9 | 59.09% | 359.95 | 4.42% | Positive |
| 2021-12 | 22 | 11 | 11 | 50.00% | 25.05 | 6.22% | Positive |
| 2022-01 | 3 | 0 | 3 | 0.00% | -507.95 | 3.19% | Negative |
| 2022-02 | 31 | 23 | 8 | 74.19% | 2830.14 | 6.41% | Positive |
| 2022-03 | 12 | 8 | 4 | 66.67% | 407.01 | 4.26% | Positive |
| 2022-04 | 3 | 0 | 3 | 0.00% | -605.60 | 3.25% | Negative |
| 2022-05 | 26 | 12 | 14 | 46.15% | 115.09 | 9.96% | Positive |
| 2022-06 | 9 | 3 | 6 | 33.33% | -1005.59 | 6.46% | Negative |
| 2022-07 | 9 | 3 | 6 | 33.33% | -655.14 | 3.82% | Negative |
| 2022-08 | 6 | 3 | 3 | 50.00% | 50.38 | 1.63% | Positive |
| 2022-09 | 3 | 0 | 3 | 0.00% | -534.29 | 3.23% | Negative |
| 2022-10 | 3 | 0 | 3 | 0.00% | -134.41 | 0.84% | Negative |
| 2022-11 | 18 | 9 | 9 | 50.00% | 621.33 | 3.45% | Positive |
| 2022-12 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2023-01 | 15 | 9 | 6 | 60.00% | 402.39 | 3.18% | Positive |
| 2023-02 | 8 | 6 | 2 | 75.00% | 1140.74 | 1.06% | Positive |
| 2023-03 | 27 | 22 | 5 | 81.48% | 3829.78 | 3.39% | Positive |
| 2023-04 | 8 | 2 | 6 | 25.00% | -551.67 | 4.94% | Negative |
| 2023-05 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2023-06 | 3 | 0 | 3 | 0.00% | -711.13 | 3.34% | Negative |
| 2023-07 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2023-08 | 9 | 3 | 6 | 33.33% | -802.79 | 3.90% | Negative |
| 2023-09 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2023-10 | 6 | 3 | 3 | 50.00% | -236.23 | 3.14% | Negative |
| 2023-11 | 6 | 0 | 6 | 0.00% | -477.45 | 2.44% | Negative |
| 2023-12 | 6 | 3 | 3 | 50.00% | -550.24 | 3.33% | Negative |
| 2024-01 | 6 | 0 | 6 | 0.00% | -474.16 | 2.56% | Negative |
| 2024-02 | 14 | 14 | 0 | 100.00% | 2866.30 | 0.00% | Positive |
| 2024-03 | 13 | 6 | 7 | 46.15% | -550.71 | 5.37% | Negative |
| 2024-04 | 14 | 6 | 8 | 42.86% | -225.05 | 4.66% | Negative |
| 2024-05 | 11 | 5 | 6 | 45.45% | 457.76 | 3.28% | Positive |
| 2024-06 | 3 | 0 | 3 | 0.00% | -82.25 | 0.40% | Negative |
| 2024-07 | 5 | 0 | 5 | 0.00% | -265.87 | 1.30% | Negative |
| 2024-08 | 20 | 14 | 6 | 70.00% | 1238.29 | 6.39% | Positive |
| 2024-09 | 5 | 0 | 5 | 0.00% | -578.97 | 2.69% | Negative |
| 2024-10 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2024-11 | 17 | 11 | 6 | 64.71% | 1156.82 | 4.82% | Positive |
| 2024-12 | 9 | 3 | 6 | 33.33% | -1203.06 | 6.37% | Negative |
| 2025-01 | 11 | 5 | 6 | 45.45% | 16.34 | 4.26% | Positive |
| 2025-02 | 3 | 0 | 3 | 0.00% | -657.42 | 3.15% | Negative |
| 2025-03 | 17 | 8 | 9 | 47.06% | -679.48 | 4.98% | Negative |
| 2025-04 | 9 | 3 | 6 | 33.33% | -863.72 | 6.23% | Negative |
| 2025-05 | 3 | 0 | 3 | 0.00% | -310.15 | 1.66% | Negative |
| 2025-06 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2025-07 | 3 | 3 | 0 | 100.00% | 177.31 | 0.00% | Positive |
| 2025-08 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2025-09 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2025-10 | 6 | 6 | 0 | 100.00% | 1111.33 | 0.00% | Positive |
| 2025-11 | 3 | 0 | 3 | 0.00% | -631.98 | 3.21% | Negative |
| 2025-12 | 9 | 6 | 3 | 66.67% | 459.98 | 3.30% | Positive |
| 2026-01 | 6 | 6 | 0 | 100.00% | 1561.07 | 0.00% | Positive |
| 2026-02 | 21 | 17 | 4 | 80.95% | 3628.83 | 2.23% | Positive |
| 2026-03 | 3 | 0 | 3 | 0.00% | -787.85 | 3.19% | Negative |
| 2026-04 | 6 | 0 | 6 | 0.00% | -581.48 | 2.43% | Negative |
| 2026-05 | 0 | 0 | 0 | 0.00% | 0.00 | 0.00% | Zero |
| 2026-06 | 12 | 6 | 6 | 50.00% | 678.71 | 4.73% | Positive |

## 8. WALK-FORWARD OOS VALIDATION
- **OOS Verdict:** PASS
- **Combined OOS PnL:** $5458.67
- **Combined OOS Trades:** 475

| Period | PnL ($) | Trades | PF | DD |
|---|---|---|---|---|
| 2022-01-01->2022-12-31 | 2937.77 | 147 | 1.37 | 21.25% |
| 2023-01-01->2023-12-31 | 1116.66 | 82 | 1.28 | 13.75% |
| 2024-01-01->2024-12-31 | 425.80 | 126 | 1.07 | 13.65% |
| 2025-01-01->2026-06-28 | 978.44 | 120 | 1.19 | 18.33% |

## 9. STRESS TESTING RESULTS
| Scenario | PnL ($) | Trades | DD | +/-/0 Months | Verdict |
|---|---|---|---|---|---|
| normal | 10883.22 | 903 | 24.41% | 33/43/2 | **PASS** |
| double_fees | 6315.80 | 880 | 24.12% | 30/45/3 | **PASS** |
| triple_fees | 3101.32 | 859 | 30.46% | 29/46/3 | **PASS** |
| double_slippage | 8450.47 | 882 | 22.81% | 31/44/3 | **PASS** |
| triple_slippage | 6100.39 | 881 | 24.23% | 30/45/3 | **PASS** |
| double_fees_double_slippage | 4439.30 | 871 | 27.50% | 30/45/3 | **PASS** |
| delay_5m | 7911.87 | 859 | 21.11% | 35/41/2 | **PASS** |
| stale_skip_15m | 10883.22 | 903 | 24.41% | 33/43/2 | **PASS** |
| delay_1_candle | 7911.87 | 859 | 21.11% | 35/41/2 | **PASS** |
| delay_2_candles | 4707.94 | 838 | 30.75% | 34/42/2 | **PASS** |
| missed_fills_10 | 9320.26 | 871 | 20.43% | 31/45/2 | **PASS** |
| missed_fills_20 | 13912.46 | 845 | 28.13% | 30/44/4 | **PASS** |
| missed_fills_30 | 8427.11 | 764 | 23.74% | 33/42/3 | **PASS** |
| combined_adverse | 3004.18 | 797 | 29.79% | 28/47/3 | **PASS** |

## 10. REGIME PnL ATTRIBUTION (Candidate A)
| Regime | Net PnL ($) |
|---|---|
| regime_bull_trend | 8561.12 |
| regime_bear_trend | 6688.62 |
| regime_toxic_chop | 0.00 |
| unknown | 0.00 |
| regime_vol_expansion | -52.12 |
| regime_funding_extreme | -286.72 |
| regime_vol_compression | -296.73 |
| regime_sideways_range | -624.73 |

## 11. COMPLIANCE & LOOKAHEAD AUDITS
- **signal_audit:** PASS
- **trade_audit:** PASS
- **no_fake_audit:** PASS

---
*Compiled by Antigravity Phase 8 Strategy Research System.*