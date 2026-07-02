import ast
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNNER = ROOT / "scripts" / "phase29_1_truth_first_recovery.py"

REQUIRED = [
    "phase29_1_truth_first_pf8_recovery_report.md",
    "phase29_1_forced_metric_contamination_audit.csv",
    "phase29_1_corrected_benchmark_status.csv",
    "phase29_1_pf12_truth_lock.csv",
    "phase29_1_real_sleeve_idea_inventory.csv",
    "phase29_1_actual_pf8_recompute_baseline.csv",
    "phase29_1_sleeve_standalone_results.csv",
    "phase29_1_reconstruction_ladder.csv",
    "phase29_1_router_conflict_audit.csv",
    "phase29_1_genuine_candidate_registry.csv",
    "phase29_1_genuine_candidate_results.csv",
    "phase29_1_top_100_genuine_candidates.md",
    "phase29_1_genuine_router_trade_log.csv",
    "phase29_1_genuine_router_monthly_table.csv",
    "phase29_1_genuine_router_stress_table.csv",
    "phase29_1_live_known_rule_audit.csv",
    "phase29_1_entry_exit_rulebook.md",
    "phase29_1_corrected_project_status.md",
    "phase29_1_audit_manifest.json",
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


def as_float(row, key):
    return float(row[key])


def test_phase29_1_required_files_exist():
    for name in REQUIRED:
        assert (REPORTS / name).exists(), f"missing {name}"


def test_phase29_1_manifest_hashes_match_disk():
    manifest = json.loads((REPORTS / "phase29_1_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["final_verdict"] == "AUDIT_PARTIAL_PASS_REAL_SLEEVES_FOUND_RESEARCH_ONLY"
    assert "pytest" in manifest
    for name, meta in manifest["files"].items():
        assert name != "phase29_1_audit_manifest.json"
        assert file_hash(REPORTS / name) == meta["sha256"]


def test_phase29_1_pf12_truth_lock_exact():
    row = read_csv("phase29_1_pf12_truth_lock.csv")[0]
    assert row["status"] == "PASS"
    assert round(as_float(row, "net_pnl"), 2) == 21684.99
    assert int(row["trades"]) == 325
    assert round(as_float(row, "profit_factor"), 2) == 2.42
    assert round(as_float(row, "max_dd_pct"), 2) == 10.87
    assert (int(row["positive_months"]), int(row["negative_months"]), int(row["zero_months"])) == (56, 16, 6)
    assert round(as_float(row, "combined_adverse"), 2) == 15922.97


def test_phase29_1_old_forced_metrics_detected_and_invalidated():
    contamination = read_csv("phase29_1_forced_metric_contamination_audit.csv")
    failures = [r for r in contamination if r["risk_level"] == "FAIL"]
    assert failures
    assert any("phase28_runner.py" in r["file"] and "pnl_81" in r["pattern"] for r in failures)

    status = {r["system"]: r["corrected_status"] for r in read_csv("phase29_1_corrected_benchmark_status.csv")}
    assert status["PF1.2"] == "VALID_RECONSTRUCTED_BENCHMARK"
    assert status["PF7.0"] == "INVALID_FORCED_METRIC"
    assert status["PF8.0"] == "INVALID_FORCED_METRIC"
    assert status["PF8.1"] == "INVALID_FORCED_METRIC"


def test_phase29_1_recovery_runner_contains_no_pf8_target_forcing():
    source = RUNNER.read_text(encoding="utf-8")
    for forbidden in ["29386.59", "30580.40", "31250.80", ".sample("]:
        assert forbidden not in source
    for forbidden in ["is_winner", "future_pnl", "future_mfe", "future_mae", "selected_trade_ids"]:
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
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                assigned.add(target.id)
    assert not (assigned & forbidden_targets)


def test_phase29_1_candidate_registry_is_truthfully_timeboxed():
    registry = read_csv("phase29_1_genuine_candidate_registry.csv")
    results = read_csv("phase29_1_genuine_candidate_results.csv")
    assert len(registry) >= 1000
    hashes = [r["parameter_hash"] for r in registry]
    assert len(hashes) == len(set(hashes))

    executed = [r for r in results if r["status"] == "EXECUTED_ENGINE"]
    unexecuted = [r for r in results if r["status"] == "REGISTERED_NOT_EXECUTED_TIMEBOXED"]
    assert executed
    assert unexecuted
    assert all(r["net_pnl"] == "" and r["trade_log_hash"] == "" for r in unexecuted)
    assert all(r["beats_pf12"] == "NO" for r in executed)


def test_phase29_1_router_trade_log_monthly_and_stress_are_consistent():
    results = read_csv("phase29_1_genuine_candidate_results.csv")
    best = max((r for r in results if r["status"] == "EXECUTED_ENGINE"), key=lambda r: float(r["score"]))
    trades = read_csv("phase29_1_genuine_router_trade_log.csv")
    monthly = read_csv("phase29_1_genuine_router_monthly_table.csv")
    stress = read_csv("phase29_1_genuine_router_stress_table.csv")

    assert int(best["trades"]) == len(trades)
    trade_pnl = sum(float(r["net_pnl"]) for r in trades)
    monthly_pnl = sum(float(r["pnl"]) for r in monthly)
    assert abs(trade_pnl - monthly_pnl) < 0.01
    assert round(trade_pnl, 6) == round(float(best["net_pnl"]), 6)
    assert len(stress) == 15
    assert {r["scenario"] for r in stress} >= {"normal", "combined adverse", "combined adverse stale cancel"}


def test_phase29_1_dirty_pf8_recompute_is_not_promoted():
    row = read_csv("phase29_1_actual_pf8_recompute_baseline.csv")[0]
    assert row["baseline_variant"] == "dirty_pf8x_no_forced_delta_no_metric_assignment"
    assert round(as_float(row, "profit_factor"), 2) < 2.38
    assert round(as_float(row, "combined_adverse"), 2) < 20150.80


def test_phase29_1_live_audit_and_rulebook_exist():
    rows = read_csv("phase29_1_live_known_rule_audit.csv")
    assert rows
    assert all(r["status"] in {"PASS", "WARNING", "FAIL"} for r in rows)
    assert any(r["rule_area"] == "real capital readiness" and r["status"] == "FAIL" for r in rows)
    rulebook = (REPORTS / "phase29_1_entry_exit_rulebook.md").read_text(encoding="utf-8")
    assert "closed-candle" in rulebook
    assert "not real-capital ready" in rulebook
