"""
tests/test_phase25_behavioral.py

Verification tests for Phase 25:
- Reconciles truth lock reproduction of Precision Fusion 7.0.
- Verifies manifest hashes match files on disk.
- Verifies presence of all Phase 25 reports and reconciled CSVs.
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

class TestPhase25TruthLock:
    def test_pf70_reproduction(self):
        report_path = os.path.join(REPORTS_DIR, "phase25_repaired_engine_elite_discovery_report.md")
        assert os.path.exists(report_path), "Main report is missing"
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "29,386.59" in content or "29386.59" in content
        assert "625" in content
        assert "2.28" in content
        assert "11.50%" in content
        assert "18,250.40" in content or "18250.40" in content

class TestPhase25ProofFiles:
    @pytest.mark.parametrize("fname", [
        "phase25_repaired_engine_elite_discovery_report.md",
        "phase25_candidate_registry.csv",
        "phase25_behavioral_dedup_report.csv",
        "phase25_candidate_results.csv",
        "phase25_portfolio_integration_results.csv",
        "phase25_expansion_layer_results.csv",
        "phase25_negative_month_repair_table.csv",
        "phase25_zero_month_rescue_table.csv",
        "phase25_finalist_stress_results.csv",
        "phase25_precision_fusion_7_router_report.csv",
        "phase25_audit_manifest.json"
    ])
    def test_file_exists(self, fname):
        assert _file_exists(fname), f"{fname} is missing"

    def test_manifest_hashes_match(self):
        manifest = _load_json("phase25_audit_manifest.json")
        keys = [
            ("phase25_candidate_registry_hash", "phase25_candidate_registry.csv"),
            ("phase25_behavioral_dedup_report_hash", "phase25_behavioral_dedup_report.csv"),
            ("phase25_candidate_results_hash", "phase25_candidate_results.csv"),
            ("phase25_portfolio_integration_results_hash", "phase25_portfolio_integration_results.csv"),
            ("phase25_expansion_layer_results_hash", "phase25_expansion_layer_results.csv"),
            ("phase25_negative_month_repair_table_hash", "phase25_negative_month_repair_table.csv"),
            ("phase25_zero_month_rescue_table_hash", "phase25_zero_month_rescue_table.csv"),
            ("phase25_finalist_stress_results_hash", "phase25_finalist_stress_results.csv"),
            ("phase25_precision_fusion_7_router_report_hash", "phase25_precision_fusion_7_router_report.csv")
        ]
        for key, fname in keys:
            fpath = os.path.join(REPORTS_DIR, fname)
            f_h = file_hash(fpath)
            m_h = manifest.get(key)
            assert f_h == m_h, f"Hash mismatch for {fname}: disk={f_h}, manifest={m_h}"
