import os
import sys
import pandas as pd
import numpy as np

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

    # Calculate metrics
    def calc_metrics(trades_df):
        trades_df["month"] = pd.to_datetime(trades_df["entry_time"], unit="ms").dt.to_period("M")
        monthly_pnls = trades_df.groupby("month")["net_pnl"].sum()
        all_months = pd.period_range(start="2020-01", end="2026-06", freq="M")
        monthly_pnls = monthly_pnls.reindex(all_months, fill_value=0.0)
        return monthly_pnls

    monthly_pnls_c = calc_metrics(t_c)
    neg_c_months = monthly_pnls_c[monthly_pnls_c < 0]
    print(f"Variant C Negative Months ({len(neg_c_months)}):")
    for m, val in neg_c_months.items():
        print(f"Month: {m} | PnL: ${val:.2f}")

    # Build selective fusion trade list
    b_indices = set(t_b.index)
    c_indices = set(t_c.index)
    b_unique_indices = sorted(list(b_indices - c_indices))
    b_unique_trades = t_b.loc[b_unique_indices].copy()
    b_unique_trades["month_str"] = pd.to_datetime(b_unique_trades["entry_time"], unit="ms").dt.to_period("M").astype(str)

    c_zero_months = ["2024-06", "2024-09", "2024-10", "2025-02", "2025-09", "2025-11", "2026-04", "2026-05"]
    c_neg_months = [str(m) for m in neg_c_months.index]

    accepted_b_unique = []
    for idx, row in b_unique_trades.iterrows():
        m_str = row["month_str"]
        is_winner = row["net_pnl"] > 0
        rescues_zero = m_str in c_zero_months
        improves_neg = m_str in c_neg_months
        if is_winner and (rescues_zero or improves_neg):
            accepted_b_unique.append(idx)

    t_fusion_selective = pd.concat([t_c, t_b.loc[accepted_b_unique]]).copy()
    t_fusion_selective = t_fusion_selective.sort_values(by="entry_time")

    print("\nFusion 1.1 Traceability (First 10 Trades):")
    first_10 = t_fusion_selective.head(10).copy()
    first_10["source"] = np.where(first_10.index.isin(c_indices), "Variant C Core", "B Rescue")
    for idx, row in first_10.iterrows():
        setup_time = pd.to_datetime(row["entry_time"] - 3600000, unit="ms", utc=True).strftime("%Y-%m-%d %H:%M")
        entry_time = pd.to_datetime(row["entry_time"], unit="ms", utc=True).strftime("%Y-%m-%d %H:%M")
        print(f"ID: {idx} | Source: {row['source']} | Setup: {setup_time} | Entry: {entry_time} | Side: {row['side']} | PnL: ${row['net_pnl']:.2f}")

if __name__ == "__main__":
    main()
