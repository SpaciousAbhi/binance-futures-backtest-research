import sys, os
sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

# Load 1h data
proc = DataProcessor('data/raw', 'data/processed')
df = pd.read_csv('data/processed/BTCUSDT_1h_processed.csv')
df = add_indicators(df)

# We will run each of the 22 templates
types = [
    "trend_pullback", "trend_breakout", "breakout_retest", "failed_breakout_reversal", "sweep_reversal",
    "vwap_mean_reversion", "bollinger_mean_reversion", "bollinger_expansion_breakout", "atr_volatility_expansion",
    "range_compression_breakout", "asia_range_breakout", "asia_range_failure", "london_continuation",
    "new_york_reversal", "funding_extreme_reversal", "funding_trend_continuation", "rsi_exhaustion_reversal",
    "wick_rejection_reversal", "volume_impulse_continuation", "swing_structure_continuation", "low_activity_filler",
    "mtf_breakout"
]

engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)

results = []
for t in types:
    cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": t,
        "trend_filter": None,
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 2.5, "sl_atr_mult": 1.5,
        "rsi_overbought": 70, "rsi_oversold": 30,
        "adx_thresh": 20, "wick_ratio_thresh": 0.45
    }
    s = UniversalStrategyTemplate(cfg)
    res = engine.run(df, s)
    m = res["metrics"]
    results.append({
        "template": t,
        "pnl": m["net_pnl"],
        "trades": m["total_trades"],
        "win_rate": m["win_rate"],
        "pf": m["profit_factor"],
        "dd": m["max_drawdown"],
        "pos_m": m["positive_months"],
        "neg_m": m["negative_months"],
        "zero_m": m["zero_months"]
    })
    print(f"{t:<30} PnL=${m['net_pnl']:>9.2f} trades={m['total_trades']:>4} PF={m['profit_factor']:.2f} DD={m['max_drawdown']:.2%} +/-/0={m['positive_months']}/{m['negative_months']}/{m['zero_months']}")

# Output to CSV and manual markdown
df_res = pd.DataFrame(results)
df_res.to_csv("scratch/standalone_results.csv", index=False)

# Build markdown manually
md = []
md.append("| Strategy Template | Net PnL ($) | Total Trades | Win Rate | Profit Factor | Max DD | +/-/0 Months |")
md.append("|---|---|---|---|---|---|---|")
for r in results:
    md.append(f"| {r['template']} | {r['pnl']:.2f} | {r['trades']} | {r['win_rate']:.2%} | {r['pf']:.2f} | {r['dd']:.2%} | {r['pos_m']}/{r['neg_m']}/{r['zero_m']} |")

with open("scratch/standalone_results.md", "w") as f:
    f.write("\n".join(md))

print("Saved standalone results to CSV and markdown!")
