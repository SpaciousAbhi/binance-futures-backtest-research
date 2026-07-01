import os
import sys
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.research.phase12_runner import build_p10_1_strategy, run_stress_test

def main():
    df = pd.read_csv("data/processed/BTCUSDT_1h_processed.csv")
    df = add_indicators(df)
    strat = build_p10_1_strategy()
    
    settings = {
        'initial_capital': 10000.0,
        'maker_fee': 0.0002,
        'taker_fee': 0.0005,
        'slippage': 0.0005,
        'max_positions': 1,
        'cooldown_candles': 5
    }
    
    risk = {
        'risk_limit_pct': 1.0,
        'monthly_risk_limit': 0.025,
        'risk_throttle_mode': 'no_throttle',
        'emergency_pause_threshold': 0.025
    }
    
    for w in [1, 2, 3]:
        cfg = risk.copy()
        cfg.update({
            "execution_mode": "hybrid",
            "atr_pct_limit": 0.50,
            "max_wait_candles": w,
            "fallback_to_market": True,
            "queue_prob": 0.30,
            "partial_fill_prob": 0.20,
            "partial_fill_factor": 0.50
        })
        res = MultiPositionBacktestEngine(**settings).run(df, strat, cfg)
        pnl = res["metrics"]["net_pnl"]
        
        # Combined adverse stress
        stress_cfg = cfg.copy()
        stress_cfg.update({"fee_mult": 2.0, "slip_mult": 2.0, "delay_candles": 1})
        res_s = MultiPositionBacktestEngine(**settings).run(df, strat, stress_cfg)
        s_pnl = res_s["metrics"]["net_pnl"]
        
        print(f"Wait={w} | PnL=${pnl:.2f} | Combined Adverse PnL=${s_pnl:.2f}")

if __name__ == "__main__":
    main()
