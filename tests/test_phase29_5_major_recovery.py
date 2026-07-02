import ast
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNNER = ROOT / "scripts" / "phase29_5_major_recovery.py"

REQUIRED = [
    "phase29_5_major_precision_fusion_breakthrough_report.md",
    "phase29_5_local_evidence_map.csv",
    "phase29_5_mtf_data_alignment_audit.csv",
    "phase29_5_teacher_mtf_trigger_match.csv",
    "phase29_5_variant_c_mtf_results.csv",
    "phase29_5_variant_b_rescue_mtf_results.csv",
    "phase29_5_pf12_executable_router_results.csv",
    "phase29_5_pf12_executable_router_trade_log.csv",
    "phase29_5_pf12_trade_match_gap_audit.csv",
    "phase29_5_dirty_pf8_upgrade_results.csv",
    "phase29_5_candidate_registry.csv",
    "phase29_5_candidate_results.csv",
    "phase29_5_benchmark_stack_comparison.csv",
    "phase29_5_live_automation_audit.md",
    "phase29_5_audit_manifest.json",
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


def test_phase29_5_required_files_exist():
    for name in REQUIRED:
        assert (REPORTS / name).exists(), f"missing {name}"


def test_phase29_5_manifest_hashes_match_disk():
    manifest = json.loads((REPORTS / "phase29_5_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["final_verdict"] == "PF12_MAJOR_MTF_RECOVERY_PROGRESS_PF8_RESEARCH_CONTINUES"
    assert manifest["execution_limit"] == 300
    for name, meta in manifest["files"].items():
        assert name != "phase29_5_audit_manifest.json"
        assert file_hash(REPORTS / name) == meta["sha256"]


def test_phase29_5_runner_has_no_forced_metric_or_fake_sampling_logic():
    source = RUNNER.read_text(encoding="utf-8")
    for forbidden in [
        "29386.59",
        "30580.40",
        "31250.80",
        "21684.99",
        "19589.91",
        "20455.48",
        ".sample(",
        "is_winner",
        "future_pnl",
        "future_r",
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


def test_phase29_5_mtf_alignment_has_no_leakage_flag():
    rows = read_csv("phase29_5_mtf_data_alignment_audit.csv")
    by_tf = {r["timeframe"]: r for r in rows}
    assert by_tf["1h"]["exists"] == "YES"
    assert by_tf["15m"]["exists"] == "YES"
    assert by_tf["5m"]["exists"] == "YES"
    assert by_tf["cross_timeframe"]["leakage_check"] == "PASS_NO_TRIGGER_BEFORE_SETUP_CLOSE"
    assert all(int(by_tf[tf]["duplicate_candles"]) == 0 for tf in ["1h", "15m", "5m"])


def test_phase29_5_teacher_mtf_trigger_match_is_analysis_only():
    rows = read_csv("phase29_5_teacher_mtf_trigger_match.csv")
    assert len(rows) == 325
    categories = {r["match_category"] for r in rows}
    assert categories
    assert all(r["used_in_live_router"] == "NO_TEACHER_ANALYSIS_ONLY" for r in rows)


def test_phase29_5_variant_and_pf12_results_are_engine_rows():
    c_rows = read_csv("phase29_5_variant_c_mtf_results.csv")
    b_rows = read_csv("phase29_5_variant_b_rescue_mtf_results.csv")
    pf12_rows = read_csv("phase29_5_pf12_executable_router_results.csv")
    assert c_rows and b_rows and pf12_rows
    assert all(r["status"] == "ENGINE_EXECUTED_MTF_C_REBUILD" for r in c_rows)
    assert all(r["status"] == "ENGINE_EXECUTED_MTF_B_RESCUE_REBUILD" for r in b_rows)
    assert pf12_rows[0]["status"] == "ENGINE_EXECUTED_PF12_MTF_ROUTER"
    assert pf12_rows[0]["pf12_recovery_status"] == "PARTIAL_RECOVERY"


def test_phase29_5_candidate_registry_and_execution_accounting():
    registry = read_csv("phase29_5_candidate_registry.csv")
    results = read_csv("phase29_5_candidate_results.csv")
    assert len(registry) == 5000
    assert len(results) == 5000
    hashes = [r["candidate_hash"] for r in registry]
    assert len(hashes) == len(set(hashes))
    executed = [r for r in results if r["status"] == "EXECUTED_ENGINE"]
    unexecuted = [r for r in results if r["status"] == "REGISTERED_NOT_EXECUTED_TIMEBOXED"]
    assert len(executed) == 300
    assert len(unexecuted) == 4700
    assert all(r["net_pnl"] != "" and r["trade_log_hash"] != "" for r in executed)
    assert all(r["net_pnl"] == "" and r["trade_log_hash"] == "" for r in unexecuted)


def test_phase29_5_pf12_router_metrics_reconcile_with_trade_log():
    pf12_rows = read_csv("phase29_5_pf12_executable_router_results.csv")
    best = pf12_rows[0]
    trades = read_csv("phase29_5_pf12_executable_router_trade_log.csv")
    assert int(best["trades"]) == len(trades)
    pnl = sum(float(r["net_pnl"]) for r in trades)
    assert abs(pnl - float(best["net_pnl"])) < 0.01
    gap = read_csv("phase29_5_pf12_trade_match_gap_audit.csv")
    summary = next(r for r in gap if r["row_type"] == "summary")
    assert summary["status"] == "PARTIAL_RECOVERY"
    assert int(summary["time_side_matches"]) > 0


def test_phase29_5_live_audit_not_real_capital_ready():
    text = (REPORTS / "phase29_5_live_automation_audit.md").read_text(encoding="utf-8")
    assert "NOT_REAL_CAPITAL_READY" in text
    assert "no Binance shadow execution" in text
