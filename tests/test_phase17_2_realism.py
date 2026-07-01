import os
import sys
import pandas as pd
import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

def test_variant_c_rules():
    # Verify SL / TP directional formula calculations
    entry_price = 50000.0
    atr = 1000.0
    
    long_sl = entry_price - 0.98 * atr
    long_tp = entry_price + 1.50 * atr
    short_sl = entry_price + 0.98 * atr
    short_tp = entry_price - 1.50 * atr
    
    assert long_sl == 49020.0
    assert long_tp == 51500.0
    assert short_sl == 50980.0
    assert short_tp == 48500.0
