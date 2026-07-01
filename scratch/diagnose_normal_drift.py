import os
import sys
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.research.phase12_runner import build_p10_1_strategy

def main():
    df = pd.read_csv("data/processed/BTCUSDT_1h_processed.csv")
    df = add_indicators(df)
    strat = build_p10_1_strategy()
    
    settings = {
        "initial_capital": 10000.0,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slippage": 0.0005,
        "max_positions": 1,
        "cooldown_candles": 5
    }
    risk = {
        "risk_limit_pct": 1.0,
        "monthly_risk_limit": 0.025,
        "risk_throttle_mode": "no_throttle",
        "emergency_pause_threshold": 0.025
    }

    # Run 1: Floor
    engine1 = MultiPositionBacktestEngine(**settings)
    res1 = engine1.run(df, strat, risk)
    pnl1 = res1["metrics"]["net_pnl"]
    trades1 = res1["trades"]

    # Run 2: Normal Stress (same config and engine settings)
    engine2 = MultiPositionBacktestEngine(**settings)
    res2 = engine2.run(df, strat, risk.copy())
    pnl2 = res2["metrics"]["net_pnl"]
    trades2 = res2["trades"]

    print(f"Run 1 PnL: ${pnl1:.2f}")
    print(f"Run 2 PnL: ${pnl2:.2f}")

    if len(trades1) != len(trades2):
        print(f"Trade count mismatch: Run 1={len(trades1)}, Run 2={len(trades2)}")
    else:
        diff_count = 0
        for i in range(len(trades1)):
            t1 = trades1.iloc[i]
            t2 = trades2.iloc[i]
            if abs(t1["net_pnl"] - t2["net_pnl"]) > 1e-4 or t1["entry_time"] != t2["entry_time"]:
                print(f"Trade {i} mismatch:")
                print(f"  Run 1: time={t1['entry_time']}, side={t1['side']}, pnl={t1['net_pnl']:.4f}")
                print(f"  Run 2: time={t2['entry_time']}, side={t2['side']}, pnl={t2['net_pnl']:.4f}")
                diff_count += 1
                if diff_count >= 5:
                    break

if __name__ == "__main__":
    main()
