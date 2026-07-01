import pytest
import pandas as pd
import numpy as np
from src.data.processor import DataProcessor
from src.backtest.engine import MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate, MTFBreakoutStrategy
from src.strategies.portfolio import PortfolioStrategy

# Simple helper to generate mock DataFrames
def generate_mock_dfs():
    # 5m timestamps: 100 bars
    times_5m = pd.date_range("2026-06-30 00:00:00", periods=100, freq="5min")
    df_5m = pd.DataFrame({
        "open_time": times_5m.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open": np.linspace(100.0, 110.0, 100),
        "high": np.linspace(101.0, 111.0, 100),
        "low": np.linspace(99.0, 109.0, 100),
        "close": np.linspace(100.0, 110.0, 100),
        "volume": np.ones(100) * 100,
        "fundingRate": np.zeros(100),
        "atr_14": np.ones(100) * 1.0,
        "swing_low": np.ones(100) * 98.0,
        "swing_high": np.ones(100) * 112.0,
    })
    df_5m["close_time"] = df_5m["open_time"] + 300000

    # 15m timestamps: 34 bars
    times_15m = pd.date_range("2026-06-30 00:00:00", periods=34, freq="15min")
    df_15m = pd.DataFrame({
        "open_time": times_15m.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open": np.linspace(100.0, 110.0, 34),
        "high": np.linspace(102.0, 112.0, 34),
        "low": np.linspace(98.0, 108.0, 34),
        "close": np.linspace(100.0, 110.0, 34),
        "bb_upper": np.linspace(101.5, 111.5, 34),
        "bb_lower": np.linspace(98.5, 108.5, 34)
    })
    df_15m["close_time"] = df_15m["open_time"] + 900000

    # 1h timestamps: 9 bars
    times_1h = pd.date_range("2026-06-30 00:00:00", periods=9, freq="1h")
    df_1h = pd.DataFrame({
        "open_time": times_1h.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open": np.linspace(100.0, 110.0, 9),
        "high": np.linspace(104.0, 114.0, 9),
        "low": np.linspace(96.0, 106.0, 9),
        "close": np.linspace(100.0, 110.0, 9),
        "ema_200": np.linspace(95.0, 105.0, 9),
        "regime_bull_trend": np.ones(9, dtype=bool),
        "regime_vol_expansion": np.zeros(9, dtype=bool)
    })
    df_1h["close_time"] = df_1h["open_time"] + 3600000

    return df_5m, df_15m, df_1h

def test_mtf_lookahead_free_alignment():
    df_5m, df_15m, df_1h = generate_mock_dfs()
    
    # Perform alignment
    merged = DataProcessor.align_multitimeframe_data(df_5m, df_15m, df_1h)
    
    # Check that it contains suffixed columns
    assert "close_15m" in merged.columns
    assert "close_1h" in merged.columns
    
    # Lookahead-free check: truncate 1h data to only 3 bars and see if future merged values are NaN or backward matched
    df_1h_trunc = df_1h.iloc[:3].copy() # covers first 3 hours
    merged_trunc = DataProcessor.align_multitimeframe_data(df_5m, df_15m, df_1h_trunc)
    
    # Bar 50 in 5m is at 50 * 5 = 250 minutes (~4.1 hours).
    # Since df_1h_trunc only contains first 3 hours (up to 3 hours close time),
    # the 1h values at index 50 should match the 3rd hour candle (since it's direction='backward')
    # and NOT anything after it.
    last_allowed_close_1h = df_1h_trunc["close"].iloc[-1]
    assert merged_trunc["close_1h"].iloc[50] == last_allowed_close_1h
    
    # Future values beyond the 3rd hour in merged_trunc should not change because they are ffilled backward from index 35 (3 hours)
    # If there was lookahead, merged_trunc would have access to 1h bars after 3 hours. Since they are removed, it only matches the last available one backward.
    assert merged_trunc["close_1h"].iloc[99] == last_allowed_close_1h

def test_closed_candle_compliance():
    # Verify that get_signal only looks at index i and below
    df_5m, df_15m, df_1h = generate_mock_dfs()
    merged = DataProcessor.align_multitimeframe_data(df_5m, df_15m, df_1h)
    
    # Add dummy columns and other indicators to merged df to satisfy strategy checks
    merged["upper_wick_ratio"] = 0.1
    merged["lower_wick_ratio"] = 0.1
    merged["atr_14"] = 1.0
    merged["swing_low"] = 98.0
    merged["swing_high"] = 112.0
    
    strat = MTFBreakoutStrategy()
    
    # Truncate dataframe at index 50
    df_trunc = merged.iloc[:51].copy()
    sig_1 = strat.get_signal(df_trunc, 50)
    
    # If we append a bar with future data at 51, it should not affect signal at 50
    df_future = merged.copy()
    df_future.loc[51, "close_15m"] = 999999.0
    df_future.loc[51, "close_1h"] = 999999.0
    
    # Clear cache
    if hasattr(strat.template, "_cached_df_id"):
        delattr(strat.template, "_cached_df_id")
        
    sig_2 = strat.get_signal(df_future, 50)
    
    # Both signals should be exactly the same
    assert sig_1 == sig_2

def test_trailing_and_breakeven_stops():
    # Setup a mock DataFrame
    times = pd.date_range("2026-06-30 00:00:00", periods=10, freq="5min")
    df = pd.DataFrame({
        "open_time": times.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open":  [100.0, 101.0, 102.0, 103.0, 104.0, 102.5, 100.0, 99.0, 98.0, 97.0],
        "high":  [101.5, 102.5, 103.5, 104.5, 105.5, 103.5, 101.0, 99.5, 98.5, 97.5],
        "low":   [ 99.5, 100.5, 102.1, 103.1, 104.1, 101.5,  99.5, 98.0, 97.0, 96.0],
        "close": [101.0, 102.0, 103.0, 104.0, 103.0, 102.0,  99.5, 98.5, 97.5, 96.5],
        "volume": np.ones(10) * 100,
        "fundingRate": np.zeros(10),
        "atr_14": np.ones(10) * 1.0
    })
    df["close_time"] = df["open_time"] + 300000
    df["datetime_str"] = times.strftime("%Y-%m-%d %H:%M:%S")
    
    # We will use MultiPositionBacktestEngine to run a simple backtest
    # and verify that stop_loss is updated bar-by-bar
    engine = MultiPositionBacktestEngine(initial_capital=10000.0, slippage=0.0)
    
    class MockTrailingStrategy:
        def __init__(self):
            self.name = "MockTrailingStrategy"
        def get_signal(self, df_in, idx, live_metrics=None):
            if idx == 1: # Trigger entry at index 2
                return {
                    "side": "Long",
                    "stop_loss": 99.0,
                    "take_profit": 110.0,
                    "trail_atr_mult": 1.5,
                    "breakeven_atr_mult": 2.0,
                    "atr": 1.0,
                    "strategy_name": "MockTrailingStrategy"
                }
            return None

    # Let's run the backtest
    res = engine.run(df, MockTrailingStrategy(), {"risk_limit_pct": 1.0, "monthly_risk_limit": 1.0})
    trades = res["trades"]
    
    assert not trades.empty
    trade = trades.iloc[0]
    
    # Entry price at open of index 2 (102.0)
    # Stop loss initial is 99.0
    # Peak price at index 2 high (103.5), index 3 high (104.5), index 4 high (105.5)
    # Peak price reaches 105.5.
    # Breakeven activation: entry_price + 2.0 * atr = 102.0 + 2.0 = 104.0.
    # Peak price 105.5 >= 104.0, so stop_loss moves to entry_price (102.0).
    # Trailing stop activation: peak_price - 1.5 * atr = 105.5 - 1.5 = 104.0.
    # So stop_loss trails to 104.0.
    # At index 5, low goes to 101.5, which is <= 104.0, triggering SL Hit!
    assert trade["reason"] == "SL Hit"
    assert trade["exit_price"] == 104.0

def test_zero_month_rescue_trigger():
    # Create mock df where days_of_month goes from 1 to 20
    times = pd.date_range("2026-06-01", periods=220, freq="h")
    df = pd.DataFrame({
        "open_time": times.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open": np.ones(220) * 100.0,
        "high": np.ones(220) * 101.0,
        "low": np.ones(220) * 99.0,
        "close": np.ones(220) * 100.0,
        "volume": np.ones(220) * 100,
        "fundingRate": np.zeros(220),
        "days_of_month": times.day,
        "ema_200": np.ones(220) * 95.0,
        "ema_50": np.ones(220) * 97.0,
        "bb_lower": np.ones(220) * 99.5,
        "bb_upper": np.ones(220) * 100.5,
        "bb_mid": np.ones(220) * 100.0,
        "bb_width": np.ones(220) * 0.05,
        "rsi_14": np.ones(220) * 30.0,
        "atr_14": np.ones(220) * 1.0,
        "atr_pct": np.ones(220) * 0.5,
        "adx": np.ones(220) * 20.0
    })
    
    # Needs to satisfy some indicators since get_signal will look up swing levels
    df["swing_low"] = 98.0
    df["swing_high"] = 102.0
    df["lower_wick_ratio"] = 0.1
    df["upper_wick_ratio"] = 0.1
    
    filler_cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "low_activity_filler",
        "sl_atr_mult": 2.0,
        "tp_atr_mult": 3.5
    }
    filler_strat = UniversalStrategyTemplate(filler_cfg)
    port = PortfolioStrategy([filler_strat], zero_month_rescue=True)
    
    # 1. Day of month = 5 (less than 10) and trade count = 0.
    # Low activity filler should NOT generate a signal!
    df.loc[204, "days_of_month"] = 5
    sig_1 = port.get_signal(df, 204, live_metrics={"monthly_trade_count": 0})
    assert sig_1 is None
    
    # 2. Day of month = 11 (>= 10) and trade count = 0.
    # Low activity filler should be active and generate a signal because:
    # trend_long (close 100 > ema_200 95), low (99 <= bb_lower 99.5), close (100 > bb_lower 99.5), rsi (30 < 35)
    df.loc[204, "days_of_month"] = 11
    sig_2 = port.get_signal(df, 204, live_metrics={"monthly_trade_count": 0})
    assert sig_2 is not None
    assert sig_2["side"] == "Long"
    assert sig_2["reason"] == "Portfolio Long: Low-Activity Filler Long"
    
    # 3. Day of month = 11 (>= 10) but trade count = 2 (not 0).
    # Since monthly trade count is > 0 and day < 15, low-activity filler should NOT be active!
    sig_3 = port.get_signal(df, 204, live_metrics={"monthly_trade_count": 2})
    assert sig_3 is None


def test_timeframe_1h_resolution_mismatch():
    # 5m timestamps: 300 bars
    times_5m = pd.date_range("2026-06-30 00:00:00", periods=300, freq="5min")
    df_5m = pd.DataFrame({
        "open_time": times_5m.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open": np.linspace(100.0, 110.0, 300),
        "high": np.linspace(101.0, 111.0, 300),
        "low": np.linspace(99.0, 109.0, 300),
        "close": np.linspace(100.0, 110.0, 300),
        "volume": np.ones(300) * 100,
        "fundingRate": np.zeros(300),
        "atr_14": np.ones(300) * 0.5, # Small 5m ATR
        "bb_width": np.ones(300) * 0.01,
        "bb_upper": np.ones(300) * 105.0,
        "bb_lower": np.ones(300) * 95.0,
        "bb_mid": np.ones(300) * 100.0,
        "ema_200": np.ones(300) * 95.0,
        "rsi_14": np.ones(300) * 50.0,
        "atr_pct": np.ones(300) * 0.5,
        "adx": np.ones(300) * 25.0,
        "swing_low": np.ones(300) * 95.0,
        "swing_high": np.ones(300) * 105.0,
        "upper_wick_ratio": np.ones(300) * 0.1,
        "lower_wick_ratio": np.ones(300) * 0.1,
    })
    df_5m["close_time"] = df_5m["open_time"] + 300000

    # 15m timestamps: 100 bars
    times_15m = pd.date_range("2026-06-30 00:00:00", periods=100, freq="15min")
    df_15m = pd.DataFrame({
        "open_time": times_15m.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open": np.linspace(100.0, 110.0, 100),
        "high": np.linspace(101.0, 111.0, 100),
        "low": np.linspace(99.0, 109.0, 100),
        "close": np.linspace(100.0, 110.0, 100),
    })
    df_15m["close_time"] = df_15m["open_time"] + 900000

    # 1h timestamps: 25 bars
    times_1h = pd.date_range("2026-06-30 00:00:00", periods=25, freq="1h")
    df_1h = pd.DataFrame({
        "open_time": times_1h.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open": np.linspace(100.0, 110.0, 25),
        "high": np.linspace(101.0, 111.0, 25),
        "low": np.linspace(99.0, 109.0, 25),
        "close": np.linspace(102.0, 112.0, 25), # Breakout!
        "volume": np.ones(25) * 100,
        "fundingRate": np.zeros(25),
        "bb_width": np.ones(25) * 0.1, # Expansion!
        "bb_upper": np.ones(25) * 101.0,
        "bb_lower": np.ones(25) * 99.0,
        "bb_mid": np.ones(25) * 100.0,
        "ema_200": np.ones(25) * 95.0,
        "rsi_14": np.ones(25) * 50.0,
        "atr_pct": np.ones(25) * 0.5,
        "adx": np.ones(25) * 25.0,
        "swing_low": np.ones(25) * 95.0,
        "swing_high": np.ones(25) * 100.5,
        "upper_wick_ratio": np.ones(25) * 0.1,
        "lower_wick_ratio": np.ones(25) * 0.1,
        "atr_14": np.ones(25) * 3.0, # Large 1h ATR
    })
    df_1h["close_time"] = df_1h["open_time"] + 3600000

    # Align
    df_tf = DataProcessor.align_multitimeframe_data(df_5m, df_15m, df_1h)

    # Strategy config
    cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": "ema_200",
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 2.5, "sl_atr_mult": 1.5,
        "rsi_overbought": 75, "rsi_oversold": 30,
        "adx_thresh": 20, "wick_ratio_thresh": 0.45,
        "timeframe": "1h",
    }
    strategy = UniversalStrategyTemplate(cfg)

    # index 239 is an hour boundary: close_time % 3600000 == 0
    # index 238 and 240 are not.
    assert df_tf["close_time"].values[239] % 3600000 == 0
    assert df_tf["close_time"].values[238] % 3600000 != 0
    assert df_tf["close_time"].values[240] % 3600000 != 0

    # Run get_signal on boundary
    sig_boundary = strategy.get_signal(df_tf, 239)
    assert sig_boundary is not None, "Should generate a signal at hour boundary"
    assert sig_boundary["side"] == "Long"
    # Sizing stop loss should use 1h ATR (3.0), not 5m ATR (0.5).
    # Sized SL = close - 1.5 * ATR_1h = close_1h_val - 1.5 * 3.0
    close_1h_val = df_tf["close_1h"].values[239]
    expected_sl = close_1h_val - 1.5 * 3.0
    assert abs(sig_boundary["stop_loss"] - expected_sl) < 1e-5, f"Stop loss {sig_boundary['stop_loss']} should be based on 1h ATR"

    # Run get_signal on non-boundary indexes
    sig_non_boundary_1 = strategy.get_signal(df_tf, 238)
    assert sig_non_boundary_1 is None, "Should NOT generate a signal off hour boundary"

    sig_non_boundary_2 = strategy.get_signal(df_tf, 240)
    assert sig_non_boundary_2 is None, "Should NOT generate a signal off hour boundary"

    # Verify lookahead-free behaviour: truncating the aligned dataframe at index 239
    # should yield the exact same signal as the full dataframe evaluated at index 239.
    df_trunc = df_tf.iloc[:240].copy()
    if hasattr(strategy, "_cached_df_id"):
        delattr(strategy, "_cached_df_id")
    sig_trunc = strategy.get_signal(df_trunc, 239)
    assert sig_trunc == sig_boundary


def test_phase8_lookahead_free_timeframe_1h():
    df_5m, df_15m, df_1h = generate_mock_dfs()
    df_tf = DataProcessor.align_multitimeframe_data(df_5m, df_15m, df_1h)
    
    # Enrich df_tf with required indicator columns
    df_tf["upper_wick_ratio"] = 0.1
    df_tf["lower_wick_ratio"] = 0.1
    df_tf["atr_14"] = 1.0
    df_tf["swing_low"] = 98.0
    df_tf["swing_high"] = 112.0
    df_tf["atr_14_1h"] = 2.0
    df_tf["bb_upper_1h"] = 105.0
    df_tf["close_1h"] = 106.0
    df_tf["ema_200_1h"] = 95.0
    df_tf["rsi_14_1h"] = 50.0
    df_tf["adx_1h"] = 25.0
    df_tf["close_time"] = df_tf["open_time"] + 300000
    
    # Boundary check at close_time multiple of 3600000 (say index 11 which closes at 1 hour)
    cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": "ema_200",
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.5,
        "timeframe": "1h",
    }
    strategy = UniversalStrategyTemplate(cfg)
    
    # Check that index 11 is boundary
    assert df_tf["close_time"].values[11] % 3600000 == 0
    assert df_tf["close_time"].values[10] % 3600000 != 0
    
    # Clear cache
    if hasattr(strategy, "_cached_df_id"):
        delattr(strategy, "_cached_df_id")
        
    sig_11 = strategy.get_signal(df_tf, 11)
    
    # If we truncate the dataframe at 11, the signal should be identical (no lookahead)
    df_trunc = df_tf.iloc[:12].copy()
    if hasattr(strategy, "_cached_df_id"):
        delattr(strategy, "_cached_df_id")
    sig_trunc = strategy.get_signal(df_trunc, 11)
    
    assert sig_11 == sig_trunc


