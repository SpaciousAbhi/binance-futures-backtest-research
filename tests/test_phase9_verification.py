import pytest
import pandas as pd
import numpy as np
from src.backtest.engine import BacktestEngine

def generate_simple_mock_df(prices):
    n = len(prices)
    times = pd.date_range("2026-06-30 00:00:00", periods=n, freq="1h")
    df = pd.DataFrame({
        "open_time": times.astype("datetime64[ns]").astype(np.int64) // 10**6,
        "open": prices,
        "high": [p + 0.5 for p in prices],
        "low": [p - 0.5 for p in prices],
        "close": prices,
        "volume": np.ones(n) * 100,
        "fundingRate": np.zeros(n),
        "atr_14": np.ones(n) * 1.0
    })
    df["close_time"] = df["open_time"] + 3600000
    df["datetime_str"] = times.strftime("%Y-%m-%d %H:%M:%S")
    return df

def test_single_engine_trailing_stop_long():
    # Long trade entered at index 1 (price 100.0), SL is 98.0
    # Price rises to 103.0 at index 2 (high = 103.5 -> peak_price = 103.5)
    # Trailing Stop = peak_price - 2.0 * atr = 103.5 - 2.0 = 101.5
    # Price drops to 101.0 at index 3 (low = 100.5), which hits 101.5 trailing SL.
    prices = [100.0, 100.0, 103.0, 101.0, 100.0]
    df = generate_simple_mock_df(prices)
    
    class MockStrategy:
        def get_signal(self, df_in, idx):
            if idx == 0: # entry executed at idx 1
                return {
                    "side": "Long",
                    "stop_loss": 98.0,
                    "take_profit": 110.0,
                    "trail_atr_mult": 2.0,
                    "atr": 1.0
                }
            return None

    engine = BacktestEngine(initial_capital=10000.0, slippage=0.0005)
    res = engine.run(df, MockStrategy())
    trades = res["trades"]
    
    assert not trades.empty
    trade = trades.iloc[0]
    assert trade["reason"] == "Stop Loss"
    # Exit price should be the trailed stop loss (101.5) adjusted for entry-slippage and exit-slippage
    # Since we set slippage=0.0005, exit price is 101.5 * (1 - 0.0005) = 101.44925
    expected_exit = 101.5 * (1.0 - 0.0005)
    assert pytest.approx(trade["exit_price"]) == expected_exit

def test_single_engine_breakeven_long():
    # Long trade entered at index 1 (price 100.0), SL is 98.0
    # Price rises to 102.5 at index 2 (high = 103.0 -> peak_price = 103.0)
    # Breakeven moves SL to entry_price (100.0) since peak >= entry + 2.0 * atr (102.0)
    # Price drops to 99.0 at index 3 (low = 98.5). It hits 100.0 (breakeven SL) instead of initial SL.
    prices = [100.0, 100.0, 102.5, 99.0, 98.0]
    df = generate_simple_mock_df(prices)
    
    class MockStrategy:
        def get_signal(self, df_in, idx):
            if idx == 0:
                return {
                    "side": "Long",
                    "stop_loss": 98.0,
                    "take_profit": 110.0,
                    "breakeven_atr_mult": 2.0,
                    "atr": 1.0
                }
            return None

    engine = BacktestEngine(initial_capital=10000.0, slippage=0.0005)
    res = engine.run(df, MockStrategy())
    trades = res["trades"]
    
    assert not trades.empty
    trade = trades.iloc[0]
    assert trade["reason"] == "Stop Loss"
    expected_exit = 100.0 * (1.0 - 0.0005)
    assert pytest.approx(trade["exit_price"]) == expected_exit

def test_single_engine_sl_tp_priority():
    # Long trade entered at index 1 (price 100.0), SL 99.0, TP 101.0
    # At index 2: high = 101.5, low = 98.5. Both SL and TP are hit on the same candle.
    # The engine should prioritize SL for conservative safety.
    prices = [100.0, 100.0, 100.0, 100.0]
    df = generate_simple_mock_df(prices)
    df.loc[2, "high"] = 102.0
    df.loc[2, "low"] = 98.0
    
    class MockStrategy:
        def get_signal(self, df_in, idx):
            if idx == 0:
                return {
                    "side": "Long",
                    "stop_loss": 99.0,
                    "take_profit": 101.0
                }
            return None

    engine = BacktestEngine(initial_capital=10000.0, slippage=0.0005)
    res = engine.run(df, MockStrategy())
    trades = res["trades"]
    
    assert not trades.empty
    trade = trades.iloc[0]
    assert trade["reason"] == "Stop Loss"
    expected_exit = 99.0 * (1.0 - 0.0005)
    assert pytest.approx(trade["exit_price"]) == expected_exit
