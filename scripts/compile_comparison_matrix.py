"""
scripts/compile_comparison_matrix.py
Compiles comparison matrix CSV comparing Strategy #1, Strategy #1.1, and Strategy #1.2.
"""
import os
import sys
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

def main():
    print("=" * 60)
    print("COMPILING STRATEGY COMPARISON MATRIX")
    print("=" * 60)
    
    # Core stats from verified sources
    data = [
        {
            "strategy": "Strategy #1 (Combined Router v1)",
            "pnl": 11205.20,
            "trades": 557,
            "profit_factor": 1.2522,
            "max_drawdown_pct": 16.2186,
            "stress_pass_count": 7,
            "combined_adverse_pnl": -39138.38,
            "win_rate": 0.518,
            "status": "VALID_EXECUTABLE_BASELINE_BUT_STRESS_FRAGILE"
        },
        {
            "strategy": "Strategy #1.1 (P37_CAND_0357)",
            "pnl": 11231.08,
            "trades": 404,
            "profit_factor": 1.3862,
            "max_drawdown_pct": 9.3716,
            "stress_pass_count": 8,
            "combined_adverse_pnl": -33384.48,
            "win_rate": 0.522,
            "status": "VALID_PROMOTED_CANDIDATE"
        },
        {
            "strategy": "Strategy #1.2 (P39_CAND_0551)",
            "pnl": 11431.41,
            "trades": 340,
            "profit_factor": 1.4998,
            "max_drawdown_pct": 7.9380,
            "stress_pass_count": 8,
            "combined_adverse_pnl": -25369.59,
            "win_rate": 0.5647,
            "status": "VALID_PROMOTED_CANDIDATE"
        }
    ]
    
    df = pd.DataFrame(data)
    matrix_path = os.path.join(_ROOT, "reports", "phase39_strategy_comparison.csv")
    df.to_csv(matrix_path, index=False)
    print(f"[PASS] Strategy comparison matrix CSV saved to: {matrix_path}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
