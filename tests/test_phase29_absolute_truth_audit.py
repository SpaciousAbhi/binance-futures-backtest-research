import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

REQUIRED = [
    "phase29_absolute_truth_audit_full_project_report.md",
    "phase29_project_inventory.csv",
    "phase29_data_integrity_audit.csv",
    "phase29_benchmark_reproduction.csv",
    "phase29_fusion_architecture_map.csv",
    "phase29_strategy_rulebook.md",
    "phase29_lookahead_hardcoding_audit.csv",
    "phase29_multi_asset_monthly_metrics.csv",
    "phase29_cross_asset_summary.csv",
    "phase29_stress_torture_results.csv",
    "phase29_live_execution_readiness.csv",
    "phase29_security_operational_safety.csv",
    "phase29_statistical_robustness.csv",
    "phase29_audit_manifest.json",
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


def test_phase29_required_files_exist():
    for name in REQUIRED:
        assert (REPORTS / name).exists(), f"missing {name}"


def test_phase29_manifest_hashes_match_disk():
    manifest = json.loads((REPORTS / "phase29_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["final_verdict"] == "AUDIT_FAIL_LOOKAHEAD_OR_HARDCODING_FOUND"
    for name, meta in manifest["files"].items():
        assert name != "phase29_audit_manifest.json"
        assert file_hash(REPORTS / name) == meta["sha256"]


def test_phase29_benchmark_rejects_pf81():
    rows = read_csv("phase29_benchmark_reproduction.csv")
    pf81 = next(r for r in rows if r["strategy"] == "PF8.1")
    assert pf81["status"] == "UNREPRODUCIBLE"
    assert "profit_factor" in pf81["drift"]
    assert "combined_adverse" in pf81["drift"]


def test_phase29_data_matrix_records_missing_required_files():
    rows = read_csv("phase29_data_integrity_audit.csv")
    missing = [r for r in rows if r["status"].startswith("MISSING")]
    assert missing, "audit should record missing required data files"
    assert any(r["asset"] == "ETHUSDT.P" and r["timeframe"] == "5m" for r in missing)


def test_phase29_hardcoding_scan_has_failures():
    rows = read_csv("phase29_lookahead_hardcoding_audit.csv")
    failures = [r for r in rows if r["classification"] == "FAIL"]
    assert failures, "expected hardcoding failures in phase runners"
    assert any("phase28_runner.py" in r["file"] and "pnl_81" in r["pattern"] for r in failures)


def test_phase29_live_readiness_not_real_capital_ready():
    rows = read_csv("phase29_live_execution_readiness.csv")
    assert rows
    assert all(r["classification"] == "NOT_REAL_CAPITAL_READY" for r in rows)
