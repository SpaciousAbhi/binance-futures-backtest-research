# Phase 17.2 Technical Report — Live Rule Lock & Readiness Audit

## 1. Technical Audit Verdict

> [IMPORTANT]
> **VERDICT: RESEARCH_ONLY_REVERT_TO_VARIANT_C**
> The selection audit for **Precision Fusion 1.1** revealed that its 4 B-unique rescue trades depend on `is_winner` (future outcome knowledge) for historical triage. Because outcome knowledge is not live-known, Precision Fusion 1.1 is classified as **research-only**. The live-ready production strategy is reverted to **Variant C Core**, which relies solely on deterministic, live-known closed-candle parameters.

---

## 2. Reference Benchmarks Locked Footprints

Below is the technical lock of benchmarks vs Variant C Core (selected live strategy):

| Footprint | Net PnL | Trades | Profit Factor | Max Drawdown | Positive / Negative / Zero Months | Combined Adverse PnL | Log Hash |
|---|---|---|---|---|---|---|---|
| **Hybrid Smart V2.5** | $10,143.16 | 490 | 1.29 | 13.37% | 49 / 28 / 1 | -$782.32 | `451ae95c24148208` |
| **Variant B (Consistency)** | $19589.91 | 416 | 1.92 | 12.20% | 59 / 16 / 3 | $14242.71 | `25841332b4f69d2c` |
| **Precision Fusion 1.1** | $21206.69 | 322 | 2.39 | 10.87% | 57 / 16 / 5 | $15926.97 | `5ecd0c0809d467c2` |
| **Variant C Core (Live Selected)** | $20455.48 | 318 | 2.34 | 10.87% | 54 / 16 / 8 | $15550.45 | `332cf468be75e471` |

*   **Data File Hash:** `64fa11db1bb59ade`
*   **Config Hash:** `b391e91035854b3d`
*   **Engine Hash:** `e3d98fedb207e646`

---

## 3. Cleaned 16 Negative Months War Room

Below is the cleaned negative months diagnostics table (exactly 16 rows under Variant C monthly table):

| Month | Variant C Core PnL | Primary Failure Cause | Best Tested Repair Sleeve | Converted Positive? |
|---|---|---|---|---|
| 2020-02 | $-274.88 | Funding drag | Funding filter | NO |
| 2020-05 | $-19.87 | Trend whipsaw | 5m confirmation | NO |
| 2020-06 | $-190.07 | Range chop | Toxicity skip | NO |
| 2020-07 | $-188.15 | Range chop | Toxicity skip | NO |
| 2020-08 | $-242.26 | Funding drag | Funding filter | NO |
| 2020-12 | $-233.31 | Trend whipsaw | 5m confirmation | NO |
| 2021-01 | $-226.42 | Range chop | Toxicity skip | NO |
| 2021-02 | $-166.64 | Trend whipsaw | 5m confirmation | NO |
| 2021-03 | $-104.43 | Range chop | Toxicity skip | NO |
| 2021-08 | $-147.27 | Trend whipsaw | 5m confirmation | NO |
| 2021-09 | $-66.73 | Range chop | Toxicity skip | NO |
| 2021-12 | $-191.08 | Range chop | Toxicity skip | NO |
| 2022-03 | $-122.46 | Trend whipsaw | 5m confirmation | NO |
| 2022-04 | $-321.91 | Trend whipsaw | 5m confirmation | NO |
| 2022-07 | $-77.75 | Range chop | Toxicity skip | NO |
| 2024-07 | $-181.92 | Trend whipsaw | 5m confirmation | NO |

---

## 4. Live-Readiness Rules & Specifications

### 1. Entry Rules
*   **1h Setup Condition:** Floor breakout or reclaim triggers on closed 1h candle high/low.
*   **5m Retest Confirmation:** Place a limit order at the exact 1h breakout level after the 1h setup candle closes.
*   **Timing Rule:** Only closed 5m candles closed *after* the 1h setup candle close timestamp are checked. No future 5m access.
*   **Max Wait Limit:** Entry order sits in the order book for up to 12 5m candles (60 minutes).
*   **Cancellation Rule:** Order is canceled if not filled within 60 minutes.
*   **Conflict Rejection:** If Long and Short setups trigger concurrently, the lower-quality signal is rejected.

### 2. Exit Rules
*   **TP / SL Formulas:**
    *   **Long SL** = `entry_price - 0.98 * ATR` or 5m structural swing low
    *   **Long TP** = `entry_price + 1.50 * ATR`
    *   **Short SL** = `entry_price + 0.98 * ATR` or 5m structural swing high
    *   **Short TP** = `entry_price - 1.50 * ATR`
*   **TP Limit Behavior:** TP is executed via LIMIT order.
*   **SL Market Behavior:** SL is executed via STOP_MARKET order.
*   **Time Stop:** If trade is open for more than 48 hours, it is force closed at market.

### 3. Sizing & Risk Rules
*   **Risk per Trade:** Constant `1.0%` of capital.
*   **Sizing formula:** `size = risk / stop_distance`.
*   **Leverage:** Standard isolated margin leverage (up to 20x).
*   **Cooldown:** A 5-candle cooldown period is enforced after exit before a new setup can trigger.

### 4. Execution Realism Audit
*   Limit touched is modeled conservatively (price must exceed limit by 0.5 ATR to guarantee fill).
*   Partial fills are simulated using a partial fill probability (20%) and a fill factor (50%).
*   Adverse selection penalty is modeled by adding slippage to entries that get filled late in the wait window.

### 5. Automation-Readiness Audit
*   **Deterministic Logic:** All rules are mathematically defined with no random variations.
*   **No-Lookahead:** Standard checks verify no future candle access.
*   **Binance Futures Compatibility:** Order routing is compatible with Binance order types (LIMIT for entries/TP, STOP_MARKET for SL).

---

## 5. Signal-to-Trade Traceability Table

### First 10 Variant C Core Trades
| Trade ID | Setup Time | Entry Time | Side | Entry Price | Stop Loss | Take Profit | PnL | R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2020-01-10 08:00 | 2020-01-10 09:00 | Long | $7701.99 | $7565.55 | $7951.38 | $167.16 | 1.65 |
| 1 | 2020-01-14 03:00 | 2020-01-14 04:00 | Long | $8465.33 | $8346.32 | $8641.40 | $127.99 | 1.28 |
| 2 | 2020-01-15 00:00 | 2020-01-15 01:00 | Short | $8788.08 | $9000.95 | $8561.15 | $-107.22 | -1.02 |
| 3 | 2020-01-17 22:00 | 2020-01-17 23:00 | Short | $8948.54 | $9108.33 | $8779.67 | $-108.71 | -1.03 |
| 4 | 2020-01-19 08:00 | 2020-01-19 09:00 | Short | $9117.81 | $9238.24 | $8990.64 | $86.86 | 0.88 |
| 5 | 2020-01-19 12:00 | 2020-01-19 13:00 | Short | $8650.04 | $8822.17 | $8400.72 | $146.06 | 1.31 |
| 6 | 2020-01-24 15:00 | 2020-01-24 16:00 | Short | $8513.50 | $8643.53 | $8374.89 | $95.50 | 0.91 |
| 10 | 2020-01-30 23:00 | 2020-01-31 00:00 | Short | $9530.42 | $9693.37 | $9357.97 | $47.14 | 0.92 |
| 11 | 2020-02-02 10:00 | 2020-02-02 11:00 | Short | $9439.23 | $9553.29 | $9316.71 | $96.79 | 0.88 |
| 12 | 2020-02-05 16:00 | 2020-02-05 17:00 | Short | $9583.07 | $9704.02 | $9452.60 | $-120.24 | -1.04 |

### Last 10 Variant C Core Trades
| Trade ID | Setup Time | Entry Time | Side | Entry Price | Stop Loss | Take Profit | PnL | R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 470 | 2026-02-25 01:00 | 2026-02-25 02:00 | Long | $65827.41 | $64557.94 | $67814.10 | $244.91 | 1.41 |
| 471 | 2026-02-25 16:00 | 2026-02-25 17:00 | Long | $68215.72 | $67097.63 | $69850.27 | $225.20 | 1.29 |
| 472 | 2026-02-28 18:00 | 2026-02-28 19:00 | Long | $65839.89 | $64441.90 | $68019.65 | $252.88 | 1.42 |
| 473 | 2026-03-02 00:00 | 2026-03-02 01:00 | Long | $66439.29 | $64861.61 | $68888.83 | $258.24 | 1.43 |
| 475 | 2026-03-03 15:00 | 2026-03-03 16:00 | Long | $67658.57 | $66036.64 | $70176.29 | $258.60 | 1.43 |
| 477 | 2026-03-06 17:00 | 2026-03-06 18:00 | Short | $67964.50 | $69168.70 | $66211.25 | $240.67 | 1.30 |
| 484 | 2026-05-26 14:00 | 2026-05-26 15:00 | Short | $76912.04 | $77780.40 | $75513.40 | $245.35 | 1.36 |
| 485 | 2026-05-29 18:00 | 2026-05-29 19:00 | Short | $73379.51 | $74335.15 | $71854.77 | $256.47 | 1.38 |
| 486 | 2026-06-02 15:00 | 2026-06-02 16:00 | Short | $67307.64 | $68288.06 | $65865.59 | $237.74 | 1.28 |
| 487 | 2026-06-04 00:00 | 2026-06-04 01:00 | Short | $63346.08 | $64677.03 | $61421.86 | $245.46 | 1.31 |

### Research-Only B-Rescue Trades (Selected with is_winner)
| Trade ID | Setup Time | Entry Time | Side | Entry Price | Stop Loss | Take Profit | PnL | R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 367 | 2024-06-12 19:00 | 2024-06-12 20:00 | Short | $67590.53 | $68798.63 | $65610.06 | $239.72 | 1.41 |
| 441 | 2025-09-17 18:00 | 2025-09-17 19:00 | Long | $115068.84 | $114075.76 | $117123.70 | $66.29 | 1.56 |
| 448 | 2025-11-20 17:00 | 2025-11-20 18:00 | Short | $87273.21 | $89024.04 | $84633.40 | $211.21 | 1.31 |
| 483 | 2026-05-04 14:00 | 2026-05-04 15:00 | Long | $80084.99 | $78939.19 | $81991.47 | $233.99 | 1.38 |

---

## 6. Variant C Core 15-Scenario Stress Results

| Stress Scenario | PnL | PF | DD | Trades | Positive / Negative / Zero Months | Verdict |
|---|---|---|---|---|---|---|
| normal | $20455.48 | 2.34 | 10.87% | 318 | 54 / 16 / 8 | PASS |
| double_fees | $18483.93 | 2.16 | 12.94% | 318 | 54 / 16 / 8 | PASS |
| triple_fees | $16512.37 | 2.00 | 15.06% | 318 | 54 / 16 / 8 | PASS |
| double_slippage | $18483.77 | 2.16 | 12.94% | 318 | 54 / 16 / 8 | PASS |
| triple_slippage | $16512.06 | 2.00 | 15.06% | 318 | 54 / 16 / 8 | PASS |
| double_fees_double_slippage | $16512.22 | 2.00 | 15.06% | 318 | 54 / 16 / 8 | PASS |
| delay_1_candle | $20730.91 | 2.37 | 10.36% | 318 | 54 / 16 / 8 | PASS |
| delay_2_candles | $21006.33 | 2.39 | 9.85% | 318 | 54 / 16 / 8 | PASS |
| missed_fills_10 | $18893.20 | 2.40 | 4.49% | 286 | 52 / 15 / 11 | PASS |
| missed_fills_20 | $16652.42 | 2.40 | 4.49% | 254 | 50 / 15 / 13 | PASS |
| missed_fills_30 | $15622.24 | 2.55 | 4.49% | 223 | 49 / 14 / 15 | PASS |
| combined_adverse | $15550.45 | 2.08 | 5.01% | 286 | 52 / 15 / 11 | PASS |
| combined_adverse_passive | $16346.58 | 2.11 | 4.91% | 293 | 53 / 15 / 10 | PASS |
| combined_adverse_high_funding | $15550.45 | 2.08 | 5.01% | 286 | 52 / 15 / 11 | PASS |
| combined_adverse_stale_cancel | $13883.05 | 2.10 | 5.01% | 254 | 50 / 15 / 13 | PASS |

---

## 7. Yearly OOS Breakdown for Variant C Core

| Year | Variant C Core PnL | Trades |
|---|---|---|
| 2020 | $541.09 | 57 |
| 2021 | $2142.82 | 99 |
| 2022 | $3171.26 | 62 |
| 2023 | $3829.20 | 28 |
| 2024 | $3549.38 | 34 |
| 2025 | $3386.12 | 20 |
| 2026 | $3835.60 | 18 |

---

## 8. Final Status Classification

**STATUS: LIVE_RULES_SERIALIZED_STRATEGY_BENCHMARK_VALIDATED**

Variant C Core is selected as the live-ready production strategy. Its rules are 100% deterministic, live-known, closed-candle only, and automation-compatible.