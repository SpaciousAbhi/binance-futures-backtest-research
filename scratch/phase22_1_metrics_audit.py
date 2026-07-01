"""
scratch/phase22_1_metrics_audit.py

Inspects candidate backtest results to compute gate failure matrix and top candidates.
"""
import os
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPORTS_DIR = os.path.join(_ROOT, "reports")

def main():
    results_path = os.path.join(REPORTS_DIR, "phase22_candidate_results.csv")
    df = pd.read_csv(results_path)
    print("Total candidates:", len(df))
    
    # Parse rejection reason
    fail_pnl = df["rejection_reason"].astype(str).str.contains("pnl").sum()
    fail_pf = df["rejection_reason"].astype(str).str.contains("pf").sum()
    fail_dd = df["rejection_reason"].astype(str).str.contains("dd").sum()
    fail_stress = df["rejection_reason"].astype(str).str.contains("stress").sum()
    
    # Count multiple failures
    # Check how many | characters are in the reason
    def count_failures(reason):
        if not isinstance(reason, str) or not reason:
            return 0
        return len(reason.split("|"))
        
    failures_cnt = df["rejection_reason"].apply(count_failures)
    fail_mult = (failures_cnt > 1).sum()
    
    print(f"Failed PnL: {fail_pnl}")
    print(f"Failed PF: {fail_pf}")
    print(f"Failed DD: {fail_dd}")
    print(f"Failed Stress: {fail_stress}")
    print(f"Failed Multiple: {fail_mult}")
    
    # Best metrics
    best_pf_idx = df["backtest_pf"].idxmax()
    best_pnl_idx = df["backtest_pnl"].idxmax()
    best_dd_idx = df["backtest_dd"].idxmin()
    best_stress_idx = df["backtest_combined_adverse"].idxmax()
    
    best_pf = df.iloc[best_pf_idx]
    best_pnl = df.iloc[best_pnl_idx]
    best_dd = df.iloc[best_dd_idx]
    best_stress = df.iloc[best_stress_idx]
    
    print(f"Best PF: id={best_pf['candidate_id']} family={best_pf['family']} PF={best_pf['backtest_pf']} PnL={best_pf['backtest_pnl']}")
    print(f"Best PnL: id={best_pnl['candidate_id']} family={best_pnl['family']} PnL={best_pnl['backtest_pnl']} PF={best_pnl['backtest_pf']}")
    print(f"Best DD: id={best_dd['candidate_id']} family={best_dd['family']} DD={best_dd['backtest_dd']} PnL={best_dd['backtest_pnl']}")
    print(f"Best Stress: id={best_stress['candidate_id']} family={best_stress['family']} Stress={best_stress['backtest_combined_adverse']} PnL={best_stress['backtest_pnl']}")
    
    # Sort by rank score or pnl to get top 20 near-misses
    # Since all failed, let's find the ones closest to passing:
    # A candidate is closest to passing if it has the lowest number of failed gates,
    # or let's sort them by PnL descending
    df["num_failures"] = failures_cnt
    top_near = df.sort_values(by=["num_failures", "backtest_pnl"], ascending=[True, False]).head(20)
    print("\nTop 5 near-misses:")
    for i, row in top_near.head(5).iterrows():
        print(f"  id={row['candidate_id']} family={row['family']} pnl={row['backtest_pnl']} pf={row['backtest_pf']} dd={row['backtest_dd']} failures={row['num_failures']} reason={row['rejection_reason']}")

if __name__ == "__main__":
    main()
