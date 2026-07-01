# Phase 20.1 Technical Report — Full Audit & Proof Lock

## 1. Technical Audit Verdict

> [IMPORTANT]
> **VERDICT: AUDIT_PARTIAL_PASS_PRECISION_FUSION_VERIFIED_PHASE20_SCALE_UNPROVEN**
> **STATUS: LIVE_RULES_SERIALIZED_STRATEGY_BENCHMARK_VALIDATED**
> **READY_FOR_PHASE18_NEGATIVE_MONTH_REPAIR**
> **NOT_YET_READY_FOR_REAL_CAPITAL_LIVE_AUTOMATION**
> *The core strategy Precision Fusion 1.2 is 100% verified and reproducible from code. However, the Phase 20 claims regarding the 100,000 template sweep, ETH/SOL validation data, and MFE/MAE mechanism dataset were simulated/placeholder reports and have no registry or database evidence.*

---

## 2. Reconciliation Table

| Claimed Metric | Source File | Reproduced Metric | Match? | Proof Hash | Issue Found |
|---|---|---|---|---|---|
| Net PnL: $21,684.99 | reports/phase20_mechanism_first_100k_template_research_report.md | $21684.99 | YES | `6729d5e0eb3adaaa` | None |
| Trades Count: 325 | reports/phase20_mechanism_first_100k_template_research_report.md | 325 | YES | `6729d5e0eb3adaaa` | None |
| Profit Factor: 2.42 | reports/phase20_mechanism_first_100k_template_research_report.md | 2.42 | YES | `6729d5e0eb3adaaa` | None |
| Max Drawdown: 10.87% | reports/phase20_mechanism_first_100k_template_research_report.md | 10.87% | YES | `6729d5e0eb3adaaa` | None |
| 100k templates sweep | reports/phase20_mechanism_first_100k_template_research_report.md | N/A | NO | None | Placeholder/Simulated count (No template registry exists) |
| ETH/SOL validation | reports/phase20_mechanism_first_100k_template_research_report.md | N/A | NO | None | Placeholder/Simulated cross-market test (No data files exist) |
| MFE/MAE mechanism dataset | reports/phase20_mechanism_first_100k_template_research_report.md | N/A | NO | None | Placeholder/Simulated dataset (No CSV rows generated) |

---

## 3. Precision Fusion 1.2 Full Reproduction Proof

*   **Reproduction Command:** `python src/research/phase20_1_runner.py`
*   **Start Timestamp:** `2026-07-01 14:11:21`
*   **End Timestamp:** `2026-07-01 14:11:41`
*   **Wall-Clock Runtime:** `20.7653 seconds`
*   **Data File Hash (BTCUSDT_1h_processed.csv):** `64fa11db1bb59ade`
*   **Config Hash:** `b391e91035854b3d`
*   **Engine Hash:** `e3d98fedb207e646`
*   **Strategy Hash:** `82d9ca669f737d59`
*   **Trade Log Hash:** `6729d5e0eb3adaaa`
*   **Monthly Table Hash:** `2d8aa4bbff707a09`
*   **Stress Table Hash:** `4201403d8bfa1def`

---

## 4. Precision Fusion 1.2 Trade Audit

*   **Total Trades Count:** `325`
*   **Long/Short Split:** `114 Longs / 211 Shorts`
*   **Wins/Losses Split:** `212 Wins / 113 Losses`
*   **Average Winner / Average Loser:** `$174.40 / $-135.29`
*   **Expectancy:** `$66.72`

### Signal-to-Trade Traceability

#### First 10 trades
| Trade ID | Source | Setup Time | Entry Time | Side | Entry Price | Stop Loss | Take Profit | PnL | R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Variant C Core | 2020-01-10 08:00 | 2020-01-10 09:00 | Long | $7701.99 | $7565.55 | $7951.38 | $167.16 | 1.65 |
| 1 | Variant C Core | 2020-01-14 03:00 | 2020-01-14 04:00 | Long | $8465.33 | $8346.32 | $8641.40 | $127.99 | 1.28 |
| 2 | Variant C Core | 2020-01-15 00:00 | 2020-01-15 01:00 | Short | $8788.08 | $9000.95 | $8561.15 | $-107.22 | -1.02 |
| 3 | Variant C Core | 2020-01-17 22:00 | 2020-01-17 23:00 | Short | $8948.54 | $9108.33 | $8779.67 | $-108.71 | -1.03 |
| 4 | Variant C Core | 2020-01-19 08:00 | 2020-01-19 09:00 | Short | $9117.81 | $9238.24 | $8990.64 | $86.86 | 0.88 |
| 5 | Variant C Core | 2020-01-19 12:00 | 2020-01-19 13:00 | Short | $8650.04 | $8822.17 | $8400.72 | $146.06 | 1.31 |
| 6 | Variant C Core | 2020-01-24 15:00 | 2020-01-24 16:00 | Short | $8513.50 | $8643.53 | $8374.89 | $95.50 | 0.91 |
| 10 | Variant C Core | 2020-01-30 23:00 | 2020-01-31 00:00 | Short | $9530.42 | $9693.37 | $9357.97 | $47.14 | 0.92 |
| 11 | Variant C Core | 2020-02-02 10:00 | 2020-02-02 11:00 | Short | $9439.23 | $9553.29 | $9316.71 | $96.79 | 0.88 |
| 12 | Variant C Core | 2020-02-05 16:00 | 2020-02-05 17:00 | Short | $9583.07 | $9704.02 | $9452.60 | $-120.24 | -1.04 |

#### Last 10 trades
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

---

## 5. Expected R Formula Audit

*   **Formula in code:**
    `expected R = expected reward distance / stop distance`
    Where Expected reward distance is TP ATR expansion, and stop distance is SL ATR contraction.
*   **Rate to price units conversion:** Rounded according to step and tick sizes before execution routing.
*   **Funding inclusion:** Dynamic carrying costs are evaluated as a separate execution filter, not within Expected R.

---

## 6. Phase 20 100k Template Claim Audit

> [WARNING]
> **CLAIM STATUS: UNPROVEN**
> No actual template registry file, database, or generation scripts exist in the repository workspace. The claimed Stage 1 to 6 counts and 100k template results were simulated/placeholder values printed in the report block. No template database was actually generated.

---

## 7. Runtime Plausibility Audit

*   **Actual backtest runtime:** ~0.08 seconds per backtest.
*   **12,580 full backtests runtime requirement:** `12,580 * 0.08 = 1,006.4 seconds (~16.7 minutes)` on a single core.
*   **Plausibility conclusion:** Suspiciously fast runtime in Phase 20 confirm that the 100k sweep was not executed live on this machine.

---

## 8. Multi-Asset Validation Audit

> [WARNING]
> **CLAIM STATUS: MULTI_ASSET_VALIDATION_NOT_PROVEN**
> No ETHUSDT or SOLUSDT processed data files exist in `data/processed/` or `data/raw/` directories, and no cross-asset run logs exist.

---

## 9. AI-Proposed Ideas Audit

> [WARNING]
> **CLAIM STATUS: AI_PROPOSED_RESEARCH_TOO_SHALLOW**
> Only one AI idea (Volume Impulse Retest Sleeve) was proposed textually, and no actual python code implementation or test runner script exists for it.

---

## 10. Precision Fusion 1.2 15-Scenario Stress Results

| Stress Scenario | PnL | PF | DD | Trades | Positive / Negative / Zero Months | Verdict |
|---|---|---|---|---|---|---|
| normal | $21684.99 | 2.42 | 10.87% | 325 | 56 / 16 / 6 | PASS |
| double_fees | $19668.94 | 2.24 | 12.94% | 325 | 56 / 16 / 6 | PASS |
| triple_fees | $17652.90 | 2.07 | 15.06% | 325 | 56 / 16 / 6 | PASS |
| double_slippage | $19668.79 | 2.24 | 12.94% | 325 | 56 / 16 / 6 | PASS |
| triple_slippage | $17652.60 | 2.07 | 15.06% | 325 | 56 / 16 / 6 | PASS |
| double_fees_double_slippage | $17652.75 | 2.07 | 15.06% | 325 | 56 / 16 / 6 | PASS |
| delay_1_candle | $21969.16 | 2.45 | 10.36% | 325 | 56 / 16 / 6 | PASS |
| delay_2_candles | $22253.33 | 2.48 | 9.85% | 325 | 56 / 16 / 6 | PASS |
| missed_fills_10 | $19350.89 | 2.42 | 3.16% | 292 | 55 / 15 / 8 | PASS |
| missed_fills_20 | $16624.58 | 2.35 | 3.16% | 260 | 52 / 16 / 10 | PASS |
| missed_fills_30 | $14897.10 | 2.40 | 3.16% | 227 | 50 / 16 / 12 | PASS |
| combined_adverse | $15922.97 | 2.09 | 3.71% | 292 | 55 / 15 / 8 | PASS |
| combined_adverse_passive | $17184.29 | 2.17 | 3.57% | 299 | 57 / 15 / 6 | PASS |
| combined_adverse_high_funding | $15922.97 | 2.09 | 3.71% | 292 | 55 / 15 / 8 | PASS |
| combined_adverse_stale_cancel | $13756.92 | 2.04 | 3.64% | 260 | 52 / 16 / 10 | PASS |

---

## 11. Yearly OOS Breakdown for Precision Fusion 1.2

| Year | Precision Fusion 1.2 PnL | Trades |
|---|---|---|
| 2020 | $541.09 | 57 |
| 2021 | $2228.07 | 100 |
| 2022 | $3171.26 | 62 |
| 2023 | $3829.20 | 28 |
| 2024 | $4004.63 | 36 |
| 2025 | $4075.12 | 24 |
| 2026 | $3835.60 | 18 |

---

## 12. Final Corrective Action List

1. Fix all status labels in reports to avoid outdated 'READY_FOR_PHASE18' tags.
2. Mark the 100,000 templates, cross-market validation, and mechanism datasets as research placeholders.
3. Focus Phase 21 on building a real, executable live-known 1,000+ candidate search engine.