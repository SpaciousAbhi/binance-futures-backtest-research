# Handoff Report: Phase 8 Multi-Timeframe (MTF) Alignment and Execution Strategy Design

This report outlines the read-only investigation, analysis, and comprehensive design for Phase 8, focusing on lookahead-free Multi-Timeframe (MTF) data alignment, execution triggers, delayed confirmation rules, risk scaling, and monthly consistency recovery modules.

---

## 1. Observation
We observed the following key aspects of the codebase:
* **Current Backtesting Framework (`src/backtest/engine.py`)**:
  * Line 48: "Pre-extract numpy arrays for instant lookups (100x speedup!)" shows that the engine relies on pre-extracted column arrays (e.g. `open_times = df["open_time"].values`, `opens = df["open"].values`) for speed.
  * Lines 225-255: The entry trigger is generated at candle `i` (using the closed candle's data) and filled at the next candle `i + 1 + delay_candles` using `opens[exec_idx]`.
  * Lines 828-833: In the `MultiPositionBacktestEngine`, a dictionary of `live_metrics` is passed to the strategy:
    ```python
    live_metrics = {
        "monthly_trade_count": current_month_trade_count,
        "monthly_dd": current_monthly_dd,
        "consecutive_losses": consecutive_losses_tracker.get(strat_name, 0),
        "capital": capital
    }
    ```
* **Current Single Timeframe Data Processor (`src/data/processor.py`)**:
  * Lines 48-54: Candles and funding rates are merged lookahead-free using:
    ```python
    merged = pd.merge_asof(
        candles,
        funding[["fundingTime", "fundingRate"]],
        left_on="open_time",
        right_on="fundingTime",
        direction="backward"
    )
    ```
* **Current Strategy Template (`src/strategies/candidates.py`)**:
  * Lines 433-435: `UniversalStrategyTemplate` extracts `days_of_month` and `hours` directly from the input dataframe to evaluate session and timing filters.
  * Lines 714-731: The `low_activity_filler` uses `live_metrics` to trigger trades if `day_of_month >= 10 and monthly_trades == 0` or `day_of_month >= 15 and monthly_trades < 6`.
* **Baseline and Targets (`WALKTHROUGH.md` and `src/research/runner.py`)**:
  * Lines 251-253 in `src/research/runner.py` show that the locked Phase 6 Baseline Portfolio (Baseline A) achieves **+$6,577.32 Net PnL** across **731 trades**, but suffers from **37 negative months** and **8 zero-trade months** over the 5.5-year history.
  * Achieving 100% positive months is the primary target for a PASS verdict, requiring strategies to protect capital in bad months and ensure activity in dry months.

---

## 2. Logic Chain
1. **Multi-Timeframe Lookahead Bias**:
   * Merging 1h and 15m candle data with 5m candles based on *open times* directly would cause future leak. For example, matching 1h data starting at 10:00:00 with the 5m candle starting at 10:00:00 is leaking the 1h candle's high, low, close, and indicators (which only close at 11:00:00) into the 10:00:00 5m candle.
   * To prevent this, we must align based on the **close times** of the higher timeframe (HTF) and the **open time** (or **close time**) of the 5m candle.
   * If we match the 5m candle's `open_time` (left key) with the HTF candle's `close_time` (right key) with `direction="backward"`, the 5m candle starting at 10:00:00 will match the 1h candle closing at 09:59:59.999. This is 100% lookahead-free but results in a 1-hour lag on the 1h indicators (since the 1h candle closing at 10:00:00 cannot be used).
   * If we instead match the 5m candle's `close_time` (left key) with the HTF candle's `close_time` (right key) with `direction="backward"`, the 5m candle starting at 09:55:00 and closing at 10:00:00 (which represents the decision-making bar `i`) will match the 1h candle closing at 09:59:59.999. Since the decision is evaluated at 10:00:00, this allows using the 1h candle that closed at 10:00:00 without lookahead bias, eliminating the 1-hour lag.
2. **Strategy Trigger Hierarchy**:
   * The `UniversalStrategyTemplate` currently queries signals based on a single timeframe. To support MTF, it must implement a setup-to-trigger state machine. The 1h data filters the overall trend direction (Regime), the 15m data identifies setup patterns (Setups), and the 5m data triggers the actual entry (Precision Entries) with tighter stops.
3. **Delayed Confirmation, Retests, and Stops**:
   * Standard breakouts have a high failure rate in choppy regimes, causing negative months. By requiring 5m close confirmation or a breakout retest bounce, we filter out false breakouts.
   * Setting stops on the 5m structure (e.g., local 5m swing high/low) rather than the 15m ATR reduces the stop distance. This allows larger contract sizes for the same risk amount, boosting the R-multiple on winners.
4. **Dynamic Exits and Risk Scaling**:
   * A fixed ATR stop/take-profit doesn't adapt to changing market conditions. Modifying TP based on the 1h ADX and trailing stops locks in profits.
   * Reducing risk scaling factor $S$ based on consecutive losses or Month-to-Date (MTD) drawdowns prevents large drawdowns from rolling over into subsequent trades during bad months.
5. **Recovery Modules**:
   * Bad-month conversion requires dynamically shifting the active modules from breakout (aggressive) to mean-reversion (defensive) when the cumulative MTD drawdown exceeds a threshold.
   * Zero-month rescue requires dynamically activating and relaxing the filters of the `low_activity_filler` based on the day of the month and trade count. Both are lookahead-free because they rely entirely on cumulative MTD statistics.

---

## 3. Caveats
* **Data Alignment Precision**: We assume that raw data files contain accurate, uncorrupted `close_time` values (e.g. `open_time + period - 1ms`). If `close_time` is missing or improperly calculated in raw CSVs, it must be generated syntactically during processing.
* **Execution Delays**: If the backtest engine uses `delay_candles > 0` (e.g., 1 bar delay), the 5m precision entry will be filled at the open of the candle *after* the trigger is confirmed. The strategy must account for this delay when setting stop-loss and take-profit levels.
* **Slippage and Fees**: Tighter 5m stops increase position sizing, which in turn increases the absolute impact of fees and slippage on net returns. We assume the scoring filter will continue to penalize high cost-erosion configurations.

---

## 4. Conclusion & Design Specification

### A. Lookahead-Free MTF Data Alignment
We propose creating an `MTFDataProcessor` that processes 1h, 15m, and 5m candle datasets separately, calculates technical indicators on each timeframe, and then aligns them into a single unified 5m DataFrame.

#### Exact Pandas Merge Keys & Directions:
1. **Pre-processing keys**:
   * Ensure each DataFrame ($DF_{5m}$, $DF_{15m}$, $DF_{1h}$) is sorted by `open_time` and has a `close_time` column.
   * If `close_time` is not present, calculate it:
     * $DF_{15m}[\text{"close\_time"}] = DF_{15m}[\text{"open\_time"}] + (15 \times 60 \times 1000) - 1$
     * $DF_{1h}[\text{"close\_time"}] = DF_{1h}[\text{"open\_time"}] + (60 \times 60 \times 1000) - 1$
2. **Column Renaming**:
   * To prevent naming collisions, prefix all indicator/OHLCV columns of the HTF DataFrames (except the merge keys):
     * $DF_{15m}$ columns renamed to `m15_[column]`
     * $DF_{1h}$ columns renamed to `h1_[column]`
3. **Alignment Operation**:
   * We merge the DataFrames on **close times** to align the end of the 5m candle (decision point) with the end of the HTF candles:
     * **Step 1 (Merge 15m)**: Match $DF_{5m}$'s `close_time` (left key) with $DF_{15m}$'s `close_time` (right key) using `direction="backward"`.
     * **Step 2 (Merge 1h)**: Match the resulting DataFrame's `close_time` (left key) with $DF_{1h}$'s `close_time` (right key) using `direction="backward"`.
4. **Pandas Implementation**:
   ```python
   # Prepare join keys
   df_15m["join_key_15m"] = df_15m["close_time"]
   df_1h["join_key_1h"] = df_1h["close_time"]
   
   # Prefix columns
   df_15m_renamed = df_15m.rename(columns=lambda x: f"m15_{x}" if x not in ["join_key_15m"] else x)
   df_1h_renamed = df_1h.rename(columns=lambda x: f"h1_{x}" if x not in ["join_key_1h"] else x)
   
   # Merge 15m into 5m
   df_aligned = pd.merge_asof(
       df_5m.sort_values("close_time"),
       df_15m_renamed.sort_values("join_key_15m"),
       left_on="close_time",
       right_on="join_key_15m",
       direction="backward"
   )
   
   # Merge 1h into result
   df_aligned = pd.merge_asof(
       df_aligned,
       df_1h_renamed.sort_values("join_key_1h"),
       left_on="close_time",
       right_on="join_key_1h",
       direction="backward"
   )
   
   # Drop temporary keys
   df_aligned = df_aligned.drop(columns=["join_key_15m", "join_key_1h"])
   ```

### B. Strategy Template & Engine Extensions
To implement the MTF setup-to-trigger state machine, the `UniversalStrategyTemplate` should be modified to track setup states across consecutive bars:

1. **State variables in `__init__`**:
   * `self.setup_state = None` # None, "PENDING_LONG", "PENDING_SHORT"
   * `self.setup_bar_idx = -1`
   * `self.setup_price_level = 0.0`
   * `self.retest_state = None` # None, "AWAITING_RETEST", "RETESTED"
2. **Setup Expiry Constraint**:
   * A setup is only valid for a maximum of 3 5m bars (15 minutes). If no trigger occurs within this window, the setup is reset.
3. **Execution Logic Flow in `get_signal`**:
   ```python
   # Step 1: Clean up expired setups
   if self.setup_state is not None and (i - self.setup_bar_idx) > 3:
       self._reset_setup_state()
   
   # Access cached array values at index i
   h1_bull = self._h1_regime_bull_trend[i]
   h1_bear = self._h1_regime_bear_trend[i]
   m15_rsi = self._m15_rsi_14[i]
   
   close_5m = self._close[i]
   low_5m = self._low[i]
   high_5m = self._high[i]
   atr_5m = self._atr_14[i]
   
   # Step 2: Look for 1h/15m setups if no active setup
   if self.setup_state is None:
       # Example: 1h Trend Bullish, 15m RSI Pullback
       if h1_bull and m15_rsi <= 40:
           self.setup_state = "PENDING_LONG"
           self.setup_bar_idx = i
           self.setup_price_level = self._m15_bb_lower[i] # level to watch
           
       elif h1_bear and m15_rsi >= 60:
           self.setup_state = "PENDING_SHORT"
           self.setup_bar_idx = i
           self.setup_price_level = self._m15_bb_upper[i]
           
   # Step 3: Evaluate 5m Entry Triggers on active setup
   if self.setup_state == "PENDING_LONG":
       # Example Trigger: 5m candle closes above 5m EMA 9
       if close_5m > self._ema_9_5m[i]:
           sl = min(self._low[i-2:i+1]) - (0.1 * atr_5m) # Tighter 5m stop
           tp = close_5m + (3.0 * self._m15_atr_14[i])   # Dynamic TP on 15m ATR
           self._reset_setup_state()
           return {"side": "Long", "stop_loss": sl, "take_profit": tp, "reason": "MTF Pullback Confirmed"}
           
   elif self.setup_state == "PENDING_SHORT":
       if close_5m < self._ema_9_5m[i]:
           sl = max(self._high[i-2:i+1]) + (0.1 * atr_5m)
           tp = close_5m - (3.0 * self._m15_atr_14[i])
           self._reset_setup_state()
           return {"side": "Short", "stop_loss": sl, "take_profit": tp, "reason": "MTF Pullback Confirmed"}
   
   return None
   ```
4. **Engine Extensions**:
   * Update the runner or backtester to call `strategy.reset()` at the beginning of each run to prevent state variables from bleeding between consecutive backtests.

### C. Advanced Execution Rules
1. **Delayed Confirmation Rules**:
   * For breakouts (e.g. 15m Bollinger Band breakouts), do not enter immediately.
   * Require that after a 15m breakout setup occurs, the 5m candle must close above the breakout level for $N=2$ consecutive bars. If `close_5m < breakout_level` during these 2 bars, the breakout is flagged as unconfirmed and the setup is discarded.
2. **Breakout Retests**:
   * *Setup*: 15m close breaks above 15m Swing High. Record `self.setup_price_level = swing_high` and set `self.retest_state = "AWAITING_RETEST"`.
   * *Retest Condition*: Wait for a 5m candle where `low_5m <= self.setup_price_level` and `close_5m >= self.setup_price_level` (price touches the level but holds it as support). Move to `"RETESTED"`.
   * *Entry Trigger*: The next 5m candle closes green (close > open) or crosses above the 5m EMA 9.
   * *Stop Loss*: Placed just below the low of the retest candle: `stop_loss = retest_candle_low - 0.1 * atr_5m`.
3. **Failed Breakout Reversals (FBR)**:
   * *Setup*: Price breaks above a 15m swing high, but immediately fails.
   * *Rejection Condition*: A 5m candle high exceeds the 15m swing high, but the candle closes back below the swing high. The candle must exhibit a large upper wick (`upper_wick_ratio >= 0.45`).
   * *Entry Trigger*: Enter Short at the open of the next 5m candle.
   * *Tighter Stop*: `stop_loss = failed_breakout_candle_high + 0.1 * atr_5m`. This creates an extremely small stop distance, allowing higher position sizing and generating high R-multiplier rewards.

### D. Dynamic Exits and Risk Scaling
1. **Dynamic Exits (Swing & ATR)**:
   * **ATR-based TP adjustment**: Adjust take profit distance using 1h trend strength:
     * If `h1_adx > 25` (strong trend): target $3.5 \times \text{ATR}_{15m}$.
     * If `h1_adx <= 25` (sideways/range): target the opposite 15m Bollinger Band or $1.5 \times \text{ATR}_{15m}$.
   * **Breakeven Trailing**: Once a trade reaches $+1.5R$ profit, automatically move the stop-loss to the entry price (breakeven).
   * **Indicator-based Trailing**: Trail the stop loss behind the 15m VWAP (for longs) or the 15m VWAP upper band (for shorts) after price reaches $+2R$.
2. **Risk Scaling & Loss-Streak Throttles**:
   * Keep a count of consecutive losses at the strategy level.
   * Adjust the sizing risk percentage dynamically:
     * $\le 2$ consecutive losses: Risk 1.0% of capital.
     * $3 \text{ to } 4$ consecutive losses: Risk 0.5% of capital (50% reduction).
     * $\ge 5$ consecutive losses: Risk 0.25% of capital (75% reduction).
     * $\ge 7$ consecutive losses: Temporary trading halt for the strategy (2 days / 576 5m bars).
   * Reset risk scaling back to 1.0% only after a trade achieves a net gain of $\ge 1.0R$.

### E. Bad-Month Conversion & Zero-Month Rescue Modules
Both modules operate inside the strategy using `live_metrics` passed bar-by-bar, ensuring 100% lookahead-free operation.

```
                  +-----------------------------------------+
                  |  MTF Strategy get_signal(df, i, metrics)|
                  +-----------------------------------------+
                                       |
                   [Lookahead-Free Regime / MTD Audits]
                                       |
                  +--------------------+--------------------+
                  |                                         |
        [MTD Drawdown Audit]                       [MTD Activity Audit]
                  |                                         |
     Is MTD Drawdown > 1.5%?                    Is Day >= 10 & Trades == 0?
                  |                                         |
          +-------+-------+                         +-------+-------+
          |               |                         |               |
         YES              NO                       YES              NO
          |               |                         |               |
   [Bad-Month Module]  [Normal]            [Zero-Month Rescue]  [Normal]
          |               |                         |               |
   * Shift to MR    * Standard               * Activate Reclaim   * Normal
   * Scale Risk       Breakout/Trend           Filler Module        Filters
     to 0.5%          Risk (1%)              * Relax Thresholds
```

1. **Bad-Month Conversion Module**:
   * At bar $i$, inspect `live_metrics["monthly_dd"]`.
   * **Stage 1 (Soft Conversion)**: If `monthly_dd > 0.015` (1.5%):
     * *Regime Shift*: Deactivate aggressive breakout strategies. Allow only mean-reversion strategies (`bollinger_mean_reversion`, `vwap_mean_reversion`) and liquidity sweeps.
     * *Risk Scaling*: Cap trade risk at 0.5%.
   * **Stage 2 (Hard Conversion)**: If `monthly_dd > 0.025` (2.5%):
     * *Deactivation*: Disable all trend-following and breakout modules. Allow only highly selective Liquidity Sweep Reversals with tight stops and a high win rate.
     * *Risk Scaling*: Cap trade risk at 0.25%.
   * **Stage 3 (Circuit Breaker)**: If `monthly_dd > 0.03` (3.0%):
     * *Halt*: Disable all entry signals for the strategy for the remainder of the calendar month.
2. **Zero-Month Rescue Module**:
   * At bar $i$, inspect the current day of the month `self._days_of_month[i]` and `live_metrics["monthly_trade_count"]`.
   * **Milestone 1 (Day 10)**: If `day_of_month >= 10` and `monthly_trade_count == 0`:
     * *Action*: Activate the `low_activity_filler` module ( Bollinger Reclaim Reversion).
   * **Milestone 2 (Day 15)**: If `day_of_month >= 15` and `monthly_trade_count < 3`:
     * *Action*: Relax the Bollinger Reclaim filters (reduce the required BB width threshold from 0.035 to 0.05, and relax the RSI overbought/oversold boundaries from 75/25 to 65/35).
   * **Milestone 3 (Day 20)**: If `day_of_month >= 20` and `monthly_trade_count < 5`:
     * *Action*: Further relax filters and increase position sizing for the filler module to ensure activity targets are achieved.

---

## 5. Verification Method

To verify this MTF alignment and execution strategy design:
1. **Historical Alignment Verification**:
   * Run a pandas alignment test script that prints the first 5 rows of `df_aligned` at the start of any hour boundary (e.g. 10:00:00).
   * Confirm that `df_aligned.loc[10:00:00, "h1_close_time"]` is equal to `09:59:59.999`.
   * Assert that `df_aligned.loc[10:00:00, "h1_close"]` matches `df_1h.loc[09:59:59.999, "close"]`, verifying no future leakage.
2. **Lookahead Audit Execution**:
   * Run the project's lookahead audit in `src/audit/system_auditor.py` (which truncates the dataset at index $i$ and compares signals to the full-dataset run).
   * Command: `pytest tests/test_backtest.py` and `pytest tests/test_phase6_verification.py`. All tests must pass, confirming that MTF indicator calculation and alignment do not introduce future leakage.
3. **Monthly Consistency Check**:
   * Execute the research runner (`python src/research/runner.py`) using the new MTF portfolio strategy.
   * Check the monthly report in the generated Markdown. Verify that:
     * The number of negative months is reduced from 37 towards 0 (using the Bad-Month Conversion module).
     * The number of zero-trade months is reduced from 8 to 0 (using the Zero-Month Rescue module).
     * The total trade count is maintained above 780.
