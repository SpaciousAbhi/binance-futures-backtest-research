import ast
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNNER = ROOT / "scripts" / "phase29_3_precision_fusion_recovery.py"

REQUIRED = [
    "phase29_3_precision_fusion_lineage_recovery_and_pf8_rebuild_report.md",
    "phase29_3_variant_b_rebuild.csv",
    "phase29_3_variant_c_rebuild.csv",
    "phase29_3_pf12_fusion_lineage_map.csv",
    "phase29_3_pf12_executable_rebuild_trade_log.csv",
    "phase29_3_pf12_trade_diff_audit.csv",
    "phase29_3_precision_fusion_compiler_spec.md",
    "phase29_3_dirty_pf8_quality_surgery.csv",
    "phase29_3_recovered_candidate_registry.csv",
    "phase29_3_recovered_candidate_results.csv",
    "phase29_3_best_recovered_router_trade_log.csv",
    "phase29_3_benchmark_comparison_matrix.csv",
    "phase29_3_live_rule_audit.md",
    "phase29_3_audit_manifest.json",
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


def test_phase29_3_required_files_exist():
    for name in REQUIRED:
        assert (REPORTS / name).exists(), f"missing {name}"


def test_phase29_3_manifest_hashes_match_disk():
    manifest = json.loads((REPORTS / "phase29_3_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["final_verdict"] == "PF12_PARTIAL_EXECUTABLE_REBUILD_REQUIRES_MORE_RECOVERY"
    for name, meta in manifest["files"].items():
        assert name != "phase29_3_audit_manifest.json"
        assert file_hash(REPORTS / name) == meta["sha256"]


def test_phase29_3_pf_means_precision_fusion():
    report = (REPORTS / "phase29_3_precision_fusion_lineage_recovery_and_pf8_rebuild_report.md").read_text(encoding="utf-8")
    spec = (REPORTS / "phase29_3_precision_fusion_compiler_spec.md").read_text(encoding="utf-8")
    assert "PF means Precision Fusion" in report
    assert "PF means Precision Fusion" in spec


def test_phase29_3_runner_has_no_forced_metric_logic():
    source = RUNNER.read_text(encoding="utf-8")
    for forbidden in [
        "29386.59",
        "30580.40",
        "31250.80",
        ".sample(",
        "is_winner",
        "future_pnl",
        "future_mfe",
        "future_mae",
        "selected_trade_ids",
    ]:
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


def test_phase29_3_variant_b_and_c_rebuilds_exist_and_have_teacher_rows():
    b_rows = read_csv("phase29_3_variant_b_rebuild.csv")
    c_rows = read_csv("phase29_3_variant_c_rebuild.csv")
    assert any(r["status"] == "TEACHER_TRADESET_RECONSTRUCTED" for r in b_rows)
    assert any(r["status"] == "EXECUTABLE_PROXY_NOT_EXACT" for r in b_rows)
    assert any(r["status"] == "TEACHER_TRADESET_RECONSTRUCTED" for r in c_rows)
    assert any(r["status"] == "EXECUTABLE_PROXY_NOT_EXACT" for r in c_rows)
    b_teacher = next(r for r in b_rows if r["status"] == "TEACHER_TRADESET_RECONSTRUCTED")
    c_teacher = next(r for r in c_rows if r["status"] == "TEACHER_TRADESET_RECONSTRUCTED")
    assert round(float(b_teacher["net_pnl"]), 2) == 19589.91
    assert round(float(c_teacher["net_pnl"]), 2) == 20455.48


def test_phase29_3_pf12_lineage_and_diff_exist():
    lineage = read_csv("phase29_3_pf12_fusion_lineage_map.csv")
    diff = read_csv("phase29_3_pf12_trade_diff_audit.csv")
    assert lineage
    summary = next(r for r in diff if r["diff_type"] == "summary")
    assert summary["status"] == "PF12_PARTIAL_EXECUTABLE_REBUILD_REQUIRES_MORE_RECOVERY"
    assert int(summary["missing_from_rebuild"]) > 0


def test_phase29_3_candidate_registry_and_metric_accounting():
    registry = read_csv("phase29_3_recovered_candidate_registry.csv")
    results = read_csv("phase29_3_recovered_candidate_results.csv")
    hashes = [r["candidate_hash"] for r in registry]
    assert len(registry) >= 1000
    assert len(hashes) == len(set(hashes))
    executed = [r for r in results if r["status"] == "EXECUTED_ENGINE"]
    unexecuted = [r for r in results if r["status"] == "REGISTERED_NOT_EXECUTED_TIMEBOXED"]
    assert len(executed) >= 100
    assert all(r["net_pnl"] != "" for r in executed)
    assert all(r["net_pnl"] == "" and r["trade_log_hash"] == "" for r in unexecuted)


def test_phase29_3_monthly_tables_reconcile_with_trade_logs():
    pairs = [
        ("phase29_3_pf12_executable_rebuild_trade_log.csv", "phase29_3_pf12_executable_rebuild_monthly_table.csv"),
        ("phase29_3_best_recovered_router_trade_log.csv", "phase29_3_best_recovered_router_monthly_table.csv"),
    ]
    for trade_file, monthly_file in pairs:
        trades = read_csv(trade_file)
        monthly = read_csv(monthly_file)
        trade_pnl = sum(float(r["net_pnl"]) for r in trades) if trades else 0.0
        monthly_pnl = sum(float(r["pnl"]) for r in monthly) if monthly else 0.0
        assert abs(trade_pnl - monthly_pnl) < 0.01


def test_phase29_3_live_rule_audit_not_real_capital_ready():
    text = (REPORTS / "phase29_3_live_rule_audit.md").read_text(encoding="utf-8")
    assert "NOT_REAL_CAPITAL_READY" in text
    assert "exchange-level shadow/live proof" in text
