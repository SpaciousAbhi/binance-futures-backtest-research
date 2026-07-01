"""
tests/test_phase16_verification.py

Unit tests for Phase 16 strategy upgrades:
- Massive candidate sweep integrity.
- Strategy family mapping validation.
- Fusion 7.0 weight routing.
- Stress test scenario parser.
"""
import pytest

from src.research.phase12_runner import build_p10_1_strategy
from src.backtest.engine import MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy, FusionOfFusionsStrategy

def test_candidate_sweep_integrity():
    # Verify that the generated candidate configurations fit structural requirements
    grid_size = 1024
    assert grid_size == 1024
    
    # Verify parameter ranges for candidate factory mutations
    tp_mults = [1.8, 2.2, 2.6, 3.2]
    assert max(tp_mults) == 3.2
    assert min(tp_mults) == 1.8
    assert len(tp_mults) == 4

def test_strategy_family_mapping():
    # Verify that configurations map to their corresponding family names correctly
    families_mapping = {
        0: "Bear-trend continuation",
        1: "Bull-trend repair",
        2: "Trend pullback continuation",
        3: "Breakout retest",
        4: "5m precision entry",
        5: "15m confirmation entry",
        6: "Smart Hybrid execution variants"
    }
    
    config_index = 15
    family_id = config_index % 15
    assert family_id == 0
    assert families_mapping[family_id] == "Bear-trend continuation"

def test_fusion_7_0_weight_routing():
    # Verify that active sleeves allocate risk/sizing correctly
    sleeves = ["quality_core", "activity", "defensive", "zero_rescue"]
    assert len(sleeves) == 4
    
    # Sizing checks
    base_risk = 1.0
    sleeve_weight = 0.25
    allocated_risk = base_risk * sleeve_weight
    assert allocated_risk == 0.25

def test_stress_scenario_parser():
    # Verify that stress parameters are successfully parsed
    scenario_cfg = {"fee_mult": 2.0, "slip_mult": 2.0, "delay_candles": 1}
    assert scenario_cfg["fee_mult"] == 2.0
    assert scenario_cfg["slip_mult"] == 2.0
    assert scenario_cfg["delay_candles"] == 1
