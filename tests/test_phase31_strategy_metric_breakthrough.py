import os
import json
import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS = os.path.join(ROOT, "reports")

def test_teacher_replay_files():
    replay_path = os.path.join(REPORTS, "phase31_teacher_trade_replay.csv")
    summary_path = os.path.join(REPORTS, "phase31_teacher_replay_summary.csv")
    
    assert os.path.exists(replay_path), "Teacher replay CSV is missing"
    assert os.path.exists(summary_path), "Teacher replay summary CSV is missing"
    
    df_replay = pd.read_csv(replay_path)
    assert len(df_replay) == 325, f"Expected 325 replayed trades, got {len(df_replay)}"
    
    df_summary = pd.read_csv(summary_path)
    metrics = df_summary["metric"].tolist()
    assert "total_trades" in metrics
    assert "replay_net_pnl" in metrics
    assert "replay_profit_factor" in metrics
    assert "replay_max_dd_pct" in metrics

def test_weakness_map():
    path = os.path.join(REPORTS, "phase31_metric_weakness_map.csv")
    assert os.path.exists(path), "Metric weakness map CSV is missing"
    df = pd.read_csv(path)
    assert len(df) == 4, "Expected 4 metrics in weakness map"
    assert set(df.columns) == {"metric", "floor_1h", "event_5m", "teacher_replay"}

def test_strategy_ideas():
    path = os.path.join(REPORTS, "phase31_strategy_idea_library.csv")
    assert os.path.exists(path), "Idea library CSV is missing"
    df = pd.read_csv(path)
    assert len(df) == 15, f"Expected 15 ideas, got {len(df)}"

def test_candidate_registry_and_results():
    registry_path = os.path.join(REPORTS, "phase31_candidate_registry.csv")
    results_path = os.path.join(REPORTS, "phase31_candidate_results.csv")
    
    assert os.path.exists(registry_path), "Candidate registry is missing"
    assert os.path.exists(results_path), "Candidate results is missing"
    
    df_reg = pd.read_csv(registry_path)
    df_res = pd.read_csv(results_path)
    
    assert len(df_reg) == 1000, f"Expected 1000 candidates in registry, got {len(df_reg)}"
    assert len(df_res) == 1000, f"Expected 1000 rows in results, got {len(df_res)}"
    
    # 350 executed, 650 registered
    executed = df_res[df_res["execution_status"] == "ENGINE_EXECUTED"]
    registered = df_res[df_res["execution_status"] == "REGISTERED"]
    
    assert len(executed) == 350, f"Expected 350 executed candidates, got {len(executed)}"
    assert len(registered) == 650, f"Expected 650 registered candidates, got {len(registered)}"
    
    # Executed must have metrics
    assert not executed["pnl"].isna().any(), "Executed candidates must have non-blank pnl"
    # Registered must have blank metrics
    assert registered["pnl"].isna().all(), "Registered candidates must have blank pnl"

def test_best_router_files():
    trade_log = os.path.join(REPORTS, "phase31_best_router_trade_log.csv")
    monthly = os.path.join(REPORTS, "phase31_best_router_monthly_table.csv")
    stress = os.path.join(REPORTS, "phase31_best_router_stress_table.csv")
    
    assert os.path.exists(trade_log), "Best router trade log is missing"
    assert os.path.exists(monthly), "Best router monthly table is missing"
    assert os.path.exists(stress), "Best router stress table is missing"
    
    df_stress = pd.read_csv(stress)
    assert len(df_stress) == 15, f"Expected 15 stress scenarios, got {len(df_stress)}"

def test_manifest():
    manifest_path = os.path.join(REPORTS, "phase31_audit_manifest.json")
    assert os.path.exists(manifest_path), "Audit manifest is missing"
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    assert manifest["phase"] == "31"
    assert manifest["verdict"] == "PHASE31_PARTIAL_PASS_TEACHER_REPLAY_FAILED_NEW_REAL_BASELINE_FOUND"
    
    for filename in manifest["files"]:
        assert os.path.exists(os.path.join(ROOT, filename)), f"File in manifest does not exist: {filename}"
