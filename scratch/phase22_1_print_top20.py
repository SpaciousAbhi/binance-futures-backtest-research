"""
scratch/phase22_1_print_top20.py

Prints the top 20 candidates in markdown table format.
"""
import os
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPORTS_DIR = os.path.join(_ROOT, "reports")

def main():
    results_path = os.path.join(REPORTS_DIR, "phase22_candidate_results.csv")
    df = pd.read_csv(results_path)
    top20 = df.sort_values(by="backtest_pnl", ascending=False).head(20)
    for i, row in top20.iterrows():
        print(f"| {row['candidate_id']} | {row['candidate_hash']} | {row['family']} | ${row['backtest_pnl']:.2f} | {row['backtest_pf']:.4f} | {row['backtest_dd']:.2%} | ${row['backtest_combined_adverse']:.2f} | {row['rejection_reason'][:60]}... |")

if __name__ == "__main__":
    main()
