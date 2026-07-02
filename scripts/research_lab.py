#!/usr/bin/env python3
"""
scripts/research_lab.py

Unified Research Lab CLI Control Panel - Phase 30.1
Supports status checks, memory integrity checks, data integrity checks,
code audit engines, benchmark listing, and next phase routing.
"""
import os
import sys
import argparse
import csv
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_cmd(cmd_list):
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True)
        return res.stdout, res.returncode
    except Exception as e:
        return f"Error executing command: {e}", 1

def handle_status():
    print("=" * 60)
    print("PRECISION FUSION RESEARCH LAB STATUS")
    print("=" * 60)
    handoff_path = os.path.join(ROOT_DIR, "project_memory", "CURRENT_HANDOFF.md")
    if os.path.exists(handoff_path):
        with open(handoff_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Find latest phase section
        print("Latest Completed Phase Context:")
        found_section = False
        for line in lines:
            if line.startswith("## Latest Completed Phase"):
                found_section = True
            if found_section:
                if line.startswith("---") and len(line) < 10:
                    break
                print(line.strip())
    else:
        print("CURRENT_HANDOFF.md missing.")
        
    print("\nLive Trading Status:")
    print("  [STATUS] NOT_REAL_CAPITAL_READY")
    print("  (Shadow mode trading, order lifecycle verification, and exchange API tests pending.)")
    print("=" * 60)

def handle_memory_check():
    print("Running Project Memory Integrity Audit...")
    check_script = os.path.join(ROOT_DIR, "scripts", "check_project_memory.py")
    if os.path.exists(check_script):
        out, code = run_cmd([sys.executable, check_script])
        print(out)
        sys.exit(code)
    else:
        print("scripts/check_project_memory.py is missing.")
        sys.exit(1)

def handle_data_check():
    print("Running Data Registry Integrity Checks...")
    processed_dir = os.path.join(ROOT_DIR, "data", "processed")
    if not os.path.exists(processed_dir):
        print("  [FAIL] data/processed directory is missing.")
        sys.exit(1)
        
    expected_files = [
        "BTCUSDT_1h_processed.csv",
        "BTCUSDT_15m_processed.csv",
        "ETHUSDT_1h_processed.csv",
        "BNBUSDT_1h_processed.csv",
        "SOLUSDT_1h_processed.csv"
    ]
    
    all_pass = True
    for f in expected_files:
        fpath = os.path.join(processed_dir, f)
        if os.path.exists(fpath):
            sz_kb = round(os.path.getsize(fpath) / 1024, 1)
            # Basic CSV check
            try:
                with open(fpath, "r", encoding="utf-8") as file:
                    header = file.readline().strip()
                print(f"  [PASS] {f} exists ({sz_kb} KB). Schema: {header[:80]}...")
            except Exception as e:
                print(f"  [FAIL] {f} exists but failed to read: {e}")
                all_pass = False
        else:
            # Note: BTCUSDT 5m processed data is gitignored, check local existence but don't fail build if not in git
            if "5m" in f:
                print(f"  [WARN] {f} missing locally (gitignored).")
            else:
                print(f"  [FAIL] Required file {f} is missing.")
                all_pass = False
                
    if all_pass:
        print("Result: DATA_REGISTRY_VERIFIED")
        sys.exit(0)
    else:
        print("Result: DATA_REGISTRY_CORRUPT")
        sys.exit(1)

def handle_audit():
    print("Executing Codebase Lookahead & Hardcoding Audit...")
    audit_script = os.path.join(ROOT_DIR, "scripts", "audit_engine.py")
    if os.path.exists(audit_script):
        out, code = run_cmd([sys.executable, audit_script])
        print(out)
        # Check if there were any critical failures (not just ALLOWED_HISTORICAL_CONTEXT)
        csv_path = os.path.join(ROOT_DIR, "reports", "phase30_1_audit_engine_scan.csv")
        critical_violations = 0
        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["risk_level"] == "CRITICAL" and row["classification"] != "ALLOWED_HISTORICAL_CONTEXT":
                        print(f"  [VIOLATION] {row['file']}:{row['line']} -> {row['classification']} ({row['context']})")
                        critical_violations += 1
        if critical_violations > 0:
            print(f"Result: AUDIT_FAILED ({critical_violations} critical violations found).")
            sys.exit(1)
        else:
            print("Result: AUDIT_PASSED (no active critical violations found).")
            sys.exit(0)
    else:
        print("scripts/audit_engine.py is missing.")
        sys.exit(1)

def handle_list_phases():
    timeline_path = os.path.join(ROOT_DIR, "project_memory", "PHASE_HISTORY_TIMELINE.md")
    if os.path.exists(timeline_path):
        with open(timeline_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(content)
    else:
        print("PHASE_HISTORY_TIMELINE.md missing.")

def handle_list_benchmarks():
    registry_path = os.path.join(ROOT_DIR, "project_memory", "BENCHMARK_REGISTRY.csv")
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for idx, row in enumerate(reader):
                if idx == 0:
                    print("-" * 110)
                    print(f"{row[0]:<35} | {row[1]:<25} | {row[2]:<10} | {row[3]:<8} | {row[4]:<8}")
                    print("-" * 110)
                else:
                    print(f"{row[0]:<35} | {row[1]:<25} | {row[2]:<10} | {row[3]:<8} | {row[4]:<8}")
            print("-" * 110)
    else:
        print("BENCHMARK_REGISTRY.csv missing.")

def handle_validate_report(report_file):
    print(f"Validating format compliance of report: {report_file}")
    validator_script = os.path.join(ROOT_DIR, "scripts", "report_validator.py")
    if os.path.exists(validator_script):
        # We can dynamically run validation logic on the specific file
        from report_validator import validate_report as run_val
        res = run_val(os.path.join(ROOT_DIR, report_file))
        print(json.dumps(res, indent=2))
        if res["passed"] == "PASS":
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("scripts/report_validator.py is missing.")
        sys.exit(1)

def handle_hash_artifacts():
    print("Artifact Hash Audit:")
    manifest_path = os.path.join(ROOT_DIR, "reports", "phase30_1_audit_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Phase {data.get('phase')} Manifest:")
        for name, info in data.get("files", {}).items():
            print(f"  {name:<60} | SHA-256: {info.get('sha256_12')} | Size: {info.get('size_kb')} KB")
    else:
        print("No active manifest found. Manifests are generated at end of phases.")

def handle_next_phase():
    print("=" * 60)
    print("NEXT PHASE ROUTING INFORMATION")
    print("=" * 60)
    next_phase_path = os.path.join(ROOT_DIR, "project_memory", "NEXT_PHASE_PLAN.md")
    if os.path.exists(next_phase_path):
        with open(next_phase_path, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("NEXT_PHASE_PLAN.md is missing.")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Research Lab CLI Control Panel")
    parser.add_argument("command", choices=[
        "status", "memory-check", "data-check", "audit",
        "list-phases", "list-benchmarks", "validate-report",
        "hash-artifacts", "next-phase"
    ], help="Command to run")
    parser.add_argument("argument", nargs="?", help="Optional file argument for validate-report")

    args = parser.parse_args()

    if args.command == "status":
        handle_status()
    elif args.command == "memory-check":
        handle_memory_check()
    elif args.command == "data-check":
        handle_data_check()
    elif args.command == "audit":
        handle_audit()
    elif args.command == "list-phases":
        handle_list_phases()
    elif args.command == "list-benchmarks":
        handle_list_benchmarks()
    elif args.command == "validate-report":
        if not args.argument:
            print("Error: validate-report requires a file path argument.")
            sys.exit(1)
        handle_validate_report(args.argument)
    elif args.command == "hash-artifacts":
        handle_hash_artifacts()
    elif args.command == "next-phase":
        handle_next_phase()

if __name__ == "__main__":
    main()
