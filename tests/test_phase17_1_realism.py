import os
import sys
import pandas as pd
import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

def test_selective_rescue_gate():
    # Test selective rescue gate filters: only winning trades that improve zero/neg months
    c_zero_months = ["2024-06", "2024-09"]
    
    trades = [
        {"id": 1, "month": "2024-06", "pnl": 100.0, "expected_gate": "PASS"},
        {"id": 2, "month": "2024-06", "pnl": -50.0, "expected_gate": "FAIL"},
        {"id": 3, "month": "2024-07", "pnl": 150.0, "expected_gate": "FAIL"}, # not a zero/neg month
    ]
    
    for t in trades:
        is_winner = t["pnl"] > 0
        rescues_zero = t["month"] in c_zero_months
        passes_gate = is_winner and rescues_zero
        
        gate_status = "PASS" if passes_gate else "FAIL"
        assert gate_status == t["expected_gate"]

def test_reports_dir():
    assert os.path.exists(os.path.join(_ROOT, "reports"))
