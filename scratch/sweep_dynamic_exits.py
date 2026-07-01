import sys, os
sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate

# Load 1h data
df = pd.read_csv('data/processed/BTCUSDT_1h_processed.csv')
df = add_indicators(df)

P5_BEST_CFG = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}

engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)

def score_exit(m):
    neg_penalty = m["negative_months"] * 500.0
    zero_penalty = m["zero_months"] * 300.0
    dd_penalty = m["max_drawdown"] * 1000.0
    return m["net_pnl"] - neg_penalty - zero_penalty - dd_penalty

trail_options = [None, 1.0, 1.5, 2.0, 2.5, 3.0]
be_options = [None, 0.5, 1.0, 1.5, 2.0]

results = []
for trail in trail_options:
    for be in be_options:
        cfg = dict(P5_BEST_CFG)
        cfg["trail_atr_mult"] = trail
        cfg["breakeven_atr_mult"] = be
        
        s = UniversalStrategyTemplate(cfg)
        res = engine.run(df, s)
        m = res["metrics"]
        
        score = score_exit(m)
        results.append({
            "trail": trail,
            "be": be,
            "pnl": m["net_pnl"],
            "trades": m["total_trades"],
            "win_rate": m["win_rate"],
            "pf": m["profit_factor"],
            "dd": m["max_drawdown"],
            "pos": m["positive_months"],
            "neg": m["negative_months"],
            "zero": m["zero_months"],
            "score": score
        })
        
        trail_str = f"{trail}" if trail else "None"
        be_str = f"{be}" if be else "None"
        print(f"Trail={trail_str:<5} BE={be_str:<5} | PnL=${m['net_pnl']:>9.2f} PF={m['profit_factor']:.2f} DD={m['max_drawdown']:.2%} +/-/0={m['positive_months']}/{m['negative_months']}/{m['zero_months']}")

# Rank by score
results.sort(key=lambda x: x["score"], reverse=True)

md = []
md.append("# Dynamic Exits Sweep Results")
md.append("\n| Trail ATR Mult | BE ATR Mult | Net PnL ($) | Total Trades | Win Rate | Profit Factor | Max DD | +/-/0 Months | Score |")
md.append("|---|---|---|---|---|---|---|---|---|")
for r in results[:15]: # Show top 15
    trail_str = f"{r['trail']}" if r["trail"] else "None"
    be_str = f"{r['be']}" if r["be"] else "None"
    md.append(f"| {trail_str} | {be_str} | {r['pnl']:.2f} | {r['trades']} | {r['win_rate']:.2%} | {r['pf']:.2f} | {r['dd']:.2%} | {r['pos']}/{r['neg']}/{r['zero']} | {r['score']:.2f} |")

with open("scratch/dynamic_exits_results.md", "w") as f:
    f.write("\n".join(md))
print("\nSaved sweep results to scratch/dynamic_exits_results.md")
