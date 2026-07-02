"""
scripts/reproduce_strategy_baselines.py
Phase 39 Baseline Strategy Reproduction Harness
Reproduces Strategy #1 and Strategy #1.1 and outputs a reproduction lock report.
"""
import os
import sys
import json
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

from scripts.phase36_strategy1_decomposition_repair import load_market, build_strategy1, run_engine, compute_metrics
from scripts.phase37_strategy1_1_second_stage_optimization import build_signal_cache, evaluate_candidate, CandidateConfig

def main():
    print("=" * 60)
    print("REPRODUCING STRATEGY BASELINES (PHASE 39)")
    print("=" * 60)
    
    df = load_market()
    
    # 1. Strategy #1
    print("Executing Strategy #1...")
    trades1 = run_engine(df, build_strategy1())
    m1 = compute_metrics(trades1)
    
    expected1 = {
        "net_pnl": 11205.20,
        "trades": 557,
        "profit_factor": 1.2522,
        "max_drawdown_pct": 16.2186
    }
    
    print("\nStrategy #1 Results:")
    for k, v in expected1.items():
        print(f"  {k:<20} | Expected: {v:<10} | Observed: {m1[k]:<10}")
        
    # 2. Strategy #1.1
    print("\nExecuting Strategy #1.1 (P37_CAND_0357)...")
    cache = build_signal_cache(df)
    params11 = {
        "allowed_sessions": ["LONDON", "NEW_YORK", "OFF_HOURS"],
        "allowed_sources": ["BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short", "Funding Reversal Short"],
        "disallowed_sources": [],
        "max_abs_funding": 0.0015,
        "max_cost_to_risk": 0.12,
        "min_adx": 12,
        "min_atr_pct": 0.3,
        "min_bb_width": 0.03,
        "min_projected_net_R": 0.82,
        "min_stop_atr": 0.0,
        "off_hours_min_expected_R": 0.0
    }
    config = CandidateConfig("P37_CAND_0357", params11, "locked_hash", "phase37_focused_strategy1_guard")
    row11, trades11, stress11 = evaluate_candidate(df, cache, config, write_log=False)
    
    expected11 = {
        "net_pnl": 11231.08,
        "trades": 404,
        "profit_factor": 1.3862,
        "max_drawdown_pct": 9.3716
    }
    
    print("\nStrategy #1.1 Results:")
    for k, v in expected11.items():
        print(f"  {k:<20} | Expected: {v:<10} | Observed: {row11[k]:<10}")
        
    # 3. Create reproduction lock CSV
    repro_rows = []
    
    # Strategy #1 rows
    for k, v in expected1.items():
        repro_rows.append({
            "strategy": "Strategy #1",
            "metric": k,
            "expected": v,
            "observed": m1[k],
            "drift": round(abs(m1[k] - v), 4),
            "status": "PASS" if abs(m1[k] - v) < 0.01 else "FAIL"
        })
        
    # Strategy #1.1 rows
    for k, v in expected11.items():
        repro_rows.append({
            "strategy": "Strategy #1.1",
            "metric": k,
            "expected": v,
            "observed": row11[k],
            "drift": round(abs(row11[k] - v), 4),
            "status": "PASS" if abs(row11[k] - v) < 0.01 else "FAIL"
        })
        
    repro_df = pd.DataFrame(repro_rows)
    repro_path = os.path.join(_ROOT, "reports", "phase39_strategy_reproduction_lock.csv")
    repro_df.to_csv(repro_path, index=False)
    print(f"\nReproduction lock CSV saved to: {repro_path}")
    
    # Assert check
    failures = repro_df[repro_df["status"] == "FAIL"]
    if not failures.empty:
        print("\n[FAIL] Baseline strategy reproduction failed with drift!")
        sys.exit(1)
    else:
        print("\n[PASS] All baseline strategies reproduced with 0.00% drift!")
        sys.exit(0)

if __name__ == "__main__":
    main()
