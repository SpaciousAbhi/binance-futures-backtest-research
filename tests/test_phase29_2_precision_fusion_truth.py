import ast
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNNER = ROOT / "scripts" / "phase29_2_precision_fusion_truth.py"

REQUIRED = [
    "phase29_2_precision_fusion_truth_reconstruction_report.md",
    "phase29_2_pf12_fusion_lineage_map.csv",
    "phase29_2_pf12_executable_rebuild_results.csv",
    "phase29_2_pf12_trade_diff_audit.csv",
    "phase29_2_precision_fusion_compiler_spec.md",
    "phase29_2_dirty_pf8_trade_quality_audit.csv",
    "phase29_2_dirty_pf8_cluster_report.md",
    "phase29_2_multitimeframe_data_audit.csv",
    "phase29_2_sleeve_standalone_results.csv",
    "phase29_2_candidate_registry.csv",
    "phase29_2_candidate_results.csv",
    "phase29_2_recovered_router_trade_log.csv",
    "phase29_2_recovered_router_monthly_table.csv",
    "phase29_2_recovered_router_stress_table.csv",
    "phase29_2_benchmark_comparison_matrix.csv",
    "phase29_2_live_automation_readiness_audit.md",
    "phase29_2_no_lookahead_hardcoding_scan.csv",
    "phase29_2_final_status_correction.md",
    "phase29_2_audit_manifest.json",
]


def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(name):
    with (REPORTS / name).open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_phase29_2_required_files_exist():
    for name in REQUIRED:
        assert (REPORTS / name).exists(), f"missing {name}"


def test_phase29_2_manifest_hashes_match_disk():
    manifest = json.loads((REPORTS / "phase29_2_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["final_verdict"] == "PF12_TRADESET_RECONSTRUCTED_BUT_EXECUTABLE_FUSION_NOT_PROVEN"
    assert manifest["executed_candidate_count"] == 100
    for name, meta in manifest["files"].items():
        assert name != "phase29_2_audit_manifest.json"
        assert file_hash(REPORTS / name) == meta["sha256"]


def test_phase29_2_pf_means_precision_fusion_in_reports():
    report = (REPORTS / "phase29_2_precision_fusion_truth_reconstruction_report.md").read_text(encoding="utf-8")
    status = (REPORTS / "phase29_2_final_status_correction.md").read_text(encoding="utf-8")
    assert "PF means Precision Fusion" in report
    assert "PF means Precision Fusion" in status


def test_phase29_2_pf12_protected_metrics_and_executable_gap():
    rows = read_csv("phase29_2_pf12_executable_rebuild_results.csv")
    protected = next(r for r in rows if r["system"] == "PF1.2 protected reconstructed trade set")
    executable = next(r for r in rows if r["system"] == "PF1.2 executable floor fusion rebuild")
    assert protected["status"] == "TRADESET_RECONSTRUCTED_EXACT"
    assert round(float(protected["net_pnl"]), 2) == 21684.99
    assert int(protected["trades"]) == 325
    assert round(float(protected["profit_factor"]), 2) == 2.42
    assert round(float(protected["max_dd_pct"]), 2) == 10.87
    assert round(float(protected["combined_adverse"]), 2) == 15922.97
    assert executable["status"] == "EXECUTABLE_FUSION_RUN_NOT_EXACT"
    assert round(float(executable["net_pnl"]), 2) == 8426.09


def test_phase29_2_trade_diff_audit_records_gap():
    rows = read_csv("phase29_2_pf12_trade_diff_audit.csv")
    summary = next(r for r in rows if r["diff_type"] == "summary")
    assert summary["status"] == "PF12_TRADESET_RECONSTRUCTED_BUT_EXECUTABLE_FUSION_NOT_PROVEN"
    assert int(summary["missing_from_executable"]) > 0
    assert int(summary["extra_in_executable"]) > 0


def test_phase29_2_runner_has_no_new_forced_metric_path():
    source = RUNNER.read_text(encoding="utf-8")
    for forbidden in ["29386.59", "30580.40", "31250.80", ".sample(", "is_winner", "future_pnl", "future_mfe", "future_mae", "selected_trade_ids"]:
        assert forbidden not in source

    tree = ast.parse(source)
    forbidden_targets = {
        "diff_pnl",
        "forced_pnl",
        "pnl_70",
        "pnl_80",
        "pnl_81",
        "pf_70",
        "pf_80",
        "pf_81",
        "dd_70",
        "dd_80",
        "dd_81",
    }
    assigned = set()
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                assigned.add(target.id)
    assert not (assigned & forbidden_targets)


def test_phase29_2_no_lookahead_scan_keeps_new_runner_clean():
    rows = read_csv("phase29_2_no_lookahead_hardcoding_scan.csv")
    new_runner = [r for r in rows if r["scope"] == "new_runner"]
    assert new_runner
    assert all(r["classification"] == "CLEAN" for r in new_runner)
    assert any(r["classification"] == "LEGACY_FAIL_EVIDENCE" for r in rows)


def test_phase29_2_candidate_registry_and_execution_accounting():
    registry = read_csv("phase29_2_candidate_registry.csv")
    results = read_csv("phase29_2_candidate_results.csv")
    hashes = [r["candidate_hash"] for r in registry]
    assert len(registry) >= 1000
    assert len(hashes) == len(set(hashes))

    executed = [r for r in results if r["status"] == "EXECUTED_ENGINE"]
    unexecuted = [r for r in results if r["status"] == "REGISTERED_NOT_EXECUTED_TIMEBOXED"]
    assert len(executed) == 100
    assert len(unexecuted) == len(results) - len(executed)
    assert all(r["net_pnl"] != "" for r in executed)
    assert all(r["net_pnl"] == "" and r["trade_log_hash"] == "" for r in unexecuted)


def test_phase29_2_recovered_router_metrics_are_computed_from_trade_log():
    results = read_csv("phase29_2_candidate_results.csv")
    best = max((r for r in results if r["status"] == "EXECUTED_ENGINE"), key=lambda r: float(r["score"]))
    trades = read_csv("phase29_2_recovered_router_trade_log.csv")
    monthly = read_csv("phase29_2_recovered_router_monthly_table.csv")
    stress = read_csv("phase29_2_recovered_router_stress_table.csv")

    assert int(best["trades"]) == len(trades)
    trade_pnl = sum(float(r["net_pnl"]) for r in trades)
    monthly_pnl = sum(float(r["pnl"]) for r in monthly)
    assert abs(trade_pnl - monthly_pnl) < 0.01
    assert round(trade_pnl, 6) == round(float(best["net_pnl"]), 6)
    assert len(stress) == 15


def test_phase29_2_live_audit_not_real_capital_ready():
    text = (REPORTS / "phase29_2_live_automation_readiness_audit.md").read_text(encoding="utf-8")
    assert "NOT_REAL_CAPITAL_READY" in text
    assert "REAL_CAPITAL_READY is forbidden" in text
