#!/usr/bin/env python3
"""
scripts/trade_analyzer.py

Runs trade-by-trade intelligence audit for Strategy #1 and Strategy #1.1.
Outputs:
  - reports/phase38_trade_by_trade_intelligence.csv
  - reports/phase38_trade_cluster_diagnostics.csv
"""
import os
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S1_PATH = os.path.join(ROOT_DIR, "reports", "phase34_strategy_1_trade_log_copy.csv")
S1_1_PATH = os.path.join(ROOT_DIR, "reports", "phase37_strategy1_1_trade_log.csv")
OUT_PATH = os.path.join(ROOT_DIR, "reports", "phase38_trade_by_trade_intelligence.csv")
DIAG_PATH = os.path.join(ROOT_DIR, "reports", "phase38_trade_cluster_diagnostics.csv")

def analyze_log(df, strategy_id):
    df = df.copy()
    df["strategy_id"] = strategy_id
    
    # Ensure times are numeric
    df["entry_time"] = pd.to_numeric(df["entry_time"])
    df["exit_time"] = pd.to_numeric(df["exit_time"])
    
    # Ensure PnL columns exist
    df["net_pnl"] = pd.to_numeric(df["net_pnl"])
    df["gross_pnl"] = pd.to_numeric(df.get("gross_pnl", df["net_pnl"]))
    df["fees"] = pd.to_numeric(df.get("fees", 0))
    df["slippage"] = pd.to_numeric(df.get("slippage", 0))
    df["funding"] = pd.to_numeric(df.get("funding", 0))
    df["R"] = pd.to_numeric(df.get("R", df["net_pnl"] / 100.0)) # estimate if missing
    
    # Calculate hold time (candles)
    if "hold_candles" in df.columns:
        df["hold_time"] = pd.to_numeric(df["hold_candles"])
    else:
        df["hold_time"] = (df["exit_time"] - df["entry_time"]) / 3600000.0
        
    # Check source_sleeve
    if "source_sleeve" not in df.columns:
        df["source_sleeve"] = df["strategy"]
        
    # Check same_candle
    if "same_candle" not in df.columns:
        df["same_candle"] = False
        
    # Check expected_R, projected_net_R, cost_to_risk
    if "expected_R" not in df.columns:
        df["expected_R"] = df["R"]
    if "projected_net_R" not in df.columns:
        df["projected_net_R"] = df["R"]
    if "cost_to_risk" not in df.columns:
        df["cost_to_risk"] = 0.05
        
    # Sort chronologically
    df = df.sort_values("entry_time").reset_index(drop=True)
    
    # Drawdown calculation
    capital = 10000.0
    equity = capital + df["net_pnl"].cumsum()
    peak = equity.cummax()
    dd_pct = (peak - equity) / peak * 100.0
    
    df["drawdown_contribution"] = np.where(df["net_pnl"] < 0, np.abs(df["net_pnl"]) / peak * 100.0, 0.0)
    
    # Losing and Winning clusters (rolling 5-trade net PnL)
    rolling_pnl = df["net_pnl"].rolling(window=5, center=True, min_periods=1).sum()
    df["losing_cluster"] = rolling_pnl < 0
    df["winning_cluster"] = rolling_pnl > 0
    
    # High friction
    friction_cost = df["fees"] + df["slippage"]
    df["high_friction"] = friction_cost > 20.0
    
    # Quality
    df["high_quality"] = (df["net_pnl"] > 0) & (df["R"] >= 1.2)
    df["low_quality"] = (df["net_pnl"] < 0) | (df["R"] < 0.5)
    
    # Suggest live-known improvements
    filters = []
    for idx, row in df.iterrows():
        filt = "none"
        if row["net_pnl"] < 0:
            if row["session"] == "OFF_HOURS":
                filt = "filter_off_hours"
            elif "Low-Activity" in str(row["source_sleeve"]) and "Long" in str(row["source_sleeve"]):
                filt = "suppress_low_activity_long"
            elif row["cost_to_risk"] > 0.12:
                filt = "cap_cost_to_risk"
            elif row["projected_net_R"] < 0.82:
                filt = "filter_low_projected_R"
        filters.append(filt)
    df["live_known_improvement"] = filters
    
    # Year/Month
    dt = pd.to_datetime(df["entry_time"], unit="ms", utc=True)
    df["year"] = dt.dt.year
    df["month"] = dt.dt.strftime("%Y-%m")
    
    return df[[
        "strategy_id", "source_sleeve", "side", "session", "entry_time", "exit_time",
        "hold_time", "entry_price", "exit_price", "net_pnl", "R", "expected_R",
        "projected_net_R", "cost_to_risk", "fees", "slippage", "funding", "reason",
        "same_candle", "month", "year", "drawdown_contribution", "losing_cluster",
        "winning_cluster", "high_friction", "low_quality", "high_quality",
        "live_known_improvement"
    ]]

def main():
    print("Running Trade-by-Trade Strategy Intelligence Audit...")
    
    if not os.path.exists(S1_PATH):
        print(f"Error: Strategy #1 log missing at {S1_PATH}")
        sys.exit(1)
        
    if not os.path.exists(S1_1_PATH):
        print(f"Error: Strategy #1.1 log missing at {S1_1_PATH}")
        sys.exit(1)
        
    s1_df = pd.read_csv(S1_PATH)
    s1_1_df = pd.read_csv(S1_1_PATH)
    
    print(f"Loaded Strategy #1: {len(s1_df)} trades")
    print(f"Loaded Strategy #1.1: {len(s1_1_df)} trades")
    
    analyzed_s1 = analyze_log(s1_df, "Strategy #1 (Combined Router v1)")
    analyzed_s1_1 = analyze_log(s1_1_df, "Strategy #1.1 (P37_CAND_0357)")
    
    combined = pd.concat([analyzed_s1, analyzed_s1_1], ignore_index=True)
    
    # Ensure output dir exists
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    
    combined.to_csv(OUT_PATH, index=False)
    print(f"Written Trade-by-Trade Intelligence CSV: {OUT_PATH}")
    
    # Build trade cluster diagnostics
    diag_rows = []
    for strat_id, df in [("Strategy #1", analyzed_s1), ("Strategy #1.1", analyzed_s1_1)]:
        losing_count = df["losing_cluster"].sum()
        winning_count = df["winning_cluster"].sum()
        high_fric_count = df["high_friction"].sum()
        low_qual_count = df["low_quality"].sum()
        high_qual_count = df["high_quality"].sum()
        total_pnl = df["net_pnl"].sum()
        avg_dd_contrib = df["drawdown_contribution"].mean()
        
        diag_rows.append({
            "strategy": strat_id,
            "total_trades": len(df),
            "total_pnl": round(total_pnl, 2),
            "losing_cluster_trades": losing_count,
            "winning_cluster_trades": winning_count,
            "high_friction_trades": high_fric_count,
            "low_quality_trades": low_qual_count,
            "high_quality_trades": high_qual_count,
            "avg_drawdown_contribution": round(avg_dd_contrib, 4)
        })
        
    diag_df = pd.DataFrame(diag_rows)
    diag_df.to_csv(DIAG_PATH, index=False)
    print(f"Written Trade Cluster Diagnostics CSV: {DIAG_PATH}")

if __name__ == "__main__":
    main()
