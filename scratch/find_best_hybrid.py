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
    
    strat = build_p10_1_strategy()
    engine = MultiPositionBacktestEngine(**settings)

    results = []
    for atr_pct in [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]:
        for wait in [1, 2, 3, 4]:
            hybrid_cfg = {
                "risk_limit_pct": 1.0,
                "monthly_risk_limit": 0.025,
                "risk_throttle_mode": "no_throttle",
                "emergency_pause_threshold": 0.025,
                "execution_mode": "hybrid",
                "atr_pct_limit": atr_pct,
                "max_wait_candles": wait,
                "fallback_to_market": True,
                "queue_prob": 0.30,
                "partial_fill_prob": 0.20,
                "partial_fill_factor": 0.50,
                "seed": 42
            }
            res = engine.run(df, strat, hybrid_cfg)
            m = res["metrics"]
            trades = res["trades"]
            
            maker = len(trades[trades["is_limit"] == True])
            taker = len(trades[trades["is_limit"] == False])
            
            results.append({
                "atr_pct": atr_pct,
                "wait": wait,
                "pnl": m["net_pnl"],
                "pf": m["profit_factor"],
                "dd": m["max_drawdown"],
                "trades": m["total_trades"],
                "maker": maker,
                "taker": taker
            })
            print(f"atr={atr_pct:.2f} wait={wait} | PnL=${m['net_pnl']:.2f} PF={m['profit_factor']:.2f} DD={m['max_drawdown']:.2%} Trades={m['total_trades']}")

    df_res = pd.DataFrame(results)
    df_res.to_csv("reports/hybrid_sweep_results.csv", index=False)
    print("\nBest by PnL:")
    print(df_res.sort_values(by="pnl", ascending=False).head(5))

if __name__ == "__main__":
    main()
