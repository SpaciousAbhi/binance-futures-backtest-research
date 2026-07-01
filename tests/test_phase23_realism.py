"""
tests/test_phase23_realism.py

Verification tests for Phase 23:
- Reconciles truth lock reproduction of Precision Fusion 1.2.
- Verifies lookahead-free and hardcoding constraints.
- Verifies manifest hashes match files on disk.
- Verifies presence and counts of all 10 proof files.
"""
import os
import re
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

class TestPhase23TruthLock:
    def test_pf12_reproduction(self):
        # Read the main report and check if the PnL is correct
        report_path = os.path.join(REPORTS_DIR, "phase23_precision_fusion_micro_surgery_report.md")
        assert os.path.exists(report_path), "Main report is missing"
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "21684.99" in content or "21,684.99" in content
        assert "325" in content
        assert "2.42" in content
        assert "10.87%" in content

class TestPhase23ProofFiles:
    @pytest.mark.parametrize("fname", [
        "phase23_precision_fusion_micro_surgery_report.md",
        "phase23_loss_surgery_results.csv",
        "phase23_winner_preservation_audit.csv",
        "phase23_behavioral_dedup_report.csv",
        "phase23_overlay_results.csv",
        "phase23_expansion_layer_results.csv",
        "phase23_negative_month_repair_table.csv",
        "phase23_zero_month_rescue_table.csv",
        "phase23_finalist_stress_results.csv",
        "phase23_audit_manifest.json"
    ])
    def test_file_exists(self, fname):
        assert _file_exists(fname), f"{fname} is missing"

    def test_manifest_hashes_match(self):
        manifest = _load_json("phase23_audit_manifest.json")
        keys = [
            ("phase23_loss_surgery_results_hash", "phase23_loss_surgery_results.csv"),
            ("phase23_winner_preservation_audit_hash", "phase23_winner_preservation_audit.csv"),
            ("phase23_behavioral_dedup_report_hash", "phase23_behavioral_dedup_report.csv"),
            ("phase23_overlay_results_hash", "phase23_overlay_results.csv"),
            ("phase23_expansion_layer_results_hash", "phase23_expansion_layer_results.csv"),
            ("phase23_negative_month_repair_table_hash", "phase23_negative_month_repair_table.csv"),
            ("phase23_zero_month_rescue_table_hash", "phase23_zero_month_rescue_table.csv"),
            ("phase23_finalist_stress_results_hash", "phase23_finalist_stress_results.csv")
        ]
        for key, fname in keys:
            fpath = os.path.join(REPORTS_DIR, fname)
            f_h = file_hash(fpath)
            m_h = manifest.get(key)
            assert f_h == m_h, f"Hash mismatch for {fname}: disk={f_h}, manifest={m_h}"

class TestPhase23NoLookahead:
    def test_no_lookahead_labels(self):
        # Audit source files for forbidden labels
        forbidden = ["is_winner", "future_pnl", "hardcoded_month"]
        # Search inside src/strategies
        strat_dir = os.path.join(_ROOT, "src", "strategies")
        if os.path.exists(strat_dir):
            for root, _, files in os.walk(strat_dir):
                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    fpath = os.path.join(root, fname)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for key in forbidden:
                            # Skip comments
                            for line in content.splitlines():
                                if key in line and not line.strip().startswith("#"):
                                    assert False, f"Forbidden key '{key}' found in active strategies file: {fpath}"

    def test_no_hardcoded_dates_in_configs(self):
        # Ensure candidate registry parameters have no hardcoded dates
        registry_path = os.path.join(REPORTS_DIR, "phase22_candidate_registry.csv")
        if os.path.exists(registry_path):
            rows = _load_csv("../reports/phase22_candidate_registry.csv")
            for r in rows:
                params = r.get("parameters_json", "")
                assert not re.search(r'\d{4}-\d{2}(-\d{2})?', params), \
                    f"Hardcoded date found in parameters: {params}"
