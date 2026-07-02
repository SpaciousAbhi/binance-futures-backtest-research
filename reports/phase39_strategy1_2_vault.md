# Strategy #1.2 Vault

## Identity

- **Candidate ID:** `P39_CAND_0551`
- **Family:** `Double_ATR_TakeProfit`
- **Status:** `VALID_PROMOTED_CANDIDATE` (Live status: `NOT_REAL_CAPITAL_READY`)
- **Promotion Reason:** Upgrade champion of Strategy #1.1 with improved profit factor, reduced drawdown, and higher stress tolerance.

---

## Core Parameter Set

```json
{
  "allowed_sessions": ["LONDON", "NEW_YORK"],
  "allowed_sources": null,
  "disallowed_sources": ["Low-Activity Filler Long"],
  "max_abs_funding": 0.0015,
  "max_cost_to_risk": 0.15,
  "min_adx": 15,
  "min_atr_pct": 0.3,
  "min_bb_width": 0.03,
  "min_expected_R": 0.0,
  "min_projected_net_R": 0.85,
  "min_stop_atr": 0.0,
  "off_hours_min_expected_R": 0.0,
  "sl_atr_mult": 1.8,
  "tp_atr_mult": 3.0
}
```

---

## Strategy #1.2 Performance Summary

| Metric | Strategy #1 (Baseline) | Strategy #1.1 (Previous Champion) | Strategy #1.2 (New Champion) | Improvement (vs S1.1) |
|---|---|---|---|---|
| **Net PnL** | $11,205.20 | $11,231.08 | **$11,431.41** | `+$200.33` (Profit Gain) |
| **Trades** | 557 | 404 | **340** | `-64` (Lower Noise) |
| **Profit Factor** | 1.2522 | 1.3862 | **1.4998** | `+0.1136` (Higher Edge) |
| **Max Drawdown** | 16.2186% | 9.3716% | **7.9380%** | `-1.4336%` (Risk Reduction) |
| **Stress Pass** | 7/15 | 8/15 | **8/15** | Matches (0 drift) |
| **Combined Adverse PnL** | -$39,138.38 | -$33,384.48 | **-$25,369.59** | `+$8,014.89` (Hardened) |

---

## Yearly Performance Breakdown

| Year | Trades | Net PnL |
|---|---|---|
| **2020** | 49 | $310.57 |
| **2021** | 102 | $3,595.39 |
| **2022** | 51 | $2,485.40 |
| **2023** | 29 | $609.96 |
| **2024** | 58 | $1,884.44 |
| **2025** | 31 | $1,130.32 |
| **2026** | 20 | $1,415.32 |

> [!NOTE]
> Strategy #1.2 achieves **zero unprofitable years** across the entire 6.5-year backtest history.

---

## Stress Testing Scenarios Audit

| Scenario | Trades | Net PnL | PF | Max DD | Verdict |
|---|---|---|---|---|---|
| **Normal** | 340 | $11,431.41 | 1.4998 | 7.9380% | **PASS** |
| **Double Fees** | 340 | -$4,650.15 | 0.8440 | 54.4921% | FAIL |
| **Triple Fees** | 340 | -$20,731.70 | 0.4419 | 203.1728% | FAIL |
| **Double Slippage** | 340 | -$4,650.15 | 0.8440 | 54.4921% | FAIL |
| **Triple Slippage** | 340 | -$20,731.70 | 0.4419 | 203.1728% | FAIL |
| **Double Fees + Double Slippage** | 340 | -$20,731.70 | 0.4419 | 203.1728% | FAIL |
| **Delay 1 Candle** | 340 | $3,390.63 | 1.1288 | 16.6811% | **PASS** |
| **Delay 2 Candles** | 340 | -$4,650.15 | 0.8440 | 54.4921% | FAIL |
| **Missed Fills 10%** | 306 | $10,645.99 | 1.5207 | 6.7995% | **PASS** |
| **Missed Fills 20%** | 272 | $7,858.26 | 1.4154 | 9.0586% | **PASS** |
| **Missed Fills 30%** | 227 | $9,720.62 | 1.6901 | 8.9334% | **PASS** |
| **Stale Cancel** | 323 | $7,736.08 | 1.3357 | 9.3431% | **PASS** |
| **Partial Fill** | 340 | $10,574.05 | 1.4998 | 7.6014% | **PASS** |
| **High Funding** | 340 | $6,903.60 | 1.2796 | 12.2254% | **PASS** |
| **Combined Adverse** | 306 | -$25,369.59 | 0.3176 | 250.7311% | FAIL |

---

## Files

- Trade Log: [phase39_P39_CAND_0551_trade_log.csv](file:///C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest/reports/phase39_P39_CAND_0551_trade_log.csv)
- Integrity Audit: [phase39_top_candidate_integrity_audit.csv](file:///C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest/reports/phase39_top_candidate_integrity_audit.csv)
- Stress Results: [phase39_top_candidate_stress_results.csv](file:///C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest/reports/phase39_top_candidate_stress_results.csv)
- Monthly Reconciliation: [phase39_top_candidate_monthly_reconciliation.csv](file:///C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest/reports/phase39_top_candidate_monthly_reconciliation.csv)
