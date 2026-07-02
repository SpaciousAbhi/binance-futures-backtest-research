import ast
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNNER = ROOT / "scripts" / "phase29_4_teacher_distillation.py"

REQUIRED = [
    "phase29_4_precision_fusion_teacher_distillation_and_live_recovery_report.md",
    "phase29_4_local_evidence_inventory.csv",
    "phase29_4_teacher_canonical_sets.csv",
    "phase29_4_teacher_vs_floor_diff.csv",
    "phase29_4_entry_time_feature_table.csv",
    "phase29_4_teacher_distilled_rules.csv",
    "phase29_4_variant_c_live_rebuild_results.csv",
    "phase29_4_variant_b_rescue_rebuild_results.csv",
    "phase29_4_pf12_live_router_trade_log.csv",
    "phase29_4_pf12_live_router_metrics.csv",
    "phase29_4_pf12_trade_match_gap_audit.csv",
    "phase29_4_dirty_pf8_recovery_results.csv",
    "phase29_4_final_benchmark_comparison.csv",
    "phase29_4_live_automation_audit.md",
    "phase29_4_audit_manifest.json",
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


def test_phase29_4_required_files_exist():
    for name in REQUIRED:
        assert (REPORTS / name).exists(), f"missing {name}"


def test_phase29_4_manifest_hashes_match_disk():
    manifest = json.loads((REPORTS / "phase29_4_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["final_verdict"] == "PF12_PARTIAL_LIVE_RECOVERY_RULES_FOUND"
    assert "antigravity_workspace" in manifest
    for name, meta in manifest["files"].items():
        assert name != "phase29_4_audit_manifest.json"
        assert file_hash(REPORTS / name) == meta["sha256"]


def test_phase29_4_report_uses_precision_fusion_boundary():
    report = (REPORTS / "phase29_4_precision_fusion_teacher_distillation_and_live_recovery_report.md").read_text(encoding="utf-8")
    assert "PF means Precision Fusion" in report
    assert "NOT_REAL_CAPITAL_READY" in report
    assert "teacher labels analysis-only" in report


def test_phase29_4_teacher_canonical_sets_are_row_computed():
    rows = read_csv("phase29_4_teacher_canonical_sets.csv")
    assert len(rows) == 3
    by_name = {r["teacher_set"]: r for r in rows}
    assert by_name["Variant B teacher"]["metrics_computed_from_trade_rows"] == "YES"
    assert by_name["Variant C teacher"]["metrics_computed_from_trade_rows"] == "YES"
    assert by_name["PF1.2 teacher"]["metrics_computed_from_trade_rows"] == "YES"
    assert round(float(by_name["Variant B teacher"]["net_pnl"]), 2) == 19589.91
    assert round(float(by_name["Variant C teacher"]["net_pnl"]), 2) == 20455.48
    assert round(float(by_name["PF1.2 teacher"]["net_pnl"]), 2) == 21684.99
    assert int(by_name["PF1.2 teacher"]["trades"]) == 325


def test_phase29_4_teacher_vs_floor_diff_exists_and_records_gap():
    rows = read_csv("phase29_4_teacher_vs_floor_diff.csv")
    summaries = [r for r in rows if r["row_type"] == "summary"]
    assert len(summaries) == 3
    pf12 = next(r for r in summaries if r["system"] == "PF1.2 teacher")
    assert int(pf12["floor_trades"]) > int(pf12["teacher_trades"])
    assert int(pf12["teacher_missing_exact"]) > 0
    assert int(pf12["nearby_time_side_matches"]) > 0


def test_phase29_4_entry_feature_table_has_no_later_outcome_columns():
    rows = read_csv("phase29_4_entry_time_feature_table.csv")
    assert rows
    forbidden = {"net_pnl", "gross_pnl", "r_multiple", "mfe", "mae", "winner", "loser", "outcome", "month_pnl"}
    headers = {h.lower() for h in rows[0].keys()}
    assert not (headers & forbidden)
    assert "expected_r_signal" in headers
    assert "has_btc_5m_antigravity" in headers


def test_phase29_4_distilled_rules_have_no_ids_dates_or_outcome_labels():
    rows = read_csv("phase29_4_teacher_distilled_rules.csv")
    assert rows
    text = "\n".join(json.dumps(r, sort_keys=True) for r in rows).lower()
    for forbidden in ["trade_id", "selected_trade", "2020-", "2021-", "2022-", "2023-", "2024-", "2025-", "2026-", "future_", "is_winner", "outcome"]:
        assert forbidden not in text
    assert all(r["live_known_validity"] == "YES" for r in rows)


def test_phase29_4_variant_rebuild_results_exist():
    c_rows = read_csv("phase29_4_variant_c_live_rebuild_results.csv")
    b_rows = read_csv("phase29_4_variant_b_rescue_rebuild_results.csv")
    assert len(c_rows) >= 3
    assert len(b_rows) >= 3
    assert all(r["status"] == "ENGINE_EXECUTED_LIVE_KNOWN_REBUILD" for r in c_rows)
    assert all(r["status"] == "ENGINE_EXECUTED_LIVE_KNOWN_REBUILD" for r in b_rows)
    assert all(r["trade_log_hash"] for r in c_rows + b_rows)


def test_phase29_4_pf12_live_router_metrics_are_computed_from_trade_log():
    trades = read_csv("phase29_4_pf12_live_router_trade_log.csv")
    metrics = read_csv("phase29_4_pf12_live_router_metrics.csv")
    live = next(r for r in metrics if r["system"] == "PF1.2 distilled live router")
    teacher = next(r for r in metrics if r["system"] == "PF1.2 protected teacher")
    assert live["status"] == "ENGINE_EXECUTED_LIVE_KNOWN_PARTIAL_RECOVERY"
    assert teacher["status"] == "TEACHER_REFERENCE_NOT_EXECUTABLE_PROOF"
    assert int(live["trades"]) == len(trades)
    assert abs(sum(float(r["net_pnl"]) for r in trades) - float(live["net_pnl"])) < 0.01
    assert round(float(live["net_pnl"]), 2) != round(float(teacher["net_pnl"]), 2)


def test_phase29_4_runner_has_no_forced_metric_logic():
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
        "forced_pnl",
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


def test_phase29_4_trade_gap_and_live_audit_not_real_capital_ready():
    gap = read_csv("phase29_4_pf12_trade_match_gap_audit.csv")
    summary = next(r for r in gap if r["row_type"] == "summary")
    assert summary["status"] == "PARTIAL_RECOVERY"
    assert int(summary["time_side_matches"]) > 0
    assert int(summary["time_side_matches"]) < int(summary["teacher_trades"])

    live_audit = (REPORTS / "phase29_4_live_automation_audit.md").read_text(encoding="utf-8")
    assert "NOT_REAL_CAPITAL_READY" in live_audit
    assert "no Binance shadow/live execution ledger" in live_audit
