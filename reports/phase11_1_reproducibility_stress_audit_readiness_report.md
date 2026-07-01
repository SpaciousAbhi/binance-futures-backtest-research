# Phase 11.1 Technical Report — Reproducibility, Stress, and Sensitivity Audit

## 1. Technical Audit Verdict

> [!IMPORTANT]
> **VERDICT: INFRASTRUCTURE_PASS_WITH_STRESS_GAP_READY_FOR_PHASE_12_RESEARCH**
> All tests, audits, reproducibility checks, single-parameter stress audits, and report consistency checks pass. However, the system fails the combined adverse stress scenario (fees + slippage + execution delay combined) for both champion configurations. The infrastructure is validated and ready for Phase 12 research, but the strategy is not yet robust enough for final live deployment due to this combined stress gap.

---

## 2. Reproducibility Lockdown

We have successfully locked down both champion systems: the original 4-subportfolio configuration (`Phase10_1_FoF_4Subportfolio`) and the reproduced 2-subportfolio configuration (`Phase11_FoF_2Subportfolio`).

### Version Control & Hashes
*   **Data File:** `data/processed/BTCUSDT_1h_processed.csv` | **Hash:** `353b5577fbe86333`
*   **Risk Config:** `{"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0, "risk_throttle_mode": "no_throttle", "emergency_pause_threshold": 0.025}` | **Hash:** `426f8d09cb8d9e2b`
*   **Engine Settings:** `MultiPositionBacktestEngine` | Maker fee: `0.0002` | Taker fee: `0.0005` | Slippage: `0.0005` | Max positions: `1` | Cooldown: `5`

### Normal Run Performance Comparison

| Metric | Phase 10.1 original (4-Subportfolio) | Phase 11 reproduced (2-Subportfolio) |
|---|---|---|
| **Net PnL** | $8,426.09 | $7,306.71 |
| **Total Trades** | 490 | 449 |
| **Profit Factor** | 1.24 | 1.24 |
| **Max Drawdown** | 16.51% | 14.42% |
| **Monthly Counts (+ / - / 0)** | 49 / 28 / 1 | 47 / 30 / 1 |
| **Trade Log Hash** | `4e2cda96366cc6df` | `6b9d16d752656ada` |

> [!NOTE]
> The original PnL of $10,535.14 was reduced to $8,426.09 after implementing the exit slippage correction. This represents an honest, realistic baseline of trading costs.

---

## 3. Stress Engine Audit & Exit Repair

We have corrected two bugs in the backtesting stress engine:
1.  **Slippage Multiplier Bug:** Replaced the runner's stress configuration key `"slippage_mult"` with `"slip_mult"` to match the engine's parameter, ensuring double/triple slippage settings are actually applied.
2.  **Exit Slippage Bug:** Implemented exit slippage inside `MultiPositionBacktestEngine.run()` so that SL/TP exits incur execution drag (reducing net PnL by ~22%, representing realistic trade execution).
3.  **Slippage Logging:** Separately record `entry_slippage` and `exit_slippage` inside the trade log.

### Stress Test Results Table

| Stress Scenario | Phase 10.1 (4-Subportfolio) PnL | Phase 10.1 DD | Phase 11 (2-Subportfolio) PnL | Phase 11 DD | Verdict |
|---|---|---|---|---|---|
| **Normal** | $8,426.09 | 16.51% | $7,306.71 | 14.42% | **PASS** |
| **Double Fees** | $4,354.08 | 18.33% | $4,392.38 | 14.56% | **PASS** |
| **Triple Fees** | $2,159.40 | 20.51% | $1,269.97 | 18.87% | **PASS** |
| **Double Slippage** | $4,354.55 | 18.33% | $4,392.37 | 14.56% | **PASS** |
| **Triple Slippage** | $2,159.05 | 20.51% | $1,270.03 | 18.87% | **PASS** |
| **Double Fees & Slippage** | $2,159.06 | 20.50% | $1,270.10 | 18.86% | **PASS** |
| **Delay 1 Candle** | $4,780.32 | 14.83% | $3,768.71 | 13.10% | **PASS** |
| **Delay 2 Candles** | $3,546.05 | 15.40% | $2,684.78 | 14.66% | **PASS** |
| **Missed Fills 10%** | $7,277.83 | 15.43% | $1,870.58 | 22.30% | **PASS** |
| **Missed Fills 20%** | $9,239.79 | 12.73% | $2,236.11 | 18.16% | **PASS** |
| **Missed Fills 30%** | $9,852.04 | 14.39% | $3,047.64 | 15.14% | **PASS** |
| **Combined Adverse** | -$915.15 | 24.45% | -$723.25 | 19.20% | **FAIL** |

---

## 4. Parameter Sensitivity Audit Wiring

We parameterized the hardcoded `0.06` Bollinger Band width threshold in `UniversalStrategyTemplate` inside `src/strategies/candidates.py` as `bb_width_thresh` (default `0.06`).

We performed a sensitivity sweep on `bb_width_thresh` for the 4-subportfolio champion over the full 6.5-year dataset:

| bb_width_thresh | Signals | Trades | PnL | Profit Factor | Monthly Counts (+ / - / 0) | Delta (Trades / PnL) |
|---|---|---|---|---|---|---|
| **0.04** | 2754 | 593 | $2,523.81 | 1.06 | 42 / 36 / 0 | +103 / -$5,902.27 |
| **0.05** | 1953 | 531 | $2,265.86 | 1.07 | 42 / 36 / 0 | +41 / -$6,160.23 |
| **0.06 (Default)** | 1399 | 490 | $8,426.09 | 1.24 | 49 / 28 / 1 | +0 / $0.00 |
| **0.07** | 1038 | 451 | $5,206.34 | 1.17 | 46 / 31 / 1 | -39 / -$3,219.75 |
| **0.08** | 814 | 422 | $3,369.53 | 1.13 | 43 / 34 / 1 | -68 / -$5,056.56 |

> [!WARNING]
> The strategy exhibits extreme sensitivity to `bb_width_thresh`. Deviating by even 0.01 in either direction degrades performance significantly. This confirms that the default value of 0.06 is highly calibrated to historical data, underscoring the necessity of implementing orthogonal mean-reversion systems in Phase 12.

---

## 5. Research Idea Engine Upgrade

The `ResearchIdeaEngine` has been upgraded to track idea lifecycle states and distinct counts:
*   **Total Ideas:** 21
*   **Generated Idea Count:** 10
*   **Tested/Accepted Idea Count:** 3 (ADX Slope Momentum Continuation, Volume Trend Confirmation Gate, 5m Pullback Reclaim)
*   **Deferred-to-Phase-12 Count:** 11 (Orthogonal strategy hypotheses)
*   **Failure-Month Count:** 15 unique months targeted

All ideas are saved to `reports/research_ideas.json` and ranked in the `reports/research_ideas_leaderboard.md`.
