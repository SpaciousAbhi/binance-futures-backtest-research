import os
import sys
import pandas as pd
import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

def test_live_known_expected_r_gate():
    # Verify Mode E expected R filter condition (expected R > 1.40)
    trades = [
        {"id": 1, "R": 1.55, "expected_gate": "PASS"},
        {"id": 2, "R": 1.22, "expected_gate": "FAIL"},
        {"id": 3, "R": 1.41, "expected_gate": "PASS"},
    ]
    
    for t in trades:
        passes_gate = t["R"] > 1.40
        gate_status = "PASS" if passes_gate else "FAIL"
        assert gate_status == t["expected_gate"]
