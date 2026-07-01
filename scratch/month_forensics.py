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
strat_c = UniversalStrategyTemplate(P5_BEST_CFG)
engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)
res_c = engine.run(df, strat_c)
met_c = res_c["metrics"]
trd_c = res_c["trades"]

# Convert trades to dataframe
df_trd = pd.DataFrame(trd_c)
df_trd["month"] = pd.to_datetime(df_trd["exit_datetime"]).dt.to_period("M").astype(str)

# Pre-extract monthly regimes
dt_series = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_localize(None)
df["month"] = dt_series.dt.to_period("M").astype(str)

regime_cols = [
    "regime_bull_trend", "regime_bear_trend", "regime_sideways_range",
    "regime_vol_compression", "regime_vol_expansion", "regime_funding_extreme",
    "regime_toxic_chop"
]

monthly_regimes = {}
for m_str, m_df in df.groupby("month"):
    counts = {}
    for r in regime_cols:
        counts[r] = m_df[r].sum() if r in m_df.columns else 0
    # Get dominant regime
    dom = max(counts, key=counts.get)
    monthly_regimes[m_str] = dom.replace("regime_", "")

# Extract negative months
neg_months = [r for r in met_c["monthly_report"] if r["net_pnl"] < 0]

md = []
md.append("# Negative Month Forensics Matrix (Candidate C)")
md.append("\n| Month | Trades | Wins | Losses | Net PnL ($) | Dominant Regime | Failure Mode | Avoidable | Proposed Fix |")
md.append("|---|---|---|---|---|---|---|---|---|")

for r in neg_months:
    m = r["month"]
    net = r["net_pnl"]
    tr_count = r["trades"]
    wins = r["wins"]
    losses = r["losses"]
    dom_r = monthly_regimes.get(m, "unknown")
    
    # Classify failure mode
    if tr_count <= 3:
        fail_mode = "Low trade count cluster"
        avoid = "Yes"
        prop_fix = "Activate Low-Activity Reversion Filler (Candidate D)"
    elif wins == 0:
        fail_mode = "False breakout cluster / Chop"
        avoid = "Yes"
        prop_fix = "Add ADX Trend Slope or Volatility Expansion Confirmation filter"
    elif r["fees"] > abs(net) * 0.5:
        fail_mode = "Cost erosion"
        avoid = "Yes"
        prop_fix = "Apply expected move Cost-to-ATR ratio threshold (> 5x costs)"
    else:
        fail_mode = "Trend Reversal / Chop"
        avoid = "No"
        prop_fix = "Dynamic trailing stops or breakeven updates"
        
    md.append(f"| {m} | {tr_count} | {wins} | {losses} | {net:.2f} | {dom_r} | {fail_mode} | {avoid} | {prop_fix} |")

# Also list zero months
zero_months = [r for r in met_c["monthly_report"] if r["net_pnl"] == 0]
md.append("\n## Zero Month Forensics Matrix (Candidate C)")
md.append("\n| Month | Trades | Dominant Regime | Failure Cause | Avoidable | Proposed Fix |")
md.append("|---|---|---|---|---|---|")
for r in zero_months:
    m = r["month"]
    dom_r = monthly_regimes.get(m, "unknown")
    md.append(f"| {m} | 0 | {dom_r} | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |")

with open("scratch/forensics_matrix.md", "w") as f:
    f.write("\n".join(md))
print("Saved forensics matrix to scratch/forensics_matrix.md")
