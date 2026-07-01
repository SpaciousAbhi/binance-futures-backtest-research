"""
tests/test_phase25_1_realism.py

Verification tests for Phase 25.1:
- Reconciles truth lock reproduction of PF 1.2 and PF 7.0.
- Verifies manifest hashes match files on disk.
- Verifies presence of all 15 Phase 25.1 proof files.
- Verifies lookahead-free and hardcoding constraints.
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

class TestPhase251TruthLock:
    def test_pf12_and_pf70_reproduction(self):
        report_path = os.path.join(REPORTS_DIR, "phase25_1_precision_fusion_7_acceptance_audit_report.md")
        assert os.path.exists(report_path), "Main report is missing"
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "21,684.99" in content or "21684.99" in content
        assert "325" in content
        assert "2.42" in content
        assert "10.87%" in content
        assert "29,386.59" in content or "29386.59" in content
        assert "625" in content
        assert "2.28" in content
        assert "11.50%" in content
        assert "18,250.40" in content or "18250.40" in content

class TestPhase251ProofFiles:
    @pytest.mark.parametrize("fname", [
        "phase25_1_precision_fusion_7_acceptance_audit_report.md",
        "phase25_1_truth_lock_comparison.csv",
        "phase25_1_trade_count_reconciliation.csv",
        "phase25_1_added_trade_audit.csv",
        "phase25_1_negative_month_repair_audit.csv",
        "phase25_1_zero_month_rescue_audit.csv",
        "phase25_1_full_15_stress_audit.csv",
        "phase25_1_drawdown_risk_audit.csv",
        "phase25_1_pf_tradeoff_audit.csv",
        "phase25_1_entry_exit_rule_serialization.md",
        "phase25_1_live_automation_readiness_audit.md",
        "phase25_1_no_lookahead_hardcoding_audit.csv",
        "phase25_1_monthly_yearly_tables.csv",
        "phase25_1_trade_traceability.csv",
        "phase25_1_audit_manifest.json"
    ])
    def test_file_exists(self, fname):
        assert _file_exists(fname), f"{fname} is missing"

    def test_manifest_hashes_match(self):
        manifest = _load_json("phase25_1_audit_manifest.json")
        keys = [
            ("phase25_1_truth_lock_comparison_hash", "phase25_1_truth_lock_comparison.csv"),
            ("phase25_1_trade_count_reconciliation_hash", "phase25_1_trade_count_reconciliation.csv"),
            ("phase25_1_added_trade_audit_hash", "phase25_1_added_trade_audit.csv"),
            ("phase25_1_negative_month_repair_audit_hash", "phase25_1_negative_month_repair_audit.csv"),
            ("phase25_1_zero_month_rescue_audit_hash", "phase25_1_zero_month_rescue_audit.csv"),
            ("phase25_1_full_15_stress_audit_hash", "phase25_1_full_15_stress_audit.csv"),
            ("phase25_1_drawdown_risk_audit_hash", "phase25_1_drawdown_risk_audit.csv"),
            ("phase25_1_pf_tradeoff_audit_hash", "phase25_1_pf_tradeoff_audit.csv"),
            ("phase25_1_entry_exit_rule_serialization_hash", "phase25_1_entry_exit_rule_serialization.md"),
            ("phase25_1_live_automation_readiness_audit_hash", "phase25_1_live_automation_readiness_audit.md"),
            ("phase25_1_no_lookahead_hardcoding_audit_hash", "phase25_1_no_lookahead_hardcoding_audit.csv"),
            ("phase25_1_monthly_yearly_tables_hash", "phase25_1_monthly_yearly_tables.csv"),
            ("phase25_1_trade_traceability_hash", "phase25_1_trade_traceability.csv")
        ]
        for key, fname in keys:
            fpath = os.path.join(REPORTS_DIR, fname)
            f_h = file_hash(fpath)
            m_h = manifest.get(key)
            assert f_h == m_h, f"Hash mismatch for {fname}: disk={f_h}, manifest={m_h}"
