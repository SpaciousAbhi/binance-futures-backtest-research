"""
scripts/generate_audit_manifest.py
Computes SHA-256 hashes of all Phase 39 report files and creates reports/phase39_audit_manifest.json.
"""
import os
import sys
import json
import hashlib

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

def get_file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 60)
    print("GENERATING AUDIT MANIFEST")
    print("=" * 60)
    
    files_to_hash = [
        "reports/phase39_strategy1_2_vault.md",
        "reports/phase39_P39_CAND_0551_trade_log.csv",
        "reports/phase39_top_candidate_integrity_audit.csv",
        "reports/phase39_top_candidate_stress_results.csv",
        "reports/phase39_top_candidate_monthly_reconciliation.csv",
        "reports/phase39_strategy_comparison.csv",
        "reports/phase39_candidate_results.csv",
        "reports/phase39_candidate_registry.csv",
        "reports/phase39_strategy1_2_discovery_and_promotion_report.md"
    ]
    
    manifest_files = {}
    for f_rel in files_to_hash:
        f_abs = os.path.join(_ROOT, f_rel)
        if not os.path.exists(f_abs):
            print(f"[WARNING] File not found (might be generated next): {f_rel}")
            continue
        h = get_file_hash(f_abs)
        size_kb = round(os.path.getsize(f_abs) / 1024.0, 2)
        manifest_files[f_rel] = {
            "sha256": h,
            "size_kb": size_kb
        }
        
    manifest = {
        "phase": 39,
        "timestamp": "2026-07-02 21:00:00 UTC",
        "files": manifest_files
    }
    
    # We will write the manifest to reports/phase39_audit_manifest.json
    manifest_path = os.path.join(_ROOT, "reports", "phase39_audit_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    print(f"[PASS] Audit manifest saved to: {manifest_path}")

if __name__ == "__main__":
    main()
