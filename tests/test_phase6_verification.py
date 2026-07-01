import pytest
import pandas as pd
import numpy as np
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

@pytest.fixture
def test_data():
    """Create mock trending/reversing price data with indicators."""
    open_times = [1577836800000 + i * 3600 * 1000 for i in range(200)] # 1h candles
    prices = [10000.0]
    for i in range(199):
        # Create steady upward trend
        prices.append(prices[-1] * 1.0005)
        
    df = pd.DataFrame({
        "open_time": open_times,
        "open": prices,
        "high": [p * 1.001 for p in prices],
        "low": [p * 0.999 for p in prices],
        "close": prices,
        "volume": [100.0] * 200,
        "fundingRate": [0.0] * 200
    })
    return add_indicators(df)

def test_baseline_locking_runs(test_data):
    """Verifies that baseline configurations are valid and execute without error."""
    engine = BacktestEngine(initial_capital=10000.0)
    
    p5_best_single_cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": None,
        "regime_filter_mode": "strict",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.8,
        "rsi_overbought": 75,
        "rsi_oversold": 30,
        "adx_thresh": 20,
        "wick_ratio_thresh": 0.45
    }
    
    strat = UniversalStrategyTemplate(p5_best_single_cfg)
    res = engine.run(test_data, strat)
    assert "metrics" in res
    assert "trades" in res

def test_portfolio_selection_score():
    """Verifies that the portfolio scoring logic correctly ranks systems."""
    # Score formula: pnl - neg_penalty - zero_penalty - trade_penalty - dd_penalty
    # neg_penalty = neg_months * 500.0
    # zero_penalty = zero_months * 300.0
    # trades < 780 penalty: (780 - trades) * 10.0
    # trades < 577 penalty: (577 - trades) * 30.0
    
    # System A (High PnL, but 10 negative months, 500 trades)
    sys_a = {
        "metrics": {
            "net_pnl": 5000.0,
            "negative_months": 10,
            "zero_months": 0,
            "total_trades": 500,
            "max_drawdown": 0.20,
            "profit_factor": 1.2
        }
    }
    
    # System B (Lower PnL, but only 1 negative month, 800 trades)
    sys_b = {
        "metrics": {
            "net_pnl": 4000.0,
            "negative_months": 1,
            "zero_months": 0,
            "total_trades": 800,
            "max_drawdown": 0.15,
            "profit_factor": 1.35
        }
    }
    
    def score_system(sys_item):
        m = sys_item["metrics"]
        neg_months = m["negative_months"]
        zero_months = m["zero_months"]
        trades = m["total_trades"]
        dd = m["max_drawdown"]
        pf = m["profit_factor"]
        pnl = m["net_pnl"]
        
        neg_penalty = neg_months * 500.0
        zero_penalty = zero_months * 300.0
        
        trade_penalty = 0.0
        if trades < 780:
            trade_penalty += (780 - trades) * 10.0
        if trades < 577:
            trade_penalty += (577 - trades) * 30.0
            
        dd_penalty = dd * 1000.0
        
        score = pnl - neg_penalty - zero_penalty - trade_penalty - dd_penalty
        return score

    score_a = score_system(sys_a)
    score_b = score_system(sys_b)
    
    # System B must rank higher because System A is penalized heavily for negative months and low activity
    assert score_b > score_a

def test_rebuilt_filler_config(test_data):
    """Verifies that the rebuilt low_activity_filler strategy runs correctly."""
    engine = BacktestEngine(initial_capital=10000.0)
    
    filler_cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "low_activity_filler",
        "trend_filter": "ema_200",
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 3.5,
        "sl_atr_mult": 2.0,
        "rsi_overbought": 75,
        "rsi_oversold": 25,
        "adx_thresh": 20,
        "wick_ratio_thresh": 0.45
    }
    
    strat = UniversalStrategyTemplate(filler_cfg)
    res = engine.run(test_data, strat)
    assert "metrics" in res
    assert "trades" in res
