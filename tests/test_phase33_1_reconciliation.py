"""Phase 33.1 reconciliation and baseline protection tests."""
import hashlib
import json
import os

import pandas as pd


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS = os.path.join(ROOT, "reports")
PM = os.path.join(ROOT, "project_memory")


def report(name: str) -> str:
    return os.path.join(REPORTS, name)


def memory(name: str) -> str:
    return os.path.join(PM, name)


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def metrics_dict() -> dict[str, str]:
    df = pd.read_csv(report("phase33_1_baseline_recovery_metrics.csv"))
    return dict(zip(df["metric"], df["value"].astype(str)))


def test_phase33_1_main_report_exists_and_has_verdict():
    path = report("phase33_1_codex_reconciliation_baseline_recovery_and_truth_lock_report.md")
    assert os.path.exists(path)
    text = read(path)
    assert "PHASE33_1_PASS_CODEX_WORK_RECONCILED_BASELINE_RECOVERED_AND_PROTECTED" in text
    assert "Phase 33 is classified as `RESEARCH_ONLY_CONSERVATIVE_STRESS_VARIANT`" in text


def test_recovered_baseline_trade_log_has_557_trades():
    path = report("phase33_1_baseline_recovery_trade_log.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert len(df) == 557
    assert (df["exit_time"] >= df["entry_time"]).all()


def test_recovered_baseline_metrics_match_trade_log_recalculation():
    m = metrics_dict()
    assert float(m["net_pnl"]) == 11205.2
    assert int(float(m["trades"])) == 557
    assert float(m["profit_factor"]) == 1.2522
    assert float(m["max_drawdown_pct"]) == 16.2186
    assert int(float(m["winning_trades"])) == 301
    assert int(float(m["losing_trades"])) == 256
    assert int(float(m["positive_months"])) == 52
    assert int(float(m["negative_months"])) == 25
    assert int(float(m["zero_months"])) == 0


def test_trade_integrity_checks_pass_or_warn_only_for_documented_duplicates():
    df = pd.read_csv(report("phase33_1_baseline_trade_integrity.csv"))
    failures = df[df["status"] == "FAIL"]
    assert len(failures) == 0, failures.to_string(index=False)
    assert "same_candle_trades_classified" in set(df["check"])


def test_baseline_stress_truth_locked_to_seven_pass_eight_fail():
    df = pd.read_csv(report("phase33_1_baseline_recovery_stress_table.csv"))
    assert len(df) == 15
    assert int((df["verdict"] == "PASS").sum()) == 7
    assert int((df["verdict"] == "FAIL").sum()) == 8
    combined = df[df["scenario"] == "combined adverse"].iloc[0]
    assert round(float(combined["net_pnl"]), 2) == -39138.38
    assert round(float(combined["max_dd_pct"]), 2) == 359.59


def test_phase33_vs_baseline_classification_keeps_primary_baseline():
    df = pd.read_csv(report("phase33_1_phase33_vs_baseline_comparison.csv"))
    baseline = df[df["system"] == "Combined Router v1 active baseline"].iloc[0]
    phase33 = df[df["system"] == "Codex Phase 33 conservative fusion"].iloc[0]
    assert baseline["classification"] == "ACTIVE_PRIMARY_EXECUTABLE_BASELINE"
    assert baseline["promotion_decision"] == "RETAIN_AS_PRIMARY"
    assert phase33["classification"] == "RESEARCH_ONLY_CONSERVATIVE_STRESS_VARIANT"
    assert phase33["promotion_decision"] == "RESEARCH_ONLY_NOT_PRIMARY"


def test_project_memory_protects_baseline_and_demotes_phase33():
    handoff = read(memory("CURRENT_HANDOFF.md"))
    registry = pd.read_csv(memory("BENCHMARK_REGISTRY.csv"))
    assert "Combined Router v1 remains the active primary executable baseline" in handoff
    assert "Phase 33 did not replace the primary baseline" in handoff
    assert "PASS=7 / FAIL=8" in handoff
    phase33 = registry[registry["benchmark_name"] == "Phase 33 Best Fusion"].iloc[0]
    recovered = registry[registry["benchmark_name"] == "Phase 33.1 Recovered Combined Router v1"].iloc[0]
    assert phase33["status"] == "RESEARCH_ONLY_CONSERVATIVE_STRESS_VARIANT"
    assert recovered["status"] == "ACTIVE_PRIMARY_EXECUTABLE_BASELINE"


def test_source_lock_hashes_required_files():
    df = pd.read_csv(report("phase33_1_source_lock.csv"))
    assert len(df) >= 10
    assert df["exists"].astype(str).str.upper().eq("TRUE").all()
    assert df["sha256"].astype(str).str.len().eq(64).all()


def test_phase33_1_script_has_no_fake_expansion_or_live_forbidden_labels():
    text = read(os.path.join(ROOT, "scripts", "phase33_1_reconciliation.py"))
    assert "replace=True" not in text
    assert ".sample(" in text  # stress uses deterministic drops without replacement, not benchmark expansion
    for token in ["is_winner", "future_pnl", "future_return", "future_mfe", "future_mae"]:
        assert token not in text


def test_manifest_hashes_match_disk_files():
    manifest = json.loads(read(report("phase33_1_audit_manifest.json")))
    assert manifest["phase33_classification"] == "RESEARCH_ONLY_CONSERVATIVE_STRESS_VARIANT"
    for name, meta in manifest["files"].items():
        path = report(name)
        assert os.path.exists(path), name
        assert sha256_file(path) == meta["sha256"], name
