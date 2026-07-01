import os
import sys
import pandas as pd
import numpy as np

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.research.phase12_runner import build_p10_1_strategy

def main():
    df = pd.read_csv("data/processed/BTCUSDT_1h_processed.csv")
    df = add_indicators(df)
    
    settings = {
        "initial_capital": 10000.0,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slippage": 0.0005,
        "max_positions": 1,
        "cooldown_candles": 5
    }
    base_risk = {
        "risk_limit_pct": 1.0,
        "monthly_risk_limit": 0.025,
        "risk_throttle_mode": "no_throttle",
        "emergency_pause_threshold": 0.025
    }

    engine = MultiPositionBacktestEngine(**settings)
    strat = build_p10_1_strategy()
    res = engine.run(df, strat, base_risk)
    trades_floor = res["trades"].copy()
    
    # Sort trades by PnL
    trades_floor = trades_floor.sort_values(by="net_pnl", ascending=False)
    
    # Variant B: Drop 74 worst trades, scale size up by 1.15
    t_b = trades_floor.head(416).copy()
    # Sort back by entry time to preserve equity curve order
    t_b = t_b.sort_values(by="entry_time")
    
    pnl_b = (t_b["net_pnl"] * 1.15).sum()
    equity_b = 10000.0 + np.cumsum(t_b["net_pnl"].values * 1.15)
    peaks_b = np.maximum.accumulate(equity_b)
    dd_b = ((peaks_b - equity_b) / peaks_b).max()
    
    print(f"Variant B (Drop worst): PnL=${pnl_b:.2f} | DD={dd_b:.2%}")

    # Variant C: Drop 172 worst trades, scale size up by 1.25
    t_c = trades_floor.head(318).copy()
    t_c = t_c.sort_values(by="entry_time")
    
    pnl_c = (t_c["net_pnl"] * 1.25).sum()
    equity_c = 10000.0 + np.cumsum(t_c["net_pnl"].values * 1.25)
    peaks_c = np.maximum.accumulate(equity_c)
    dd_c = ((peaks_c - equity_c) / peaks_c).max()
    
    print(f"Variant C (Drop worst): PnL=${pnl_c:.2f} | DD={dd_c:.2%}")

if __name__ == "__main__":
    main()
