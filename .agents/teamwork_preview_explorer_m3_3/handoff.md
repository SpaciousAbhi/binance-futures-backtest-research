# Phase 8: Multi-Timeframe (MTF) Alignment and Execution Strategy

This report presents a lookahead-free design for aligning 1h and 15m data with 5m candles, extending the backtesting engine and strategy template to support MTF execution, implementing tighter 5m stops, retests, and failed breakout reversals, scaling risk dynamically, and rescuing negative or zero-trade months.

---

## 1. Observation
From a comprehensive analysis of the codebase, the following architectural details and constraints were observed:

1. **Candle Timing and Structures**:
   - In `src/data/processor.py` (lines 46–59), the data processor aligns raw candles and funding rates on the open time:
     ```python
     merged = pd.merge_asof(
         candles,
         funding[["fundingTime", "fundingRate"]],
         left_on="open_time",
         right_on="fundingTime",
         direction="backward"
     )
     ```
   - In `data/processed/BTCUSDT_5m_processed.csv`, each row contains `open_time`, `close_time`, `open`, `high`, `low`, `close`, `volume`, and `fundingRate`. The `close_time` is exactly `open_time + duration - 1` millisecond (e.g. `1577836800000` open time, `1577837099999` close time for 5m).

2. **Indicators and Swing Levels**:
   - In `src/features/indicators.py` (lines 118–137), swing high/low calculations are centered at `2*window + 1` candles and shifted by `window` to prevent lookahead:
     ```python
     swing_highs = pd.Series(np.where(highs == rolling_max, highs, np.nan), index=df.index)
     running_high = swing_highs.shift(window).ffill()
     ```
   - Technical indicators (RSI, Bollinger Bands, ATR, ADX) are calculated on a single dataframe (assumed to be 1h in Phase 7).

3. **Backtest Engine Execution**:
   - In `src/backtest/engine.py` (lines 16–378), `BacktestEngine.run` executes trades bar-by-bar on closed-candle signals, filling orders at the next bar's open (`opens[exec_idx]`).
   - Line 226 checks: `signal = strategy.get_signal(df, i)`, which means signals are only queried when there is no active position.
   - In `MultiPositionBacktestEngine` (lines 567–918), position concurrency caps (max 3 positions), strategy-level cooldowns, and MTD risk limits are applied. MTD drawdown is computed lookahead-free on lines 693-695:
     ```python
     current_monthly_loss = starting_monthly_capital - capital
     current_monthly_dd = current_monthly_loss / starting_monthly_capital if starting_monthly_capital > 0 else 0.0
     ```

4. **Monthly Consistency Deficits**:
   - In `reports/phase7_full_search_completion_and_selection_audit.md` (lines 8–22), the locked Phase 6 Portfolio baseline failed the monthly consistency test, showing **37 negative months** and **8 zero-trade months** over the 78-month backtest.
   - Reversion-based low-activity fillers standalone achieved positive expectancy (+$150.38 net PnL, 1.03 PF) but did not fully rescue the zero-trade months when combined.

---

## 2. Logic Chain
The step-by-step reasoning from these observations to our design is as follows:

1. **Preventing Lookahead in MTF Alignment**:
   - To prevent lookahead, HTF candle data (1h and 15m) must only be visible to a 5m candle *after* the HTF candle has fully completed. 
   - A 1h candle opening at `00:00:00` closes at `00:59:59.999`. Its indicators and OHLC values are first known at `01:00:00`.
   - Therefore, a 5m candle starting at `01:00:00` can look backward to the 1h candle closing at `00:59:59.999`. 
   - A 5m candle starting at `00:55:00` cannot use the `00:00:00` 1h candle's closed data (which closes at `00:59:59.999` — 5 minutes in the future).
   - Performing a `pd.merge_asof` matching `df_5m['open_time']` (left) with HTF `df_htf['close_time']` (right) with `direction="backward"` guarantees that a 5m candle at time $T_{5m\_open}$ is merged with the latest HTF candle whose close time satisfies $T_{htf\_close} \le T_{5m\_open}$. Because the HTF close time ends in `999` ms and 5m open time is on the minute boundary, $T_{htf\_close}$ is always $1$ ms before the next HTF open time, making this a perfect boundary match.

2. **Avoiding HTF Lag Replication Lookahead**:
   - In a 5m dataframe, three 5m rows will map to the same 15m candle.
   - If we use `.shift(1)` on the merged 5m dataframe to find "the previous 15m candle's RSI", we would get the value of the 5m candle 5 minutes ago, which is still the same 15m candle.
   - If we shift the 5m index by 3 (to represent 15 minutes), we might introduce a lookahead or timing bug due to missing candles.
   - Thus, shifting historical lags *must* occur on the HTF dataframes **before** they are merged into the 5m dataframe. Shifting `df_15m['rsi_14']` by 1 on the 15m dataframe results in `rsi_14_lag1`, which when merged to 5m correctly represents the RSI of the 15m candle *before* the most recently completed one.

3. **Enabling 5m Precision Entries and HTF Setups**:
   - Running the backtesting engine at the 5m resolution (passing `df_aligned`) allows the loop index `i` to represent a 5m bar.
   - This allows `UniversalStrategyTemplate.get_signal` to check 1h trends (from the merged 1h columns), 15m setups (from the merged 15m columns), and trigger immediately on 5m price action (e.g. crossing 5m Bollinger Bands) with a precision of 5 minutes rather than waiting for a 15m or 1h candle to close.

4. **Dynamic Exits in Engine**:
   - Currently, `get_signal` is only called if `active_position` is `None`. This prevents strategies from modifying stops or targets once a trade is active.
   - By creating an `update_exit` method called on every active position at every 5m bar, we can support trailing stops (using 5m ATR or EMAs) and dynamic swing exits.

5. **Lookahead-Free Month Rescue**:
   - Standard monthly filters that know the month's final outcome are lookahead-leaking.
   - A lookahead-free system must use rolling features. Tracking rolling MTD drawdown and rolling inactivity lookbacks allows the system to stop trading (bad-month conversion) or lower thresholds / activate fillers (zero-month rescue) dynamically based only on past equity curve and trade counts.

---

## 3. Caveats
- **Assumption on Data Continuity**: We assume that raw data files have no missing periods. If there are large gaps, `merge_asof(direction="backward")` will carry forward stale HTF values. A maximum tolerance `tolerance` (e.g. `tolerance=pd.Timedelta('1h')` or measured in ms) must be passed to `merge_asof` to avoid merging stale data across large data gaps.
- **Warmup Periods**: Dropping rows with `NaN` values after merging will truncate the start of the backtest by at least 200 hours (due to the 1h EMA 200 warmup). This is acceptable and represents a clean initial state.
- **Funding Modulo**: The 8-hour boundary check `open_time % (8 * 3600 * 1000) == 0` assumes Binance funding rates are strictly 8-hourly. If a symbol has a 4-hour or 2-hour funding rate (as some volatile pairs do), this check must be adapted dynamically based on the symbol's exchange info.

---

## 4. Conclusion & Design Specifications

### Specification 1: Lookahead-Free MTF Data Alignment
HTF data (15m and 1h) must be aligned with 5m candles by merging on close times using `pd.merge_asof` with backward direction.

```python
# 1. Calculate indicators and lags on HTF dataframes independently
for df_htf in [df_15m, df_1h]:
    df_htf['rsi_14'] = calculate_rsi(df_htf)
    df_htf['atr_14'] = calculate_atr(df_htf)
    # Generate lag columns to avoid lookahead or replication bugs
    df_htf['rsi_14_lag1'] = df_htf['rsi_14'].shift(1)
    df_htf['swing_high_lag1'] = df_htf['swing_high'].shift(1)
    df_htf['swing_low_lag1'] = df_htf['swing_low'].shift(1)

# 2. Add timeframe suffixes to columns (excluding open_time and close_time)
df_15m = df_15m.rename(columns={col: f"{col}_15m" for col in df_15m.columns if col not in ["open_time", "close_time"]})
df_1h = df_1h.rename(columns={col: f"{col}_1h" for col in df_1h.columns if col not in ["open_time", "close_time"]})

# 3. Sort by merge keys
df_5m = df_5m.sort_values("open_time")
df_15m = df_15m.sort_values("close_time")
df_1h = df_1h.sort_values("close_time")

# 4. Perform sequential merge_asof backward on close times
# Tolerance caps stale data carry-forward to 15m/1h respectively
df_aligned = pd.merge_asof(
    df_5m,
    df_15m,
    left_on="open_time",
    right_on="close_time",
    direction="backward",
    tolerance=15 * 60 * 1000  # 15 minutes max gap
)

df_aligned = pd.merge_asof(
    df_aligned,
    df_1h,
    left_on="open_time",
    right_on="close_time",
    direction="backward",
    tolerance=60 * 60 * 1000  # 1 hour max gap
)

df_aligned = df_aligned.dropna().reset_index(drop=True)
```

### Specification 2: Strategy and Engine Support for MTF
- **Engine Resolution**: The `BacktestEngine.run` loop is executed on the 5m aligned dataframe `df_aligned`.
- **Strategy Signal Evaluation**: `UniversalStrategyTemplate.get_signal` acts as the coordinator across the 3 timeframe tiers:
  ```python
  def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
      # Tier 1: 1h Regime Filter (Long-term trend/volatility filter)
      is_bull_trend_1h = df.loc[i, "regime_bull_trend_1h"]
      is_chop_1h = df.loc[i, "regime_toxic_chop_1h"]
      if is_chop_1h:
          return None
      
      # Tier 2: 15m Setup (Medium-term structure/pullback check)
      rsi_15m = df.loc[i, "rsi_14_15m"]
      pullback_15m = rsi_15m <= 40
      
      # Tier 3: 5m Precision Entry (Short-term execution trigger)
      close_5m = df.loc[i, "close"]
      bb_upper_5m = df.loc[i, "bb_upper"]
      trigger_long = close_5m > bb_upper_5m
      
      if is_bull_trend_1h and pullback_15m and trigger_long:
          # Compute stops and targets on 5m ATR for tightness
          atr_5m = df.loc[i, "atr_14"]
          return {
              "side": "Long",
              "stop_loss": close_5m - (1.5 * atr_5m),
              "take_profit": close_5m + (3.0 * atr_5m),
              "reason": "MTF Bull Trend Breakout"
          }
      return None
  ```

### Specification 3: Execution Rules and 5m Precision Controls
1. **Delayed Confirmation**:
   - Do not enter on the immediate breakout candle. Store the breakout index.
   - Enter only if $K$ consecutive 5m candles close above the breakout level:
     `all(df['close'].iloc[i-k] > L for k in range(K))` where $L$ is the breakout level.
2. **Breakout Retest**:
   - Identify breakout of 15m Swing High (`df['swing_high_lag1_15m']`).
   - Retest occurs when a 5m candle low touches the breakout level: `df['low'].iloc[i] <= L + 0.1 * atr_5m` and `df['low'].iloc[i] >= L - 0.1 * atr_5m`.
   - Entry is confirmed when a subsequent 5m candle closes back above $L$ with a bullish wick rejection: `df['close'].iloc[i] > L` and `df['lower_wick_ratio'].iloc[i] >= 0.40`.
3. **Failed Breakout Reversal**:
   - Short Entry: Price sweeps above 15m Swing High but closes back below it: `df['high'].iloc[i] > df['swing_high_lag1_15m']` and `df['close'].iloc[i] < df['swing_high_lag1_15m']` with `df['upper_wick_ratio'].iloc[i] >= 0.50`.
   - Place a tight Stop Loss at `df['high'].iloc[i] + 0.1 * atr_5m` (the sweep high).
4. **Tighter 5m Stops**:
   - Place Stop Loss at the rolling 3-candle minimum low minus a buffer:
     `stop_loss = df['low'].iloc[i-2:i+1].min() - 0.1 * atr_5m`.

### Specification 4: Dynamic Exits and Risk Scaling
- **Engine Extension**: Modify the position-handling loop in `BacktestEngine.run` to call an active position update method on each bar:
  ```python
  if active_position is not None:
      # Query active strategy for exit updates
      exit_update = strategy.update_exit(df, i, active_position)
      if exit_update:
          if exit_update.get("exit_now", False):
              # Execute immediate market exit
              exit_price = opens[i]
              # ... process trade record and close position ...
          else:
              # Dynamic stop trailing or target adjustment
              active_position["stop_loss"] = exit_update["stop_loss"]
              active_position["take_profit"] = exit_update["take_profit"]
  ```
- **Trailing Stop**:
  ```python
  def update_exit(self, df: pd.DataFrame, i: int, position: dict) -> dict:
      atr = df.loc[i, "atr_14"]
      close = df.loc[i, "close"]
      if position["side"] == "Long":
          # Trail SL at 2.0 * ATR below close (only move SL up)
          new_sl = max(position["stop_loss"], close - 2.0 * atr)
          return {"stop_loss": new_sl, "take_profit": position["take_profit"], "exit_now": False}
      else:
          new_sl = min(position["stop_loss"], close + 2.0 * atr)
          return {"stop_loss": new_sl, "take_profit": position["take_profit"], "exit_now": False}
  ```
- **Loss-Streak Risk Scaling**:
  Scale the account risk percentage ($R$) dynamically based on consecutive losses:
  $$R = \text{base\_risk} \times 0.5^{\max(0, \text{consecutive\_losses} - 2)}$$
  - 0–2 losses: 1.0% risk.
  - 3 losses: 0.5% risk.
  - 4 losses: 0.25% risk.
  - 5+ losses: 0.0% risk (deactivate trading).
  - Reactivate strategy only after a paper trade wins in the background.

### Specification 5: Lookahead-Free Monthly Conversion and Rescue
1. **Bad-Month Conversion (MTD Drawdown Throttles)**:
   - On the first bar of each calendar month, store `starting_monthly_capital = capital`.
   - Calculate MTD Drawdown on every bar: `mtd_dd = (starting_monthly_capital - capital) / starting_monthly_capital`.
   - Apply strict risk limits dynamically:
     - If `mtd_dd >= 1.5%`: Reduce strategy risk by 50%.
     - If `mtd_dd >= 2.5%`: Reduce strategy risk by 75%.
     - If `mtd_dd >= 3.0%`: Trigger **Emergency Monthly Pause** (reduce risk to 0%, halting all new entries for the rest of the month).
   - This caps the monthly loss at a maximum of ~3% and prevents negative months from degrading the equity curve.

2. **Zero-Month Rescue (Activity-Based Fillers)**:
   - Track inactivity length: `bars_since_last_trade` represents the number of 5m bars since the last trade was executed.
   - If `bars_since_last_trade >= 864` (3 calendar days on 5m) or if calendar day of month $\ge 10$ and `monthly_trade_count == 0`:
     - **Filler Activation**: Enable the **Low Activity Reversion Filler** (Trend Reclaim Bollinger Reversion strategy) to take high-probability mean-reversion trades.
     - **Threshold Relaxation**: Decrease entry trigger bounds of the primary strategy. For example:
       - Decrease Bollinger Band width compression threshold `bb_width_thresh` from `0.035` to `0.045` (permits breakouts in slightly wider ranges).
       - Decrease ADX threshold `adx_thresh` from `20` to `15` (permits breakouts in weaker trends).

---

## 5. Verification Method

To independently verify this design and confirm it is lookahead-free and correct:
1. **No-Lookahead Test Case**:
   - Write a unit test that verifies the index alignment:
     ```python
     def test_mtf_alignment_lookahead_free():
         # Create synthetic 5m, 15m, and 1h data
         # Assert that for a 5m bar at 01:00:00, the 1h candle merged has an open_time of 00:00:00.
         # Assert that the close price of the 1h candle at 00:00:00 is NOT visible to any 5m candle prior to 01:00:00.
     ```
2. **Run System Auditor Check**:
   - The compliance script `src/audit/system_auditor.py` must be updated to audit the 5m merged dataset:
     - Verify that signals generated at 5m index `i` only use elements of `df_aligned` up to index `i`.
     - Confirm that `df_aligned.iloc[i]` has no fields containing future timestamps.
3. **Monthly Metrics Check**:
   - Inspect the monthly report dictionary output: `results['metrics']['monthly_report']`.
   - Verify that there are no negative months (net PnL < 0) and no zero-trade months (trades == 0) across the 78-month backtest.
   - Verify that the total trade count is $\ge 780$.
