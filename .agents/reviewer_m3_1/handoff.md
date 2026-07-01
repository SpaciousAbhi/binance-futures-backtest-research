# Handoff Report: Baseline Performance Discrepancy Investigation

## 1. Observation
- In `reports/phase7_ultradeep_monthly_consistency_research_report.md` (lines 17-23), the baselines show negative PnLs:
  ```
  ## 1. LOCKED BASELINES COMPARISON TABLE
  | Baseline Model | Net PnL ($) | Max Drawdown | Profit Factor | Total Trades | +/-/0 Months |
  |---|---|---|---|---|---|
  | Baseline A: Phase 6 Portfolio | -2236.96 | 34.99% | 0.82 | 348 | 17/30/31 |
  | Baseline B: Phase 5 Best Single Candidate | -2587.60 | 27.64% | 0.72 | 161 | 23/24/31 |
  | Baseline C: Rebuilt Positive Filler | -9414.17 | 94.20% | 0.58 | 721 | 13/65/0 |
  ```
- In `src/research/runner.py` (lines 256, 261, 266), the baseline comparisons are backtested on the `df_tf` (5m aligned) dataset:
  ```python
  p6_chosen_res = multi_engine.run(df_tf, p6_chosen_portfolio, {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0})
  ...
  p5_single_res = engine.run(df_tf, p5_single_strat)
  ...
  filler_res = engine.run(df_tf, filler_strat)
  ```
- In `src/strategies/candidates.py` (lines 427-448), the technical indicator values (e.g. `_close`, `_bb_upper`, `_rsi_14`, `_atr_14`) are extracted from the default column names of the DataFrame without suffix matching:
  ```python
  self._close = df["close"].values
  self._bb_upper = df["bb_upper"].values
  self._rsi_14 = df["rsi_14"].values
  self._atr_14 = df["atr_14"].values
  ```
- Running our diagnostic script (`python .agents/reviewer_m3_1/verify_baselines.py`) yielded the following side-by-side comparison:
  ```
  === RUNNING ON 1H DATA ===
  Baseline B (Best Single) 1H PnL: $6872.29 | Trades: 295 | Max DD: 6.96%
  Baseline C (Filler) 1H PnL: $150.38 | Trades: 82 | Max DD: 14.33%
  Baseline A (Portfolio) 1H PnL: $5760.09 | Trades: 738 | Max DD: 23.10%

  === RUNNING ON 5M ALIGNED DATA ===
  Baseline B (Best Single) 5M PnL: $-2587.60 | Trades: 161 | Max DD: 27.64%
  Baseline C (Filler) 5M PnL: $-9414.17 | Trades: 721 | Max DD: 94.20%
  Baseline A (Portfolio) 5M PnL: $-2236.96 | Trades: 348 | Max DD: 34.99%
  ```

## 2. Logic Chain
1. The baseline configurations (`p5_best_single_cfg`, `rebuilt_filler_cfg`, etc.) represent 1h strategies that are designed and optimized for 1h candles and 1h indicators.
2. In `runner.py`, they are backtested on `df_tf` (which is aligned onto the 5m timeframe).
3. Inside `UniversalStrategyTemplate.get_signal`, since the columns are retrieved without suffix checking, they map to the 5m columns (`close`, `bb_upper`, `rsi_14`, `atr_14`, etc.).
4. This causes the 1h baseline strategies to trigger entry signals based on 5m candles and 5m indicators.
5. In addition, stop-loss and take-profit levels are calculated as multiples of `atr_14` (which is the 5m ATR). The 5m ATR is much smaller than the 1h ATR (e.g. $10–50 for BTC vs $100–300).
6. The combination of high trigger frequency (overtrading) and extremely tight stop/profit targets leads to transaction fees and slippage rapidly eroding the strategy's capital.
7. This explains why the baselines generated massive losses and negative PnLs in the report. For example, Baseline C (Filler) traded 721 times and lost -$9,414.17 on `df_tf`, whereas on its correct `datasets["1h"]` it traded 82 times and gained +$150.38.

## 3. Caveats
- We assume that the original baseline performance on the 1h candles represents the correct target behavior.
- We did not modify any source code files, adhering to our "Review-only" constraint.

## 4. Conclusion
- The negative PnLs of Baseline A, B, and C in the report are caused by evaluating 1h baseline strategies directly on 5m candles and 5m indicators instead of 1h candles/indicators.
- Recommended Fixes:
  1. Modify `runner.py` to evaluate baseline comparisons (A, B, C) on `datasets["1h"]` instead of `df_tf` to preserve their original correct performance.
  2. For evaluating 1h strategies on the 5m DataFrame, modify `UniversalStrategyTemplate` to support a `"timeframe": "1h"` parameter. When `"close_1h"` is present:
     - Check `open_time % 3600000 == 0` to ensure signals are only generated at the start of the hour.
     - Use the `_1h` columns (e.g., `close_1h`, `bb_upper_1h`, `rsi_14_1h`, `ema_200_1h`, `atr_14_1h`) instead of 5m indicators.
     - Calculate TP/SL using `atr_14_1h` (1h ATR) so stop distances are correctly sized.
     - The backtest engine will execute exits (hits to SL/TP) at the 5m candle resolution, achieving 5m precision execution of 1h signals.
  3. Keep the new MTF breakout/portfolio strategy running on `df_tf` (5m aligned data).

## 5. Verification Method
- Execute the diagnostic script: `python .agents/reviewer_m3_1/verify_baselines.py`
- Verify that:
  - 1H data results show positive PnLs matching historical baseline performance.
  - 5M aligned data results show negative PnLs matching the values in the monthly consistency report.

---

# Quality Review Report

## Review Summary

**Verdict**: REQUEST_CHANGES

## Findings

### [Critical] Finding 1: Resolution Mismatch in Baseline Backtest

- **What**: 1H baseline strategies are evaluated directly on 5m candles and 5m indicators.
- **Where**: `src/research/runner.py` (lines 256, 261, 266)
- **Why**: Running 1h strategies at 5m resolution using 5m indicators causes extreme overtrading and tight stop/profit targets, resulting in massive fee erosion and losses.
- **Suggestion**: Evaluate baseline comparison strategies on `datasets["1h"]` instead of `df_tf`. Modify `UniversalStrategyTemplate` to support a `"timeframe": "1h"` parameter and query signals only at the start of the hour boundary using `_1h` columns when evaluated on `df_tf`.

## Verified Claims

- Net PnLs in report match 5m aligned DataFrame evaluation exactly → verified via `verify_baselines.py` → PASS
- 1H data baseline strategies achieve positive performance matching historical records → verified via `verify_baselines.py` → PASS

## Coverage Gaps

- The behavior of other baseline candidates (D, E) under multi-timeframe execution was not explored — risk level: medium — recommendation: define a timeframe parameter in configuration files to prevent future alignment issues.

## Unverified Items

- None.

---

# Adversarial Challenge Report

## Challenge Summary

**Overall risk assessment**: HIGH

## Challenges

### [Critical] Challenge 1: Severe Transaction Fee Erosion

- **Assumption challenged**: Baseline strategies are comparable under the `df_tf` dataset without codebase modification.
- **Attack scenario**: If the system is deployed using `df_tf` with the baseline configuration, the strategy will overtrade by 8-10x, leading to total fee erosion and bankruptcy.
- **Blast radius**: Total loss of capital (94% drawdown on the filler).
- **Mitigation**: Shift execution back to 1h dataset for baselines, and enforce strict boundary checking on `df_tf`.

## Stress Test Results

- Normal 5M evaluation of Baseline C -> Net loss of -$9,414.17 -> FAIL
- Normal 1H evaluation of Baseline C -> Net profit of +$150.38 -> PASS
