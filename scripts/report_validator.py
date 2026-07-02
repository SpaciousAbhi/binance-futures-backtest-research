#!/usr/bin/env python3
"""
scripts/report_validator.py

Report Validator - Phase 30.1
Scans and validates report files in the reports/ directory to ensure compliance
with proof standards, final verdicts, live status warning, and next phase plans.
Outputs:
  - reports/phase30_1_report_validator_results.csv
"""
import os
import re
import csv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
CSV_PATH = os.path.join(ROOT_DIR, "reports", "phase30_1_report_validator_results.csv")

def validate_report(file_path):
    rel_path = os.path.relpath(file_path, ROOT_DIR)
    
    # Read report content
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return {
            "file": rel_path,
            "verdict_found": "FAIL",
            "benchmark_table_found": "FAIL",
            "live_status_present": "FAIL",
            "next_phase_exists": "FAIL",
            "passed": "FAIL",
            "notes": f"Error reading file: {e}"
        }

    # 1. Check for final verdict
    verdict_patterns = [
        r"(verdict|final verdict)\b",
        r"PHASE\d+_[A-Z0-9_]+",
        r"PF12_MTF_[A-Z0-9_]+"
    ]
    verdict_found = "PASS" if any(re.search(p, content, re.IGNORECASE) for p in verdict_patterns) else "FAIL"

    # 2. Check for benchmark tables
    table_found = "PASS" if "|" in content and re.search(r"\|\s*Benchmark\s*\|", content, re.IGNORECASE) or re.search(r"\|\s*Metric\s*\|", content, re.IGNORECASE) else "FAIL"
    # Fallback check for any markdown table if specifically named headers aren't present
    if table_found == "FAIL":
        # Check if there are at least two lines containing multiple pipes
        pipe_lines = [line for line in content.split("\n") if line.count("|") >= 3]
        if len(pipe_lines) >= 3:
            table_found = "PASS"

    # 3. Check for live status warning
    live_status_present = "PASS" if "NOT_REAL_CAPITAL_READY" in content or "live trading status" in content.lower() else "FAIL"

    # 4. Check for next phase recommendation
    next_phase_exists = "PASS" if "next phase" in content.lower() or "next recommended" in content.lower() or "phase 29.7" in content.lower() or "phase 31" in content.lower() else "FAIL"

    # Overall passed
    passed = "PASS" if (verdict_found == "PASS" and live_status_present == "PASS" and next_phase_exists == "PASS") else "FAIL"
    
    notes = []
    if verdict_found == "FAIL": notes.append("Missing final verdict classification.")
    if table_found == "FAIL": notes.append("Missing benchmark comparison table.")
    if live_status_present == "FAIL": notes.append("Missing NOT_REAL_CAPITAL_READY warning.")
    if next_phase_exists == "FAIL": notes.append("Missing next phase recommendations.")
    
    return {
        "file": rel_path,
        "verdict_found": verdict_found,
        "benchmark_table_found": table_found,
        "live_status_present": live_status_present,
        "next_phase_exists": next_phase_exists,
        "passed": passed,
        "notes": "; ".join(notes) if notes else "All checks pass."
    }

def run_validator():
    results = []
    
    # We validate major markdown reports in reports/
    if os.path.exists(REPORTS_DIR):
        for file in sorted(os.listdir(REPORTS_DIR)):
            if file.endswith(".md"):
                # Skip architecture audit since it is not a phase execution report,
                # or design docs which are helper schemas.
                if "architecture_audit" in file or "design" in file or "schema" in file or "ideas" in file:
                    continue
                full_path = os.path.join(REPORTS_DIR, file)
                results.append(validate_report(full_path))

    # Write results to CSV
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    headers = ["file", "verdict_found", "benchmark_table_found", "live_status_present", "next_phase_exists", "passed", "notes"]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)

    print(f"Report Validator complete. Checked {len(results)} markdown reports.")
    print(f"Report Validation CSV written: {CSV_PATH}")
    return results

if __name__ == "__main__":
    run_validator()
