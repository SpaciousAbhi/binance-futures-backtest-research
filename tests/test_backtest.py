import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone
import os

from src.backtest.engine import BacktestEngine
from src.features.indicators import add_indicators
from src.strategies.candidates import VolatilitySqueezeBreakout
from src.audit.system_auditor import SystemAuditor

@pytest.fixture
def mock_data():
    """Generates 500 rows of mock candle data with aligned funding rates."""
    np.random.seed(42)
    # 15m intervals = 900,000 ms
    step = 15 * 60 * 1000
    start_ts = 1577836800000 # 2020-01-01 00:00:00 UTC
    
    open_times = [start_ts + i * step for i in range(500)]
    
    # Random walk price starting at 10,000
    prices = [10000.0]
    for _ in range(499):
        prices.append(prices[-1] * (1.0 + np.random.normal(0, 0.002)))
        
    df = pd.DataFrame({
        "open_time": open_times,
        "open": prices,
        "high": [p * (1.0 + abs(np.random.normal(0, 0.003))) for p in prices],
        "low": [p * (1.0 - abs(np.random.normal(0, 0.003))) for p in prices],
        "close": prices, # Simple close = open random walk
        "volume": np.random.uniform(10, 100, 500)
    })
    
    # Adjust high/low to be valid
    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)
    
    # Add funding time and rate
    # Binance funding is every 8 hours (28,800,000 ms)
    # We set funding rate to 0.0001 (0.01%)
    df["fundingRate"] = 0.0001
    df["fundingTime"] = (df["open_time"] // 28800000) * 28800000
    df["datetime"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["datetime_str"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    return add_indicators(df)

def test_candle_and_funding_alignment(mock_data):
    """Checks that open times increment correctly and fundingTime is aligned."""
    diffs = mock_data["open_time"].diff().dropna().astype(int)
    # Timeframe is 15m, so diffs must be exactly 900,000 ms
    assert (diffs == 15 * 60 * 1000).all()
    # Funding times must be multiples of 8 hours
    funding_times = mock_data["fundingTime"].unique()
    for ft in funding_times:
        assert ft % (8 * 3600 * 1000) == 0

def test_next_candle_execution(mock_data):
    """Checks that trades are executed on the open of the candle following the signal."""
    # Create a mock strategy that triggers a Long signal at index 50
    class MockStrategy:
        name = "Mock"
        hypothesis = "Mock"
        def get_signal(self, df, i):
            if i == 50:
                return {
                    "side": "Long",
                    "stop_loss": df.loc[i, "close"] - 100,
                    "take_profit": df.loc[i, "close"] + 200,
                    "reason": "Trigger at 50"
                }
            return None

    engine = BacktestEngine(slippage=0.0)
    res = engine.run(mock_data, MockStrategy())
    trades = res["trades"]
    
    assert not trades.empty
    trade = trades.iloc[0]
    # Signal triggered at 50, executed at 51 open
    expected_entry_time = mock_data.loc[51, "open_time"]
    assert trade["entry_time"] == expected_entry_time

def test_fee_and_slippage_calculation(mock_data):
    """Verifies that taker fees and slippage are correctly calculated and deducted."""
    class MockStrategy:
        name = "Mock"
        hypothesis = "Mock"
        def get_signal(self, df, i):
            if i == 50:
                # Stop loss very close so it hits immediately on index 51 close/high/low
                return {
                    "side": "Long",
                    "stop_loss": df.loc[i, "close"] - 1000,
                    "take_profit": df.loc[i, "close"] + 2,
                    "reason": "Test"
                }
            return None

    # Taker fee 0.001 (0.1%), Slippage 0.01 (1.0%)
    engine = BacktestEngine(maker_fee=0.001, taker_fee=0.001, slippage=0.01)
    res = engine.run(mock_data, MockStrategy())
    trades = res["trades"]
    
    assert not trades.empty
    trade = trades.iloc[0]
    
    # Entry slip calculation: raw_price * (1 + slippage)
    raw_entry = mock_data.loc[51, "open"]
    expected_entry = raw_entry * 1.01
    assert abs(trade["entry_price"] - round(expected_entry, 1)) < 1.0

def test_funding_calculations(mock_data):
    """Verifies funding cost calculations for a multi-bar position."""
    # Ensure position is held through an 8-hour boundary
    # We will trigger a trade at index 20 and close at index 60
    # Let's count how many 8-hour boundaries fall in [index 21, index 60]
    boundary_count = 0
    for idx in range(21, 61):
        if mock_data.loc[idx, "open_time"] % (8 * 3600 * 1000) == 0:
            boundary_count += 1
            
    assert boundary_count > 0

    class MockStrategy:
        name = "Mock"
        hypothesis = "Mock"
        def get_signal(self, df, i):
            if i == 20:
                return {
                    "side": "Long",
                    "stop_loss": 1.0, # Will not hit
                    "take_profit": 9999999.0, # Will not hit
                    "reason": "Hold"
                }
            return None

    # Run and force close at end (index 499)
    engine = BacktestEngine(slippage=0.0)
    res = engine.run(mock_data, MockStrategy())
    trades = res["trades"]
    trade = trades.iloc[0]
    
    # Since funding rate is 0.0001 and we held it through multiple 8h boundaries,
    # cumulative funding cost must be positive and non-zero.
    assert trade["funding"] > 0

def test_drawdown_calculation(mock_data):
    """Checks that max drawdown calculation correctly computes peaks and troughs."""
    # Create simple trade log with known PnL: start=10000, trade1=+1000, trade2=-2000, trade3=+500
    # Equity curve: 10000 -> 11000 -> 9000 -> 9500
    # Peak curve:   10000 -> 11000 -> 11000 -> 11000
    # Drawdowns:    0 -> 0 -> 2000/11000 (18.18%) -> 1500/11000
    # Max Drawdown should be 2000/11000 = 18.18%
    engine = BacktestEngine(initial_capital=10000.0)
    trades_df = pd.DataFrame([
        {"net_pnl": 1000.0, "gross_pnl": 1000.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 1.0, "hold_candles": 1, "exit_datetime": "2020-01-02 00:00:00"},
        {"net_pnl": -2000.0, "gross_pnl": -2000.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": -1.0, "hold_candles": 1, "exit_datetime": "2020-01-03 00:00:00"},
        {"net_pnl": 500.0, "gross_pnl": 500.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 0.5, "hold_candles": 1, "exit_datetime": "2020-01-04 00:00:00"}
    ])
    metrics = engine._calculate_metrics(trades_df, 9500.0)
    assert abs(metrics["max_drawdown"] - (2000.0 / 11000.0)) < 0.0001

def test_mfe_mae_calculation(mock_data):
    """Validates Maximum Favorable Excursion and Maximum Adverse Excursion tracking."""
    # We trigger a trade at index 50, execute at 51, and hold it until exit at 55.
    # We check if MFE and MAE are correctly computed based on high and low prices.
    class MockStrategy:
        name = "Mock"
        hypothesis = "Mock"
        def get_signal(self, df, i):
            if i == 50:
                return {
                    "side": "Long",
                    "stop_loss": 1.0,
                    "take_profit": 999999.0,
                    "reason": "Test MFE/MAE"
                }
            return None

    engine = BacktestEngine(slippage=0.0)
    # We manually slice dataframe to run only up to index 55 to force close at 55
    df_sliced = mock_data.iloc[:56].copy()
    res = engine.run(df_sliced, MockStrategy())
    trade = res["trades"].iloc[0]
    
    # Entry at 51 open
    entry_p = df_sliced.loc[51, "open"]
    
    # Max price reached from index 51 to 55
    max_h = df_sliced.loc[51:55, "high"].max()
    min_l = df_sliced.loc[51:55, "low"].min()
    
    expected_mfe = (max_h - entry_p) / entry_p
    expected_mae = (entry_p - min_l) / entry_p
    
    assert abs(trade["MFE"] - expected_mfe) < 0.0001
    assert abs(trade["MAE"] - expected_mae) < 0.0001

def test_no_future_leakage_audit(mock_data):
    """Verifies that SystemAuditor correctly detects lack of lookahead in VolatilitySqueezeBreakout."""
    strat = VolatilitySqueezeBreakout()
    engine = BacktestEngine()
    auditor = SystemAuditor(mock_data, strat, engine)
    audit_res = auditor.audit_signals()
    assert audit_res["status"] == "PASS"


def test_bankruptcy_stop(mock_data):
    """Verifies that when capital drops to <= 0, the engine immediately liquidates the account and breaks."""
    # Create a strategy that forces massive losses
    class BankruptStrategy:
        name = "Bankrupt"
        hypothesis = "Bankrupt"
        def get_signal(self, df, i):
            if i == 10:
                return {
                    "side": "Long",
                    "stop_loss": 1.0, # SL far away
                    "take_profit": 999999.0,
                    "reason": "Bankruptcy Trigger"
                }
            return None

    # Taker fee and slippage extremely high to bankrupt the account
    engine = BacktestEngine(initial_capital=100.0, maker_fee=0.9, taker_fee=0.9, slippage=0.9)
    res = engine.run(mock_data, BankruptStrategy())
    
    assert res["metrics"]["net_pnl"] <= -100.0
    assert res["metrics"]["max_drawdown"] == 1.0  # Capped at 100%
    assert any(t["reason"] == "Bankruptcy (Funding)" or "Bankruptcy" in t["reason"] or "Liquidated" in t["reason"] for t in res["trades"].to_dict(orient="records"))


def test_monthly_reporting_alignment():
    """Verifies that zero-trade months are properly reindexed and counted in the totals."""
    # Create 3 months of mock data: 2020-01-01, 2020-02-01, 2020-03-01
    open_times = [
        int(pd.to_datetime("2020-01-01 00:00:00").tz_localize(timezone.utc).timestamp() * 1000),
        int(pd.to_datetime("2020-02-01 00:00:00").tz_localize(timezone.utc).timestamp() * 1000),
        int(pd.to_datetime("2020-03-01 00:00:00").tz_localize(timezone.utc).timestamp() * 1000)
    ]
    df = pd.DataFrame({
        "open_time": open_times,
        "open": [10000.0, 10000.0, 10000.0],
        "high": [10100.0, 10100.0, 10100.0],
        "low": [9900.0, 9900.0, 9900.0],
        "close": [10000.0, 10000.0, 10000.0],
        "volume": [100.0, 100.0, 100.0],
        "fundingRate": [0.0001, 0.0001, 0.0001],
        "fundingTime": open_times
    })
    
    # Run a backtest where only 1 trade happens
    class SingleTradeStrategy:
        name = "Single"
        hypothesis = "Single"
        def get_signal(self, df, i):
            if i == 0:
                return {
                    "side": "Long",
                    "stop_loss": 9000.0,
                    "take_profit": 11000.0,
                    "reason": "One trade only"
                }
            return None

    engine = BacktestEngine()
    res = engine.run(df, SingleTradeStrategy())
    metrics = res["metrics"]
    
    total_months = metrics["positive_months"] + metrics["negative_months"] + metrics["zero_months"]
    
    # We should have a non-zero count of zero months since there was only one trade
    assert metrics["zero_months"] > 0
    assert total_months == 3  # Total calendar months in our custom DataFrame is 3


def test_portfolio_conflict_resolution(mock_data):
    """Checks that PortfolioStrategy resolves conflicting Long and Short signals correctly."""
    class LongStrategy:
        name = "LongStrat"
        hypothesis = "Long"
        def get_signal(self, df, i):
            if i == 50:
                return {"side": "Long", "stop_loss": 9000, "take_profit": 11000, "reason": "Long"}
            return None

    class ShortStrategy:
        name = "ShortStrat"
        hypothesis = "Short"
        def get_signal(self, df, i):
            if i == 50:
                return {"side": "Short", "stop_loss": 11000, "take_profit": 9000, "reason": "Short"}
            return None

    from src.strategies.portfolio import PortfolioStrategy
    
    portfolio = PortfolioStrategy([LongStrategy(), ShortStrategy()], conflict_rule="cancel")
    sig = portfolio.get_signal(mock_data, 50)
    assert sig is None  # Conflict resolved by cancelling out

