"""
scripts/diagnose_top_candidate.py
Runs monthly reconciliation and yearly analytics for the promoted Strategy #1.2 candidate (P39_CAND_0551).
"""
import os
import sys
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

def main():
    print("=" * 60)
    print("DIAGNOSTICS & MONTHLY RECONCILIATION FOR STRATEGY #1.2")
    print("=" * 60)
    
    log_path = os.path.join(_ROOT, "reports", "phase39_P39_CAND_0551_trade_log.csv")
    if not os.path.exists(log_path):
        print(f"[ERROR] Trade log not found at: {log_path}")
        sys.exit(1)
        
    df = pd.read_csv(log_path)
    df["entry_dt"] = pd.to_datetime(df["entry_time"], unit="ms", utc=True)
    df["month"] = df["entry_dt"].dt.to_period("M")
    df["year"] = df["entry_dt"].dt.to_period("Y")
    
    # 1. Month-by-month reconciliation
    monthly_pnl = df.groupby("month")["net_pnl"].sum()
    monthly_trades = df.groupby("month")["net_pnl"].count()
    
    monthly_rows = []
    for m in pd.period_range(start=df["month"].min(), end=df["month"].max(), freq="M"):
        pnl = monthly_pnl.get(m, 0.0)
        trades = monthly_trades.get(m, 0)
        monthly_rows.append({
            "month": str(m),
            "net_pnl": round(float(pnl), 2),
            "trades": int(trades),
            "status": "PROFITABLE" if pnl > 0 else ("UNPROFITABLE" if pnl < 0 else "ZERO_TRADES")
        })
        
    monthly_df = pd.DataFrame(monthly_rows)
    monthly_path = os.path.join(_ROOT, "reports", "phase39_top_candidate_monthly_reconciliation.csv")
    monthly_df.to_csv(monthly_path, index=False)
    print(f"[PASS] Monthly reconciliation CSV saved to: {monthly_path}")
    
    # 2. Yearly breakdown printout
    yearly_pnl = df.groupby("year")["net_pnl"].sum()
    yearly_trades = df.groupby("year")["net_pnl"].count()
    print("\nYearly Performance Breakdown:")
    print("-" * 50)
    print(f"{'Year':<10} | {'Trades':<8} | {'Net PnL':<12}")
    print("-" * 50)
    for y in sorted(df["year"].unique()):
        print(f"{str(y):<10} | {yearly_trades.get(y, 0):<8} | ${yearly_pnl.get(y, 0.0):<11.2f}")
    print("-" * 50)
    
    print(f"\nTotal profitable months: {len(monthly_df[monthly_df['net_pnl'] > 0])}")
    print(f"Total unprofitable months: {len(monthly_df[monthly_df['net_pnl'] < 0])}")
    print(f"Total zero months: {len(monthly_df[monthly_df['net_pnl'] == 0])}")
    
if __name__ == "__main__":
    main()
