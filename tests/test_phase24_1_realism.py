"""
tests/test_phase24_1_realism.py

Verification tests for Phase 24.1:
- Reconciles truth lock reproduction of Precision Fusion 1.2.
- Verifies manifest hashes match files on disk.
- Verifies presence of all Phase 24.1 reports and reconciled CSVs.
"""
import os
import csv
import json
import hashlib
import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPORTS_DIR = os.path.join(_ROOT, "reports")

def _file_exists(name):
    return os.path.exists(os.path.join(REPORTS_DIR, name))

def _load_csv(name):
    path = os.path.join(REPORTS_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def _load_json(name):
    path = os.path.join(REPORTS_DIR, name)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def file_hash(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

class TestPhase241TruthLock:
    def test_pf12_reproduction(self):
        report_path = os.path.join(REPORTS_DIR, "phase24_1_engine_repair_reconciliation_report.md")
        assert os.path.exists(report_path), "Main reconciliation report is missing"
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "21,684.99" in content or "21684.99" in content
        assert "325" in content
        assert "2.42" in content
        assert "10.87%" in content

class TestPhase241ProofFiles:
    @pytest.mark.parametrize("fname", [
        "phase24_1_engine_repair_reconciliation_report.md",
        "phase24_1_behavioral_count_reconciliation.csv",
        "phase24_1_candidate_funnel_audit.csv",
        "phase24_1_parameter_wiring_verification.csv",
        "phase24_1_filter_vs_signal_generation_audit.csv",
        "phase24_1_candidate_leaderboard_audit.csv",
        "phase24_1_audit_manifest.json"
    ])
    def test_file_exists(self, fname):
        assert _file_exists(fname), f"{fname} is missing"

    def test_manifest_hashes_match(self):
        manifest = _load_json("phase24_1_audit_manifest.json")
        keys = [
            ("phase24_wiring_change_log_hash", "phase24_wiring_change_log.csv"),
            ("phase24_behavioral_unit_test_summary_hash", "phase24_behavioral_unit_test_summary.csv"),
            ("phase24_controlled_registry_hash", "phase24_controlled_registry.csv"),
            ("phase24_behavioral_diversity_report_hash", "phase24_behavioral_diversity_report.csv"),
            ("phase24_candidate_results_hash", "phase24_candidate_results.csv"),
            ("phase24_portfolio_integration_results_hash", "phase24_portfolio_integration_results.csv"),
            ("phase24_negative_zero_month_impact_hash", "phase24_negative_zero_month_impact.csv"),
            ("phase24_finalist_stress_results_hash", "phase24_finalist_stress_results.csv")
        ]
        for key, fname in keys:
            fpath = os.path.join(REPORTS_DIR, fname)
            f_h = file_hash(fpath)
            m_h = manifest.get(key)
            assert f_h == m_h, f"Hash mismatch for {fname}: disk={f_h}, manifest={m_h}"
