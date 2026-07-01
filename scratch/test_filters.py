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

def score_filters(m):
    neg_penalty = m["negative_months"] * 500.0
    zero_penalty = m["zero_months"] * 300.0
    dd_penalty = m["max_drawdown"] * 1000.0
    # Penalty for too few trades
    trade_penalty = 0.0
    if m["total_trades"] < 250:
        trade_penalty = (250 - m["total_trades"]) * 20.0
    return m["net_pnl"] - neg_penalty - zero_penalty - dd_penalty - trade_penalty

adx_options = [0, 10, 15, 20, 25]
rsi_options = [(100, 0), (80, 20), (75, 25), (70, 30)]
cost_options = [0.0, 3.0, 4.0, 5.0]

results = []
for adx in adx_options:
    for ob, os in rsi_options:
        for cost_mult in cost_options:
            cfg = dict(P5_BEST_CFG)
            cfg["adx_thresh"] = adx
            cfg["rsi_overbought"] = ob
            cfg["rsi_oversold"] = os
            cfg["cost_to_atr_mult"] = cost_mult
            
            s = UniversalStrategyTemplate(cfg)
            res = engine.run(df, s)
            m = res["metrics"]
            
            score = score_filters(m)
            results.append({
                "adx": adx,
                "rsi_ob": ob,
                "rsi_os": os,
                "cost_mult": cost_mult,
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

# Rank by score
results.sort(key=lambda x: x["score"], reverse=True)

print("Top 15 Filter Configurations:")
for r in results[:15]:
    print(f"ADX={r['adx']:<2} RSI={r['rsi_ob']}/{r['rsi_os']} Cost={r['cost_mult']:.1f} | PnL=${r['pnl']:>9.2f} trades={r['trades']:>4} PF={r['pf']:.2f} DD={r['dd']:.2%} +/-/0={r['pos']}/{r['neg']}/{r['zero']} Score={r['score']:.2f}")

# Save to markdown table
md = []
md.append("# BB Expansion Filter Optimization Results")
md.append("\n| ADX Thresh | RSI Overbought/Oversold | Cost-to-ATR Mult | Net PnL ($) | Total Trades | Win Rate | Profit Factor | Max DD | +/-/0 Months | Score |")
md.append("|---|---|---|---|---|---|---|---|---|---|")
for r in results[:15]:
    md.append(f"| {r['adx']} | {r['rsi_ob']}/{r['rsi_os']} | {r['cost_mult']:.1f} | {r['pnl']:.2f} | {r['trades']} | {r['win_rate']:.2%} | {r['pf']:.2f} | {r['dd']:.2%} | {r['pos']}/{r['neg']}/{r['zero']} | {r['score']:.2f} |")

with open("scratch/filter_optimization_results.md", "w") as f:
    f.write("\n".join(md))
print("Saved filter results to scratch/filter_optimization_results.md")
