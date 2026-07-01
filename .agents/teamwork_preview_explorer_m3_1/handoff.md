# Phase 8 Multi-Timeframe (MTF) Alignment and Execution Strategy Report

## 1. Observation
We observed the following files and structural patterns in the codebase:
- **Data Processor**: In `src/data/processor.py` (lines 48-54), the current alignment of candles and funding rates uses `pd.merge_asof` on the opening timestamps with a backward direction:
  ```python
  merged = pd.merge_asof(
      candles,
      funding[["fundingTime", "fundingRate"]],
      left_on="open_time",
      right_on="fundingTime",
      direction="backward"
  )
  ```
- **Universal Strategy Template**: In `src/strategies/candidates.py` (lines 388-773), `UniversalStrategyTemplate` defines 21 raw trading modules that evaluate signals bar-by-bar at index `i` (representing the closed candle). The strategy method `get_signal` signature is:
  ```python
  def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
  ```
  And lines 427-460 cache column arrays using the DataFrame's Python ID (`id(df)`) to bypass slow pandas series lookups inside the barloop.
- **Backtesting Engine**: In `src/backtest/engine.py` (lines 581-918), `MultiPositionBacktestEngine` runs a bar-by-bar loop over the input DataFrame `df` and queries `strategy.get_signal(df, i, live_metrics=live_metrics)` (lines 835-840). Positions are filled at `i + 1 + delay_candles` (usually next open) and are evaluated for exits bar-by-bar.
- **Low-Activity Filler**: In `src/strategies/candidates.py` (lines 714-732), the `low_activity_filler` module implements a late-month rescue system that activates based on `live_metrics`:
  ```python
  monthly_trades = live_metrics.get("monthly_trade_count", 0) if live_metrics else 0
  day_of_month = self._days_of_month[i]
  if (day_of_month >= 10 and monthly_trades == 0) or (day_of_month >= 15 and monthly_trades < 6):
  ```
- **Verification Tests**: In `tests/test_phase7_verification.py` (lines 111-144), `test_filler_rescue_no_lookahead` verifies lookahead-free compliance by comparing signal outputs on a truncated dataframe vs. a dataframe appended with extreme future values.

---

## 2. Logic Chain
To design the lookahead-free MTF alignment and execution strategy for Phase 8, we step-by-step trace from observations to our designs:

1. **Lookahead-Free Alignment (derived from `processor.py`)**:
   - Merging higher timeframes (1h, 15m) onto a lower timeframe (5m) using `open_time` would cause lookahead bias. For example, at 12:05:00, the 5m candle has closed. A backward merge on `open_time` would associate this 5m candle (open 12:00:00) with the 15m candle (open 12:00:00). However, the 15m candle contains price movements up to 12:15:00, which are unknown at 12:05:00.
   - To resolve this, we must define the exact moment of candle completion: `close_time = open_time + duration_ms`.
   - By sorting all dataframes by `close_time` ascending and using `pd.merge_asof` with `direction="backward"`, the 12:00-12:05 candle (closes at 12:05) will match the 15m candle closing at or before 12:05 (which is the 11:45-12:00 candle, closing at 12:00). At 12:15, the 12:10-12:15 candle will match the 12:00-12:15 candle (closing at 12:15). This aligns the HTF data exactly at the moment it closes, eliminating future leaks.

2. **MTF Setup and Trigger Structure (derived from `candidates.py` and `engine.py`)**:
   - The backtesting engine in `engine.py` operates on a bar-by-bar loop over the primary input DataFrame. If the primary DataFrame is the 5m timeframe, the engine naturally runs at 5m resolution.
   - We can modify `UniversalStrategyTemplate` to read indicators calculated on the 1h and 15m dataframes (prior to merging) and merged as columns.
   - We structure the strategy rules hierarchically:
     1. **1h Regime Filter**: E.g., `close_1h > ema_200_1h` (major trend) or `regime_toxic_chop_1h == False`.
     2. **15m Tactical Setup**: E.g., `close_15m` breaking out of `bb_upper_15m` (primes the setup).
     3. **5m Precision Entry**: E.g., a 5m bullish pin bar or a 5m close reclaiming a support level.
   - This provides 5m precision entries and exits, while maintaining alignment with 1h trend regimes and 15m structures.

3. **Micro-Execution and Tighter Stops**:
   - **Delayed Confirmation**: After a 15m breakout setup is primed, we check the primary 5m bars to ensure that the price stays above the breakout level for $N$ consecutive 5m candles before entering.
   - **Breakout Retests**: We monitor the 5m low. If it retraces to touch the 15m breakout level (within a tolerance like 0.1%) and shows a 5m bullish rejection (`lower_wick_ratio >= 0.5`), we enter Long.
   - **Failed Breakout Reversals**: If a 15m breakout occurs but the 5m price closes back inside the band (`close_5m < bb_upper_15m`) with a large upper wick (`upper_wick_ratio >= 0.55`), we enter a reversal Short.
   - **Tighter Stops**: Rather than placing the stop loss using the wide 15m ATR, we place it using the 5m local structure (e.g. just below the 5m swing low or at `close - 1.5 * atr_5m`). This increases our R-multiple potential since the stop-loss distance is smaller.

4. **Dynamic Exits and Risk Scaling**:
   - **Trailing Stop Loss (TSL)**: The backtesting engine's position tracker can be modified to update the active position's `stop_loss` at each 5m bar `i` using a trailing ATR multiplier or trailing swing levels.
   - **Breakeven Stops**: Move the stop loss to the entry price once the trade hits a progress threshold (e.g., $1.0 \times R$).
   - **Exponential Risk decay**: In the order sizing logic (which currently steps down risk from 1% to 0.5% at $\ge 3$ losses), we introduce an exponential decay function: `risk_pct = base_risk_pct * (0.5 ** (consecutive_losses // 3))`.

5. **Lookahead-Free Month Rescue (derived from `test_phase7_verification.py` and `engine.py`)**:
   - The Month-to-Date (MTD) drawdown and trade count are calculated bar-by-bar at index `i` using only the historical records of the current calendar month.
   - **Bad-Month Conversion**: If MTD drawdown reaches a threshold (e.g. 2.0%), we set `risk_pct = 0.0` for the remainder of that month, ensuring the month's loss is capped lookahead-free.
   - **Zero-Month Rescue**: If the day of the month is $\ge 15$ and the trade count is 0, we loosen the trend/regime filters and enable high-probability reversion setups (e.g., "Trend-Following Bollinger Reclaim Reversion" on 5m) to capture trades in low-activity months.

---

## 3. Caveats
- **Pre-calculation of HTF Indicators**: All technical indicators for the 15m and 1h dataframes must be calculated *before* merging. If indicators are computed on resampled/merged columns in the 5m dataframe, they will incorporate lookahead bias due to forward-filled values.
- **Slippage on Tighter Stops**: Using tighter 5m stop losses means stop market orders are triggered closer to the entry price. Under high volatility, slippage might represent a larger percentage of the stop-loss distance, which must be accounted for in the slippage parameter of the engine.
- **Execution Delay Compatibility**: The engine's `delay_candles` parameter must be compatible with the micro-execution rules. If there is a 1-candle delay on a 5m timeframe, the entry will be filled at the open of the next 5m candle, which is standard.

---

## 4. Conclusion
We conclude that Phase 8's MTF strategy can be fully implemented in a lookahead-free manner with 5m execution precision, tighter stops, trailing exits, and monthly risk/rescue throttles.

### Proposed Architecture:
1. **Data Pipeline**:
   - Compute `close_time` for all timeframes:
     `df['close_time'] = df['open_time'] + duration_ms`
   - Merge 15m and 1h indicators onto the 5m dataframe using `pd.merge_asof` with `direction="backward"` on `close_time`.
2. **Strategy Trigger Logic**:
   - Query 1h columns for trend/regime filters, 15m columns for setups (e.g., Bollinger breakout), and 5m columns for entry confirmation (e.g., candle reclaim or breakout of the previous 5m high).
3. **Dynamic Stop placement**:
   - Place stop losses at `close - 1.5 * atr_5m` or the 5m local swing low.
4. **Engine Extensions**:
   - Bar-by-bar trailing stops and breakeven adjustments.
   - Exponential loss-streak sizing decay.
   - Dynamic MTD drawdown halting and late-month rescue activation.

---

## 5. Verification Method
To independently verify the correctness and lookahead-free nature of the MTF strategy:

### A. Pandastest for Lookahead-Free Merging
Run the following script to confirm that the merge does not introduce lookahead bias:
```python
import pandas as pd
import numpy as np

def verify_mtf_merge(df_5m, df_15m, df_1h):
    # Compute close times
    df_5m['close_time'] = df_5m['open_time'] + 5 * 60 * 1000
    df_15m['close_time'] = df_15m['open_time'] + 15 * 60 * 1000
    df_1h['close_time'] = df_1h['open_time'] + 60 * 60 * 1000
    
    # Sort
    df_5m = df_5m.sort_values('close_time')
    df_15m = df_15m.sort_values('close_time')
    df_1h = df_1h.sort_values('close_time')
    
    # Rename columns to avoid collision
    df_15m_merged = df_15m.add_suffix('_15m').rename(columns={'close_time_15m': 'close_time'})
    df_1h_merged = df_1h.add_suffix('_1h').rename(columns={'close_time_1h': 'close_time'})
    
    # Merges
    df_aligned = pd.merge_asof(df_5m, df_15m_merged, on='close_time', direction='backward')
    df_aligned = pd.merge_asof(df_aligned, df_1h_merged, on='close_time', direction='backward')
    
    # Check that at any index, close_15m belongs to a candle that has closed
    for idx, row in df_aligned.iterrows():
        # The 15m candle's close time must be <= the 5m candle's close time
        assert row['close_time_15m'] <= row['close_time']
        # The 1h candle's close time must be <= the 5m candle's close time
        assert row['close_time_1h'] <= row['close_time']
        
    print("Alignment verification passed: No lookahead leakage detected.")
```

### B. Signal Leakage Unit Test
Add a test in `tests/test_phase8_verification.py` based on dataframe truncation:
```python
def test_mtf_strategy_no_lookahead():
    # 1. Generate full merged 5m dataframe
    df_full = generate_mock_merged_df()
    strategy = UniversalStrategyTemplate(params={"mtf_mode": True})
    
    # 2. Get signal on a truncated version up to index i
    i = 100
    df_trunc = df_full.iloc[:i+1].copy()
    sig_trunc = strategy.get_signal(df_trunc, i)
    
    # 3. Modify future rows in df_full (index > i) with extreme values
    df_leak = df_full.copy()
    df_leak.loc[i+1:, ["close", "close_15m", "close_1h"]] = 999999.0
    
    # 4. Get signal on the modified dataframe at index i
    sig_leak = strategy.get_signal(df_leak, i)
    
    # 5. Assert that the signals are identical
    assert sig_trunc == sig_leak, "Lookahead leakage: Future data modified strategy output at historical index!"
```

### C. Running Pytest
Execute the test command from the root directory to verify that all unit and E2E tests pass:
```powershell
pytest tests/
```
