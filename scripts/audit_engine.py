#!/usr/bin/env python3
"""
scripts/audit_engine.py

Static analysis tool that scans the codebase for lookahead bias, forced metrics,
hardcoding, and fake strategy expansion patterns.
Outputs:
  - reports/phase30_1_audit_engine_scan.csv
"""
import os
import re
import csv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(ROOT_DIR, "reports", "phase30_1_audit_engine_scan.csv")

# Regular expression patterns for static checks
PATTERNS = {
    "FORCED_PNL": re.compile(r"(\bdiff_pnl\s*=|net_pnl\.sum\(\)\s*\+=\s*|pnl_81_calc\s*=\s*pnl_81|pnl_81\s*=\s*\d+\.\d+)"),
    "FORCED_PF": re.compile(r"(\bprofit_factor\s*=\s*\d+\.\d+|\bpf_calc\s*=\s*\d+\.\d+)"),
    "FORCED_DD": re.compile(r"(\bmax_drawdown\s*=\s*\d+\.\d+)"),
    "VERDICT_HARDCODING": re.compile(r"verdict\s*=\s*['\"]PASS_[A-Z0-9_]+['\"]"),
    "SAMPLE_REPLACE": re.compile(r"\.sample\s*\(.*replace\s*=\s*True"),
    "IS_WINNER_LIVE": re.compile(r"\bis_winner\b"),
    "FUTURE_PNL": re.compile(r"\bfuture_pnl\b"),
    "FUTURE_RETURN": re.compile(r"\bfuture_return\b"),
    "FUTURE_MFE": re.compile(r"\bfuture_mfe\b"),
    "FUTURE_MAE": re.compile(r"\bfuture_mae\b"),
    "HARDCODED_TRADE_ID": re.compile(r"trade_id\s*==\s*\d+"),
    "HARDCODED_MONTH_REPAIR": re.compile(r"['\"](20\d{2}-\d{2})['\"]\s*in\s*.*skip"),
}

def scan_file(file_path):
    rel_path = os.path.relpath(file_path, ROOT_DIR)
    results = []

    # Read file line by line
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line or clean_line.startswith("#"):
                    continue  # Ignore comment lines
                
                for name, pattern in PATTERNS.items():
                    m = pattern.search(clean_line)
                    if m:
                        matched_text = m.group(0)
                        
                        # Determine classification and risk level
                        risk_level = "WARNING"
                        classification = "WARNING"
                        rec = "Review pattern for lookahead or hardcoding."

                        # Specific Rule-based classification
                        if name in ["FORCED_PNL", "FORCED_PF", "FORCED_DD"]:
                            classification = "FAIL_FORCED_METRIC"
                            risk_level = "CRITICAL"
                            rec = "Do not hardcode or mutate computed backtest metrics."
                        elif name == "VERDICT_HARDCODING":
                            classification = "FAIL_FORCED_METRIC"
                            risk_level = "CRITICAL"
                            rec = "Ensure final verdicts are dynamically computed from backtest results."
                        elif name == "SAMPLE_REPLACE":
                            classification = "FAIL_FAKE_EXPANSION"
                            risk_level = "CRITICAL"
                            rec = "Avoid duplicating trades using sample(replace=True) to pad candidate lists."
                        elif name in ["FUTURE_PNL", "FUTURE_RETURN", "FUTURE_MFE", "FUTURE_MAE", "IS_WINNER_LIVE"]:
                            if "src/strategies/" in rel_path:
                                classification = "FAIL_LIVE_PATH_VIOLATION"
                                risk_level = "CRITICAL"
                                rec = "Forbidden lookahead variable inside live strategy class."
                            else:
                                classification = "FAIL_LOOKAHEAD_RISK"
                                risk_level = "HIGH"
                                rec = "Lookahead variable in research script. Limit usage to offline diagnostics only."
                        elif name in ["HARDCODED_TRADE_ID", "HARDCODED_MONTH_REPAIR"]:
                            classification = "FAIL_LOOKAHEAD_RISK"
                            risk_level = "HIGH"
                            rec = "Do not hardcode parameters to specific trade IDs or dates."

                        # Normalize path separator for checks
                        norm_path = rel_path.replace(os.sep, "/")
                        is_historical_runner = "phase" in norm_path.lower()
                        is_test_file = norm_path.startswith("tests/")
                        
                        if is_historical_runner:
                            classification = "ALLOWED_HISTORICAL_CONTEXT"
                            risk_level = "INFO"
                            rec = "Historical context. Reference only; do not copy logic into new strategies."
                        elif is_test_file:
                            classification = "ALLOWED_HISTORICAL_CONTEXT"
                            risk_level = "INFO"
                            rec = "Test validation check pattern."

                        results.append({
                            "file": rel_path,
                            "line": idx,
                            "pattern": name,
                            "risk_level": risk_level,
                            "context": matched_text,
                            "classification": classification,
                            "recommendation": rec
                        })
    except Exception as e:
        print(f"Error reading {rel_path}: {e}")
        
    return results

def run_audit():
    findings = []
    
    # Folders to scan
    scan_dirs = ["src", "scripts", "tests"]
    for d in scan_dirs:
        dir_path = os.path.join(ROOT_DIR, d)
        if not os.path.exists(dir_path):
            continue
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    # Skip audit script itself
                    if "audit_engine.py" in file:
                        continue
                    findings.extend(scan_file(full_path))
                    
    # Write to CSV
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    headers = ["file", "line", "pattern", "risk_level", "context", "classification", "recommendation"]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in findings:
            writer.writerow(row)
            
    print(f"Audit Complete. Scanned all python files. Findings count: {len(findings)}")
    print(f"Audit Scan CSV written to: {CSV_PATH}")
    return findings

if __name__ == "__main__":
    run_audit()
