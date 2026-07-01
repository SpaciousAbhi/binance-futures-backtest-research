import sys, os
sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

# Load 1h data
df = pd.read_csv('data/processed/BTCUSDT_1h_processed.csv')
df = add_indicators(df)

# Define candidates (same optimized ones)
cfg_c = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 100, "rsi_oversold": 0,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}
cfg_f = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "atr_volatility_expansion",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 3.0, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}
cfg_g = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "funding_extreme_reversal",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.0, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}
cfg_d = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "low_activity_filler",
    "trend_filter": "ema_200",
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 3.5, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 25,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}

s_c = UniversalStrategyTemplate(cfg_c)
s_f = UniversalStrategyTemplate(cfg_f)
s_g = UniversalStrategyTemplate(cfg_g)
s_d = UniversalStrategyTemplate(cfg_d)

port_3 = PortfolioStrategy([s_c, s_f, s_g], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=False)
port_4 = PortfolioStrategy([s_c, s_f, s_g, s_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)

# Parameter sweeps
throttle_options = ["no_throttle", "soft", "medium", "hard", "emergency_pause"]
ep_options = [0.02, 0.025, 0.03, 0.04]
max_pos_options = [1, 2, 3]

results = []

for port_name, port_obj in [("C+F+G", port_3), ("C+F+G+D", port_4)]:
    for max_pos in max_pos_options:
        for throttle in throttle_options:
            for ep in ep_options:
                multi_engine = MultiPositionBacktestEngine(
                    initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005,
                    max_positions=max_pos, cooldown_candles=5
                )
                cfg_run = {
                    "monthly_risk_limit": 0.025,
                    "risk_limit_pct": 1.0,
                    "risk_throttle_mode": throttle,
                    "emergency_pause_threshold": ep
                }
                res = multi_engine.run(df, port_obj, cfg_run)
                m = res["metrics"]
                
                # Sizing penalty for low trade counts or negative months
                neg_penalty = m["negative_months"] * 500.0
                zero_penalty = m["zero_months"] * 300.0
                trade_penalty = 0.0
                if m["total_trades"] < 500:
                    trade_penalty = (500 - m["total_trades"]) * 10.0
                score = m["net_pnl"] - neg_penalty - zero_penalty - trade_penalty - m["max_drawdown"] * 1000.0
                
                results.append({
                    "port": port_name,
                    "max_pos": max_pos,
                    "throttle": throttle,
                    "ep": ep,
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
                
# Sort by score
results.sort(key=lambda x: x["score"], reverse=True)

print("Top 15 Portfolio configurations:")
for r in results[:15]:
    print(f"Port={r['port']} Pos={r['max_pos']} Throttle={r['throttle']:<15} EP={r['ep']:.3f} | PnL=${r['pnl']:>8.2f} trades={r['trades']:>4} PF={r['pf']:.2f} DD={r['dd']:.2%} +/-/0={r['pos']}/{r['neg']}/{r['zero']} Score={r['score']:.2f}")

# Save to markdown table
md = []
md.append("# Portfolio Optimization Results")
md.append("\n| Portfolio | Max Pos | Throttle Mode | EP Threshold | Net PnL ($) | Total Trades | Win Rate | Profit Factor | Max DD | +/-/0 Months | Score |")
md.append("|---|---|---|---|---|---|---|---|---|---|---|")
for r in results[:20]:
    md.append(f"| {r['port']} | {r['max_pos']} | {r['throttle']} | {r['ep']:.3f} | {r['pnl']:.2f} | {r['trades']} | {r['win_rate']:.2%} | {r['pf']:.2f} | {r['dd']:.2%} | {r['pos']}/{r['neg']}/{r['zero']} | {r['score']:.2f} |")

with open("scratch/portfolio_optimization_results.md", "w") as f:
    f.write("\n".join(md))
print("Saved portfolio results to scratch/portfolio_optimization_results.md")
