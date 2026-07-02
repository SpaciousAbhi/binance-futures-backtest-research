"""
tests/test_phase30_1_research_lab.py

Verification tests for Phase 30.1 - Research Lab and Idea Engine OS.
Ensures existence and correctness of all CLI, compiler, auditor, and validator files.
"""
import os
import subprocess
import sys
import pandas as pd
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_cmd(cmd_list):
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    return res.stdout, res.returncode

def test_research_lab_exists():
    assert os.path.exists(os.path.join(ROOT_DIR, "scripts", "research_lab.py"))

def test_research_lab_status_runs():
    cmd = [sys.executable, os.path.join(ROOT_DIR, "scripts", "research_lab.py"), "status"]
    out, code = run_cmd(cmd)
    assert code == 0
    assert "NOT_REAL_CAPITAL_READY" in out

def test_idea_engine_exists():
    assert os.path.exists(os.path.join(ROOT_DIR, "scripts", "idea_engine.py"))

def test_idea_library_exists():
    csv_path = os.path.join(ROOT_DIR, "reports", "phase30_1_idea_library.csv")
    md_path = os.path.join(ROOT_DIR, "reports", "phase30_1_top_ideas.md")
    assert os.path.exists(csv_path)
    assert os.path.exists(md_path)
    
    df = pd.read_csv(csv_path)
    assert len(df) == 15  # Exactly 15 structured strategy families
    # Verify key schema columns
    assert "idea_id" in df.columns
    assert "family" in df.columns
    assert "hypothesis" in df.columns
    assert "lookahead_risk" in df.columns
    assert "hardcoding_risk" in df.columns

def test_candidate_template_compiler_exists():
    assert os.path.exists(os.path.join(ROOT_DIR, "src", "research", "candidate_template_compiler.py"))

def test_candidate_registry_exists():
    reg_path = os.path.join(ROOT_DIR, "reports", "phase30_1_sample_candidate_registry.csv")
    schema_path = os.path.join(ROOT_DIR, "reports", "phase30_1_candidate_template_schema.md")
    assert os.path.exists(reg_path)
    assert os.path.exists(schema_path)
    
    df = pd.read_csv(reg_path)
    assert len(df) == 15
    assert "candidate_id" in df.columns
    assert "no_lookahead_audit_status" in df.columns
    assert "execution_status" in df.columns
    assert "metric_status" in df.columns

def test_audit_engine_exists():
    assert os.path.exists(os.path.join(ROOT_DIR, "scripts", "audit_engine.py"))

def test_audit_scan_exists():
    scan_path = os.path.join(ROOT_DIR, "reports", "phase30_1_audit_engine_scan.csv")
    assert os.path.exists(scan_path)
    
    df = pd.read_csv(scan_path)
    assert "file" in df.columns
    assert "pattern" in df.columns
    assert "classification" in df.columns
    # Ensure classification column uses correct categories
    unique_classifications = df["classification"].unique()
    assert all(c in ["ALLOWED_HISTORICAL_CONTEXT", "WARNING", "FAIL_LIVE_PATH_VIOLATION", "FAIL_FORCED_METRIC", "FAIL_LOOKAHEAD_RISK", "FAIL_FAKE_EXPANSION"] for c in unique_classifications)

def test_candidate_execution_queue_exists():
    assert os.path.exists(os.path.join(ROOT_DIR, "scripts", "candidate_execution_queue.py"))

def test_queue_smoke_test_exists():
    csv_path = os.path.join(ROOT_DIR, "reports", "phase30_1_execution_queue_smoke_test.csv")
    design_path = os.path.join(ROOT_DIR, "reports", "phase30_1_execution_queue_design.md")
    assert os.path.exists(csv_path)
    assert os.path.exists(design_path)
    
    df = pd.read_csv(csv_path)
    assert len(df) == 15
    # Verify unexecuted candidates remain blank
    unexec = df[df["execution_status"] == "REGISTERED"]
    assert len(unexec) == 13
    assert unexec["pnl"].isna().all()
    assert unexec["trades"].isna().all()
    assert unexec["profit_factor"].isna().all()
    
    # Executed candidates (batch size 2) must have metrics
    exec_cands = df[df["execution_status"] == "ENGINE_EXECUTED"]
    assert len(exec_cands) == 2
    assert not exec_cands["pnl"].isna().any()

def test_report_validator_exists():
    assert os.path.exists(os.path.join(ROOT_DIR, "scripts", "report_validator.py"))

def test_report_validator_output_exists():
    csv_path = os.path.join(ROOT_DIR, "reports", "phase30_1_report_validator_results.csv")
    assert os.path.exists(csv_path)

def test_update_project_memory_exists():
    assert os.path.exists(os.path.join(ROOT_DIR, "scripts", "update_project_memory.py"))
    assert os.path.exists(os.path.join(ROOT_DIR, "reports", "phase30_1_memory_updater_design.md"))

def test_readme_references_research_lab():
    readme = open(os.path.join(ROOT_DIR, "README.md"), encoding="utf-8").read()
    assert "scripts/research_lab.py" in readme or "research_lab.py" in readme

def test_agents_references_rulebook():
    agents = open(os.path.join(ROOT_DIR, "AGENTS.md"), encoding="utf-8").read()
    assert "PROJECT_RULEBOOK.md" in agents

def test_memory_index_references_infra():
    idx = open(os.path.join(ROOT_DIR, "project_memory", "MEMORY_INDEX.md"), encoding="utf-8").read()
    assert "research_lab.py" in idx

def test_no_huge_search_run():
    # Verify that checkpoints only contain smoke test candidates, proving no huge strategy search ran
    checkpoint_path = os.path.join(ROOT_DIR, "reports", "execution_checkpoint.json")
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) <= 2  # Max 2 candidates in smoke test

def test_no_new_benchmark_promoted():
    # Verify that BENCHMARK_REGISTRY has not added a new promoted strategy benchmark
    registry_path = os.path.join(ROOT_DIR, "project_memory", "BENCHMARK_REGISTRY.csv")
    df = pd.read_csv(registry_path)
    # Check that no benchmark has status VALID_EXECUTABLE_BENCHMARK except the allowed historical floor
    promoted = df[df["status"] == "VALID_EXECUTABLE_BENCHMARK"]
    assert len(promoted) == 1
    assert "Floor Fusion" in promoted.iloc[0]["benchmark_name"]
