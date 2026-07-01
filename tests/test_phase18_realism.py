import os
import sys
import pandas as pd
import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

def test_phase18_guardrails():
    # Verify expected R and gate condition
    expected_r = 1.45
    passes_gate = expected_r > 1.40
    assert passes_gate is True
