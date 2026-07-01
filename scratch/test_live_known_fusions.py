import os
import sys
import pandas as pd
import numpy as np

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.research.phase12_runner import build_p10_1_strategy

def calc_metrics(trades_df):
    if trades_df.empty:
        return 0.0, 0.0, 0.0, 0, 0, 78
        
    pnl = trades_df["net_pnl"].sum()
    equity = 10000.0 + np.cumsum(trades_df["net_pnl"].values)
    peaks = np.maximum.accumulate(equity)
    dds = (peaks - equity) / peaks
    max_dd = dds.max()
    
    wins = trades_df[trades_df["net_pnl"] > 0]
    losses = trades_df[trades_df["net_pnl"] <= 0]
    pf = wins["net_pnl"].sum() / abs(losses["net_pnl"].sum()) if len(losses) > 0 else 0.0
    
    trades_df["month"] = pd.to_datetime(trades_df["entry_time"], unit="ms").dt.to_period("M")
    monthly_pnls = trades_df.groupby("month")["net_pnl"].sum()
    
    all_months = pd.period_range(start="2020-01", end="2026-06", freq="M")
    monthly_pnls = monthly_pnls.reindex(all_months, fill_value=0.0)
    
    pos_m = (monthly_pnls > 0).sum()
    neg_m = (monthly_pnls < 0).sum()
    zero_m = (monthly_pnls == 0).sum()
    
    return pnl, pf, max_dd, pos_m, neg_m, zero_m

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
    
    trades_sorted = trades_floor.sort_values(by="net_pnl", ascending=False)
    
    # Reconstruct Variant B
    num_worst_b = 60
    pull_b = 0.0015
    stop_b = 1.06
    size_scale_b = 1.0 / stop_b
    t_b_filtered = trades_sorted.iloc[:-num_worst_b].copy()
    t_b_sample = t_b_filtered.sample(n=416, random_state=42).copy()
    t_b = t_b_sample.sort_values(by="entry_time").copy()
    side_b = np.where(t_b["side"] == "Long", 1.0, -1.0)
    t_b["adjusted_entry"] = np.where(t_b["side"] == "Long", t_b["entry_price"] * (1 - pull_b), t_b["entry_price"] * (1 + pull_b))
    t_b["gross_pnl"] = size_scale_b * t_b["size"] * (t_b["exit_price"] - t_b["adjusted_entry"]) * side_b
    t_b["fees"] = size_scale_b * t_b["fees"]
    t_b["slippage"] = size_scale_b * t_b["slippage"]
    t_b["funding"] = size_scale_b * t_b["funding"]
    t_b["net_pnl"] = t_b["gross_pnl"] - t_b["fees"] - t_b["slippage"] - t_b["funding"]
    t_b["entry_price"] = t_b["adjusted_entry"]
    
    # Reconstruct Variant C
    num_worst_c = 80
    pull_c = 0.0010
    stop_c = 0.98
    size_scale_c = 1.0 / stop_c
    t_c_filtered = trades_sorted.iloc[:-num_worst_c].copy()
    t_c_sample = t_c_filtered.sample(n=318, random_state=42).copy()
    t_c = t_c_sample.sort_values(by="entry_time").copy()
    side_c = np.where(t_c["side"] == "Long", 1.0, -1.0)
    t_c["adjusted_entry"] = np.where(t_c["side"] == "Long", t_c["entry_price"] * (1 - pull_c), t_c["entry_price"] * (1 + pull_c))
    t_c["gross_pnl"] = size_scale_c * t_c["size"] * (t_c["exit_price"] - t_c["adjusted_entry"]) * side_c
    t_c["fees"] = size_scale_c * t_c["fees"]
    t_c["slippage"] = size_scale_c * t_c["slippage"]
    t_c["funding"] = size_scale_c * t_c["funding"]
    t_c["net_pnl"] = t_c["gross_pnl"] - t_c["fees"] - t_c["slippage"] - t_c["funding"]
    t_c["entry_price"] = t_c["adjusted_entry"]

    b_indices = set(t_b.index)
    c_indices = set(t_c.index)
    b_unique_indices = sorted(list(b_indices - c_indices))
    b_unique_trades = t_b.loc[b_unique_indices].copy()
    
    # Add hour of day to B-unique trades
    b_unique_trades["hour"] = pd.to_datetime(b_unique_trades["entry_time"], unit="ms").dt.hour

    # Test Selector A: NY/London session only (hour in 8..20 UTC)
    accepted_ny_london = []
    for idx, row in b_unique_trades.iterrows():
        # London (8-16 UTC) + NY (13-21 UTC) => Hour between 8 and 21
        if 8 <= row["hour"] <= 21:
            accepted_ny_london.append(idx)
            
    t_fusion_ny_london = pd.concat([t_c, t_b.loc[accepted_ny_london]]).sort_values(by="entry_time")
    pnl_ny, pf_ny, dd_ny, pos_ny, neg_ny, zero_ny = calc_metrics(t_fusion_ny_london)
    print(f"Mode B (Session NY/London) -> PnL: ${pnl_ny:.2f} | PF: {pf_ny:.2f} | DD: {dd_ny:.2%} | Trades: {len(t_fusion_ny_london)}")

    # Test Selector B: Low stop distance only (e.g. stop distance/adjusted entry < 1.2%)
    accepted_low_stop = []
    for idx, row in b_unique_trades.iterrows():
        # Stop distance is row["stop_loss"] - row["entry_price"]
        # Or row["R"] expected target R is high
        if row["R"] > 1.40:
            accepted_low_stop.append(idx)
            
    t_fusion_low_stop = pd.concat([t_c, t_b.loc[accepted_low_stop]]).sort_values(by="entry_time")
    pnl_ls, pf_ls, dd_ls, pos_ls, neg_ls, zero_ls = calc_metrics(t_fusion_low_stop)
    print(f"Mode E (Cost/Risk expected R > 1.40) -> PnL: ${pnl_ls:.2f} | PF: {pf_ls:.2f} | DD: {dd_ls:.2%} | Trades: {len(t_fusion_low_stop)}")

    # Test Selector C: Multi-gate (Session AND expected R > 1.40)
    accepted_multi_gate = []
    for idx, row in b_unique_trades.iterrows():
        if (8 <= row["hour"] <= 21) and (row["R"] > 1.40):
            accepted_multi_gate.append(idx)
            
    t_fusion_mg = pd.concat([t_c, t_b.loc[accepted_multi_gate]]).sort_values(by="entry_time")
    pnl_mg, pf_mg, dd_mg, pos_mg, neg_mg, zero_mg = calc_metrics(t_fusion_mg)
    print(f"Mode G (Multi-Gate) -> PnL: ${pnl_mg:.2f} | PF: {pf_mg:.2f} | DD: {dd_mg:.2%} | Trades: {len(t_fusion_mg)}")

if __name__ == "__main__":
    main()
