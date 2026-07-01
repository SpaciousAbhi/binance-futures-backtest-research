import pytest
import numpy as np
import pandas as pd
from src.backtest.engine import MultiPositionBacktestEngine
from src.features.indicators import add_indicators

@pytest.fixture
def base_mock_data():
    """Generates a small mock dataframe for stress testing."""
    open_times = [1577836800000 + i * 15 * 60 * 1000 for i in range(100)] # 15m candles
    prices = [10000.0]
    for i in range(99):
        # Create a steady upward trend for clear results
        prices.append(prices[-1] * 1.001)
        
    df = pd.DataFrame({
        "open_time": open_times,
        "open": prices,
        "high": [p * 1.002 for p in prices],
        "low": [p * 0.998 for p in prices],
        "close": prices,
        "volume": [100.0] * 100,
        "fundingRate": [0.0] * 100
    })
    return add_indicators(df)

class MockSingleSignalStrategy:
    """Strategy that triggers exactly one Long signal at index 10."""
    name = "MockSingleSignal"
    hypothesis = "Signal at 10"
    def get_signal(self, df, i):
        if i == 10:
            return {
                "side": "Long",
                "stop_loss": df.loc[i, "close"] - 200,
                "take_profit": df.loc[i, "close"] + 500,
                "reason": "Signal at 10",
                "strategy_name": "MockSingleSignal"
            }
        return None

def test_multi_engine_delay_candles(base_mock_data):
    """Verifies that delay_candles shifts the entry index and entry price."""
    engine = MultiPositionBacktestEngine(slippage=0.0)
    strat = MockSingleSignalStrategy()
    
    # 1. Normal execution (delay_candles=0 -> executed at index 11 open)
    res_normal = engine.run(base_mock_data, strat, config={"delay_candles": 0})
    trades_normal = res_normal["trades"]
    assert len(trades_normal) == 1
    t_normal = trades_normal.iloc[0]
    assert t_normal["entry_time"] == base_mock_data.loc[11, "open_time"]
    assert abs(t_normal["entry_price"] - round(base_mock_data.loc[11, "open"], 1)) < 1e-3
    
    # 2. Delayed execution (delay_candles=2 -> executed at index 13 open)
    res_delayed = engine.run(base_mock_data, strat, config={"delay_candles": 2})
    trades_delayed = res_delayed["trades"]
    assert len(trades_delayed) == 1
    t_delayed = trades_delayed.iloc[0]
    assert t_delayed["entry_time"] == base_mock_data.loc[13, "open_time"]
    assert abs(t_delayed["entry_price"] - round(base_mock_data.loc[13, "open"], 1)) < 1e-3

def test_multi_engine_missed_fills(base_mock_data):
    """Verifies that missed_fill_pct probabilistically removes trades with a seed."""
    engine = MultiPositionBacktestEngine(slippage=0.0)
    strat = MockSingleSignalStrategy()
    
    # Run with 100% missed fill rate -> should have 0 trades
    res = engine.run(base_mock_data, strat, config={"missed_fill_pct": 1.0})
    assert len(res["trades"]) == 0
    
    # Run with 0% missed fill rate -> should have 1 trade
    res_fill = engine.run(base_mock_data, strat, config={"missed_fill_pct": 0.0})
    assert len(res_fill["trades"]) == 1

def test_multi_engine_stale_skip(base_mock_data):
    """Verifies that stale_skip rejects orders when the delay in minutes exceeds stale_limit_minutes."""
    engine = MultiPositionBacktestEngine(slippage=0.0)
    strat = MockSingleSignalStrategy()
    
    # Setup delay_candles = 2 (which is 30 minutes on a 15m timeframe).
    # If stale_limit_minutes = 15, then 30 > 15 -> order should be skipped!
    res_stale = engine.run(base_mock_data, strat, config={
        "delay_candles": 2,
        "stale_skip": True,
        "stale_limit_minutes": 15
    })
    assert len(res_stale["trades"]) == 0
    
    # If stale_limit_minutes = 45, then 30 < 45 -> order should be filled!
    res_not_stale = engine.run(base_mock_data, strat, config={
        "delay_candles": 2,
        "stale_skip": True,
        "stale_limit_minutes": 45
    })
    assert len(res_not_stale["trades"]) == 1

def test_multi_engine_cost_multipliers(base_mock_data):
    """Verifies that fee_mult and slip_mult actually increase trading costs and reduce net PnL."""
    engine = MultiPositionBacktestEngine(taker_fee=0.001, slippage=0.001)
    strat = MockSingleSignalStrategy()
    
    # Normal run
    res_normal = engine.run(base_mock_data, strat, config={"fee_mult": 1.0, "slip_mult": 1.0})
    metrics_normal = res_normal["metrics"]
    
    # Double fees and slippage
    res_stress = engine.run(base_mock_data, strat, config={"fee_mult": 2.0, "slip_mult": 2.0})
    metrics_stress = res_stress["metrics"]
    
    # Check that costs are higher and Net PnL is lower
    assert metrics_stress["fees"] > metrics_normal["fees"]
    assert metrics_stress["slippage"] > metrics_normal["slippage"]
    assert metrics_stress["net_pnl"] < metrics_normal["net_pnl"]
    
    # Check separate entry and exit slippage recording
    assert "entry_slippage" in metrics_stress
    assert "exit_slippage" in metrics_stress
    assert metrics_stress["entry_slippage"] > 0
    assert metrics_stress["exit_slippage"] > 0

def test_combined_adverse_does_not_silently_disable_trades(base_mock_data):
    """Verifies that combined adverse does not silently disable all trades with timeframe scaling."""
    engine = MultiPositionBacktestEngine(slippage=0.0005, taker_fee=0.0005)
    strat = MockSingleSignalStrategy()
    
    # Run with combined adverse parameters
    res = engine.run(base_mock_data, strat, config={
        "fee_mult": 2.0,
        "slip_mult": 2.0,
        "delay_candles": 1,
        "missed_fill_pct": 0.0,
        "stale_skip": True,
        "stale_limit_minutes": 15
    })
    
    assert len(res["trades"]) == 1
    t = res["trades"].iloc[0]
    assert t["entry_price"] > 0

def test_parameter_sensitivity_wiring_bb_width():
    """Verifies that varying bb_width_thresh changes Bollinger Expansion signal/trade generation."""
    from src.strategies.candidates import UniversalStrategyTemplate
    
    # Create 250 rows of data so i >= 200 warm-up limit is satisfied
    open_times = [1577836800000 + i * 15 * 60 * 1000 for i in range(250)]
    prices = [10000.0]
    for i in range(249):
        # We want to create a sudden breakout at index 210 to trigger BB Expansion
        if i == 210:
            prices.append(prices[-1] * 1.10) # 10% jump!
        else:
            prices.append(prices[-1] * 1.0001)
            
    df = pd.DataFrame({
        "open_time": open_times,
        "open": prices,
        "high": [p * 1.001 for p in prices],
        "low": [p * 0.999 for p in prices],
        "close": prices,
        "volume": [100.0] * 250,
        "fundingRate": [0.0] * 250
    })
    # Add indicators
    df = add_indicators(df)
    
    # Strat 1: Narrow width threshold (0.01) -> should trigger breakout trades
    strat_narrow = UniversalStrategyTemplate({
        "template_type": "bollinger_expansion_breakout",
        "bb_width_thresh": 0.01,
        "trend_filter": None,
        "regime_filter_mode": "no_filter"
    })
    
    # Strat 2: Wide width threshold (0.25) -> should trigger zero trades
    strat_wide = UniversalStrategyTemplate({
        "template_type": "bollinger_expansion_breakout",
        "bb_width_thresh": 0.25,
        "trend_filter": None,
        "regime_filter_mode": "no_filter"
    })
    
    engine = MultiPositionBacktestEngine(slippage=0.0)
    res_narrow = engine.run(df, strat_narrow)
    res_wide = engine.run(df, strat_wide)
    
    n_trades = res_narrow["metrics"]["total_trades"]
    w_trades = res_wide["metrics"]["total_trades"]
    
    assert n_trades > w_trades, f"Parameter sensitivity check failed: narrow={n_trades} wide={w_trades}"

def test_idea_engine_count_and_lifecycle_separation():
    """Verifies that ResearchIdeaEngine counts generated, tested, and failure months separately."""
    import os
    import json
    from src.research.idea_engine import ResearchIdeaEngine, ResearchIdea
    
    engine = ResearchIdeaEngine()
    
    # Add one generated idea
    engine.add_idea(ResearchIdea(
        idea_id="TEST_1", name="Test Idea 1", hypothesis="H1", failure_category="chop",
        expected_benefit="B1", affected_months=["2024-01"], live_compatible=True,
        lookahead_risk="NONE", implementation_plan="P1", acceptance_metrics={},
        rejection_criteria={}, required_data=[], status="GENERATED"
    ))
    
    # Add one tested/accepted idea
    engine.add_idea(ResearchIdea(
        idea_id="TEST_2", name="Test Idea 2", hypothesis="H2", failure_category="false_breakout",
        expected_benefit="B2", affected_months=["2024-01", "2024-02"], live_compatible=True,
        lookahead_risk="NONE", implementation_plan="P2", acceptance_metrics={},
        rejection_criteria={}, required_data=[], status="ACCEPTED"
    ))
    
    # Add one Phase 12 deferred idea
    engine.add_idea(ResearchIdea(
        idea_id="TEST_3", name="Test Idea 3", hypothesis="H3", failure_category="low_activity",
        expected_benefit="B3", affected_months=["2023-07"], live_compatible=True,
        lookahead_risk="NONE", implementation_plan="P3", acceptance_metrics={},
        rejection_criteria={}, required_data=[], status="DEFERRED_TO_PHASE_12"
    ))
    
    # Export to dict via save_ideas_json mock logic
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "ideas.json")
        engine.save_ideas_json(json_path)
        
        with open(json_path) as f:
            data = json.load(f)
            
        assert data["total_ideas_count"] == 3
        assert data["generated_ideas_count"] == 1
        assert data["tested_ideas_count"] == 1
        assert data["deferred_ideas_count"] == 1
        assert data["failure_month_count"] == 3 # 2024-01, 2024-02, 2023-07 are unique
        assert data["lifecycle_status_counts"]["GENERATED"] == 1
        assert data["lifecycle_status_counts"]["ACCEPTED"] == 1
        assert data["lifecycle_status_counts"]["DEFERRED_TO_PHASE_12"] == 1


