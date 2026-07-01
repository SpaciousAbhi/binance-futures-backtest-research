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
    
    settings = {
        "initial_capital": 10000.0,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slippage": 0.0005,
        "max_positions": 1,
        "cooldown_candles": 5
    }
    
    # Smart Hybrid V3 Config
    hybrid_cfg = {
        "risk_limit_pct": 1.0,
        "monthly_risk_limit": 0.025,
        "risk_throttle_mode": "no_throttle",
        "emergency_pause_threshold": 0.025,
        "execution_mode": "hybrid",
        "atr_pct_limit": 0.80,
        "max_wait_candles": 4,
        "fallback_to_market": True,
        "queue_prob": 0.30,
        "partial_fill_prob": 0.20,
        "partial_fill_factor": 0.50,
        "seed": 42
    }

    engine = MultiPositionBacktestEngine(**settings)
    strat = build_p10_1_strategy()
    res = engine.run(df, strat, hybrid_cfg)
    m = res["metrics"]
    trades = res["trades"]

    print("--- Smart Hybrid V3 Actual Metrics ---")
    print(f"PnL: ${m['net_pnl']:.2f}")
    print(f"Trades: {m['total_trades']}")
    print(f"Profit Factor: {m['profit_factor']:.2f}")
    print(f"Max Drawdown: {m['max_drawdown']:.2%}")
    print(f"Positive/Negative/Zero Months: {m['positive_months']} / {m['negative_months']} / {m['zero_months']}")

    # Maker/Taker stats
    maker = len(trades[trades["is_limit"] == True])
    taker = len(trades[trades["is_limit"] == False])
    partial = len(trades[trades["is_partial_fill"] == True])
    fallback = len(trades[trades["is_fallback_market"] == True])
    adverse = len(trades[trades["is_adverse_selection"] == True])

    print("\n--- Fills Distribution ---")
    print(f"Maker Fills: {maker}")
    print(f"Taker Fills: {taker}")
    print(f"Partial Fills: {partial}")
    print(f"Fallback Market Fills: {fallback}")
    print(f"Adverse Selection Fills: {adverse}")

if __name__ == "__main__":
    main()
