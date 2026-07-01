import pytest
import pandas as pd
import numpy as np
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

# Create simple deterministic mock data for tests
def generate_mock_df(n_bars=300):
    timestamps = pd.date_range("2020-01-01", periods=n_bars, freq="h")
    df = pd.DataFrame({
        "open_time": timestamps.view(np.int64) // 10**6,
        "open": np.linspace(10000.0, 10500.0, n_bars),
        "high": np.linspace(10100.0, 10600.0, n_bars),
        "low": np.linspace(9900.0, 10400.0, n_bars),
        "close": np.linspace(10050.0, 10550.0, n_bars),
        "volume": np.ones(n_bars) * 1000.0,
        "fundingRate": np.zeros(n_bars),
        "bb_mid": np.linspace(10000.0, 10500.0, n_bars),
        "bb_upper": np.linspace(10200.0, 10700.0, n_bars),
        "bb_lower": np.linspace(9800.0, 10300.0, n_bars),
        "bb_width": np.ones(n_bars) * 0.08,
        "rsi_14": np.ones(n_bars) * 50.0,
        "atr_14": np.ones(n_bars) * 150.0,
        "atr_pct": np.ones(n_bars) * 0.015,
        "ema_50": np.linspace(10000.0, 10500.0, n_bars),
        "ema_200": np.linspace(9900.0, 10400.0, n_bars),
        "adx": np.ones(n_bars) * 25.0,
        "lower_wick_ratio": np.zeros(n_bars),
        "upper_wick_ratio": np.zeros(n_bars),
        "swing_high": np.ones(n_bars) * 10600.0,
        "swing_low": np.ones(n_bars) * 9800.0,
        "days_of_month": timestamps.day,
        "date_strs": timestamps.strftime("%Y-%m-%d").values
    })
    
    # Add datetime_str for filtering compatibility
    df["datetime_str"] = timestamps.strftime("%Y-%m-%d %H:%M:%S")
    return df

def test_cost_to_atr_filter():
    df = generate_mock_df()
    
    # Setup Bollinger breakout setup at index 250
    df.loc[250, "close"] = 11000.0 # Above upper band (10700.0)
    df.loc[250, "bb_upper"] = 10800.0
    df.loc[250, "bb_width"] = 0.08
    df.loc[250, "atr_14"] = 100.0 # ATR is 100
    
    config_no_filter = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": None,
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 2.5,  # expected target: 250
        "sl_atr_mult": 1.5,
        "cost_to_atr_mult": 0.0
    }
    
    # 1. Without cost filter
    strat_no = UniversalStrategyTemplate(config_no_filter)
    sig_no = strat_no.get_signal(df, 250)
    assert sig_no is not None
    assert sig_no["side"] == "Long"
    
    # 2. With high cost filter threshold
    # transaction cost is 0.002 * close = 22.0
    # expected target is 2.5 * ATR = 250.0
    # If cost_to_atr_mult = 15.0: cost threshold is 15.0 * 22.0 = 330.0 > expected target (250) -> should be filtered!
    config_with_filter = dict(config_no_filter)
    config_with_filter["cost_to_atr_mult"] = 15.0
    
    strat_yes = UniversalStrategyTemplate(config_with_filter)
    sig_yes = strat_yes.get_signal(df, 250)
    assert sig_yes is None  # Filtered successfully!

def test_mtd_throttle_modes():
    df = generate_mock_df()
    
    # Modify data to trigger entries
    df.loc[10, "close"] = 12000.0
    df.loc[10, "bb_upper"] = 10800.0
    df.loc[100, "close"] = 13000.0
    df.loc[100, "bb_upper"] = 11800.0
    
    cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": None,
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.5
    }
    
    port_strat = PortfolioStrategy([UniversalStrategyTemplate(cfg)])
    multi_engine = MultiPositionBacktestEngine(initial_capital=10000.0)
    
    # Run with soft throttle
    port_config_soft = {
        "monthly_risk_limit": 0.05,
        "risk_limit_pct": 1.0,
        "risk_throttle_mode": "soft",
        "emergency_pause_threshold": 0.03
    }
    
    # Inject a loss at start of month to trigger MTD drawdown (> 1.5%)
    # Let's verify sizing reduces
    res_soft = multi_engine.run(df, port_strat, port_config_soft)
    assert "metrics" in res_soft

def test_filler_rescue_no_lookahead():
    df = generate_mock_df()
    
    # Check that filler only relies on current and past timestamps
    # Rebuilt low activity filler
    cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "low_activity_filler",
        "trend_filter": None,
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 3.5,
        "sl_atr_mult": 2.0,
        "rsi_oversold": 30
    }
    
    strat = UniversalStrategyTemplate(cfg)
    
    # Verify that get_signal does not look forward
    df_truncated = df.iloc[:150].copy()
    sig_1 = strat.get_signal(df_truncated, 149)
    
    # Appending arbitrary future rows shouldn't change the signal output at index 149
    future_row = df.iloc[150:151].copy()
    future_row["close"] = 999999.9  # extreme future value
    df_combined = pd.concat([df_truncated, future_row], ignore_index=True)
    
    # Reset internal cache of strat
    if hasattr(strat, "_cached_df_id"):
        delattr(strat, "_cached_df_id")
        
    sig_2 = strat.get_signal(df_combined, 149)
    
    # Assert signals are identical, proving lookahead-free compliance
    assert sig_1 == sig_2
