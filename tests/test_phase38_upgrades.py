#!/usr/bin/env python3
"""
tests/test_phase38_upgrades.py

Unit tests for Phase 38 Research Lab upgrades and Idea Engine.
"""
import os
import sys
import subprocess
import pandas as pd

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_cli(args):
    cmd = [sys.executable, os.path.join(ROOT_DIR, "scripts", "research_lab.py")] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout, res.returncode

def test_preflight():
    # Preflight check should run and return 0 (since our files and memory are clean)
    stdout, code = run_cli(["preflight"])
    assert "PREFLIGHT STATUS: SUCCESS" in stdout
    assert code == 0

def test_postflight():
    stdout, code = run_cli(["postflight"])
    assert "POSTFLIGHT STATUS: SUCCESS" in stdout
    assert code == 0

def test_candidate_dashboard():
    stdout, code = run_cli(["candidate-dashboard"])
    assert "CANDIDATE EXECUTION QUEUE DASHBOARD" in stdout
    assert code == 0

def test_schema_validators():
    registry_path = os.path.join(ROOT_DIR, "reports", "phase37_candidate_registry.csv")
    if os.path.exists(registry_path):
        stdout, code = run_cli(["validate-candidate-schema", registry_path])
        assert "Candidate registry schema is fully compliant" in stdout
        assert code == 0

    trade_log_path = os.path.join(ROOT_DIR, "reports", "phase37_strategy1_1_trade_log.csv")
    if os.path.exists(trade_log_path):
        stdout, code = run_cli(["validate-trade-schema", trade_log_path])
        assert "Trade log schema is fully compliant" in stdout
        assert code == 0

def test_idea_engine_outputs():
    # Verify that the generated Idea Engine files exist and are not empty
    library_path = os.path.join(ROOT_DIR, "reports", "phase38_idea_engine_library.csv")
    top_ideas_path = os.path.join(ROOT_DIR, "reports", "phase38_top_50_ideas.md")

    assert os.path.exists(library_path)
    assert os.path.exists(top_ideas_path)

    df = pd.read_csv(library_path)
    assert len(df) >= 250
    assert "live_known_safety" in df.columns
    assert "expected_pnl_impact" in df.columns
