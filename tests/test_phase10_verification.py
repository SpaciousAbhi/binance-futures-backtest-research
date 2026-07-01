import pytest
import numpy as np
import pandas as pd
from src.features.indicators import add_indicators
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy, FusionOfFusionsStrategy
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine


def test_adx_slope_calculation():
    # Create mock data with increasing ADX values
    dates = pd.date_range(start="2026-01-01", periods=50, freq="h")
    df = pd.DataFrame({
        "open_time": [int(d.timestamp() * 1000) for d in dates],
        "open": np.linspace(100, 110, 50),
        "high": np.linspace(101, 111, 50),
        "low": np.linspace(99, 109, 50),
        "close": np.linspace(100.5, 110.5, 50),
        "volume": np.ones(50) * 1000,
        "fundingRate": np.zeros(50)
    })
    
    df_enriched = add_indicators(df)
    
    # Verify that ADX slope columns exist
    assert "adx_slope_1" in df_enriched.columns
    assert "adx_slope_3" in df_enriched.columns
    assert "adx_slope_5" in df_enriched.columns
    
    # Check slope value calculation
    # For a point i, diff(3) should be adx[i] - adx[i-3]
    adx_val = df_enriched["adx"].values
    adx_slope_3 = df_enriched["adx_slope_3"].values
    
    for idx in range(3, 50):
        expected_diff = adx_val[idx] - adx_val[idx-3]
        assert np.isclose(adx_slope_3[idx], expected_diff)


def test_volume_trend_calculation():
    dates = pd.date_range(start="2026-01-01", periods=30, freq="h")
    # Set volume so it has a sudden surge at index 25
    volume = np.ones(30) * 100
    volume[25] = 500
    
    df = pd.DataFrame({
        "open_time": [int(d.timestamp() * 1000) for d in dates],
        "open": np.ones(30) * 100,
        "high": np.ones(30) * 101,
        "low": np.ones(30) * 99,
        "close": np.ones(30) * 100.5,
        "volume": volume,
        "fundingRate": np.zeros(30)
    })
    
    df_enriched = add_indicators(df)
    
    assert "volume_trend" in df_enriched.columns
    
    # Calculate rolling volume manually
    series_vol = pd.Series(volume)
    expected_trend = (series_vol / series_vol.rolling(20).mean()).fillna(1.0).values
    
    assert np.allclose(df_enriched["volume_trend"].values, expected_trend)


def test_fof_routing_and_logging():
    # Create dummy strategy classes that return mock signals
    class MockStrategy:
        def __init__(self, name, side):
            self.name = name
            self.side = side
            
        def get_signal(self, df, i, live_metrics=None):
            return {"side": self.side, "stop_loss": 10.0, "take_profit": 20.0, "reason": "mock"}

    dates = pd.date_range(start="2026-01-01", periods=10, freq="h")
    df = pd.DataFrame({
        "open_time": [int(d.timestamp() * 1000) for d in dates],
        "close": np.ones(10) * 100
    })
    
    s_act = MockStrategy("activity", "Long")
    s_def = MockStrategy("defensive", "Short")
    
    fof = FusionOfFusionsStrategy({
        "activity": s_act,
        "defensive": s_def
    }, conflict_rule="cancel")
    
    # Test case A: Low trades (< 5) and low drawdown (< 1.5%)
    # Under this condition:
    # - activity fusion is ACTIVE (monthly_trades = 0 < 5) -> yields Long
    # - defensive fusion is INACTIVE (monthly_dd = 0.0 < 1.5%) -> skipped
    # Result should be Long signal from activity
    live_a = {"monthly_trade_count": 0, "monthly_dd": 0.0}
    sig_a = fof.get_signal(df, 5, live_metrics=live_a)
    assert sig_a is not None
    assert sig_a["side"] == "Long"
    
    # Verify signal logging is populated
    assert len(fof.signal_logs) > 0
    latest_logs = fof.signal_logs[-3:] # check last entries
    # Make sure we have sub_portfolio routing entries
    assert any(log["sub_portfolio"] == "activity" for log in latest_logs)
    assert any(log["sub_portfolio"] == "defensive" for log in latest_logs)
    
    # Test case B: High trades (>= 5) and high drawdown (>= 1.5%)
    # Under this condition:
    # - activity fusion is INACTIVE (monthly_trades = 6 >= 5) -> skipped
    # - defensive fusion is ACTIVE (monthly_dd = 0.02 >= 1.5%) -> yields Short
    # Result should be Short signal from defensive
    live_b = {"monthly_trade_count": 6, "monthly_dd": 0.02}
    sig_b = fof.get_signal(df, 5, live_metrics=live_b)
    assert sig_b is not None
    assert sig_b["side"] == "Short"


def test_no_fake_audit_rules(mocker):
    from src.audit.system_auditor import SystemAuditor
    from unittest.mock import mock_open, patch
    
    class DummyStrategy:
        pass
        
    strategy = DummyStrategy()
    auditor = SystemAuditor(df=None, strategy=strategy, engine=None)
    
    # 1. Safe code content (if not i, if i == 0)
    safe_code = """
    def get_signal(self, df, i):
        if not i:
            self.signal_logs = []
        if i == 0:
            return None
        return {"side": "Long"}
    """
    with patch("inspect.getfile", return_value="/path/to/strategy.py"):
        with patch("builtins.open", mock_open(read_data=safe_code)):
            res = auditor.audit_no_fake()
            assert res["status"] == "PASS"
            assert not res["reasons"]
        
    # 2. Violating code content (if i == 520)
    violating_code = """
    def get_signal(self, df, i):
        if i == 520:
            return {"side": "Long"}
        return None
    """
    with patch("inspect.getfile", return_value="/path/to/strategy.py"):
        with patch("builtins.open", mock_open(read_data=violating_code)):
            res = auditor.audit_no_fake()
            assert res["status"] == "FAIL"
            assert any("if i ==" in r or "Potential trade/signal" in r for r in res["reasons"])
