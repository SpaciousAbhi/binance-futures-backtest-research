"""
tests/test_phase31_1_combined_router_acceptance.py

Phase 31.1 — Combined Router Full Acceptance Audit Tests.
Tests verify all output files exist, metrics reconcile from trade log,
no lookahead violations, stress audit exists, and project memory is updated.
"""
import os
import sys
import json
import csv
import hashlib
import math
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS = os.path.join(ROOT, "reports")
PM = os.path.join(ROOT, "project_memory")

REQUIRED_OUTPUTS = [
    "reports/phase31_1_source_lock.csv",
    "reports/phase31_1_cand0190_reproduction.csv",
    "reports/phase31_1_combined_router_reproduction.csv",
    "reports/phase31_1_full_trade_audit.csv",
    "reports/phase31_1_entry_exit_rule_serialization.md",
    "reports/phase31_1_lookahead_hardcoding_audit.csv",
    "reports/phase31_1_metric_reconciliation.csv",
    "reports/phase31_1_stress_torture_audit.csv",
    "reports/phase31_1_live_execution_feasibility.md",
    "reports/phase31_1_weakness_map.csv",
    "reports/phase31_1_combined_router_acceptance_audit_report.md",
    "reports/phase31_1_audit_manifest.json",
]

PHASE31_TRADE_LOG = os.path.join(REPORTS, "phase31_best_router_trade_log.csv")

INITIAL_CAPITAL = 10000.0


# ============================================================
# Helpers
# ============================================================

def load_trade_log():
    return pd.read_csv(PHASE31_TRADE_LOG)


def compute_pf(df):
    pnl = df["net_pnl"].astype(float)
    wins = pnl[pnl > 0].sum()
    losses = abs(pnl[pnl <= 0].sum())
    return wins / losses if losses > 0 else float("inf")


def compute_max_dd(df):
    equity = INITIAL_CAPITAL + df["net_pnl"].astype(float).cumsum()
    peaks = equity.cummax()
    return float(((peaks - equity) / peaks).max())


# ============================================================
# Test 1 — All required output files exist
# ============================================================
@pytest.mark.parametrize("rel_path", REQUIRED_OUTPUTS)
def test_required_output_files_exist(rel_path):
    """All Phase 31.1 output files must exist."""
    full = os.path.join(ROOT, rel_path)
    assert os.path.exists(full), f"MISSING: {rel_path}"
    assert os.path.getsize(full) > 0, f"EMPTY FILE: {rel_path}"


# ============================================================
# Test 2 — Combined Router trade log trade count check
# ============================================================
def test_phase31_trade_log_exists():
    """Phase 31 best router trade log must exist."""
    assert os.path.exists(PHASE31_TRADE_LOG), "phase31_best_router_trade_log.csv is missing"


def test_phase31_trade_log_count():
    """Phase 31 trade log must have exactly 557 rows (the claimed count)."""
    df = load_trade_log()
    assert len(df) == 557, f"Expected 557 trades, got {len(df)}"


# ============================================================
# Test 3 — Every trade has required fields
# ============================================================
def test_all_trades_have_required_fields():
    """Every trade must have entry_time, exit_time, side, entry_price, exit_price, SL, TP, net_pnl."""
    df = load_trade_log()
    required = ["entry_time", "exit_time", "side", "entry_price", "exit_price", "stop_loss", "take_profit", "net_pnl"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"
        missing = df[col].isna().sum()
        assert missing == 0, f"Column {col} has {missing} null values"


def test_all_trade_entry_prices_positive():
    """All entry prices must be positive."""
    df = load_trade_log()
    bad = df[df["entry_price"].astype(float) <= 0]
    assert len(bad) == 0, f"{len(bad)} trades have non-positive entry_price"


def test_all_trade_exit_prices_positive():
    """All exit prices must be positive."""
    df = load_trade_log()
    bad = df[df["exit_price"].astype(float) <= 0]
    assert len(bad) == 0, f"{len(bad)} trades have non-positive exit_price"


def test_all_trades_have_stop_loss():
    """All trades must have a stop loss > 0."""
    df = load_trade_log()
    bad = df[df["stop_loss"].astype(float) <= 0]
    assert len(bad) == 0, f"{len(bad)} trades have no stop loss"


def test_all_trades_have_take_profit():
    """All trades must have a take profit > 0."""
    df = load_trade_log()
    bad = df[df["take_profit"].astype(float) <= 0]
    assert len(bad) == 0, f"{len(bad)} trades have no take profit"


# ============================================================
# Test 4 — Entry time before exit time
# ============================================================
def test_entry_time_before_or_equal_exit_time():
    """Exit time must be >= entry time for all trades."""
    df = load_trade_log()
    bad = df[df["entry_time"].astype(float) > df["exit_time"].astype(float)]
    assert len(bad) == 0, f"{len(bad)} trades have entry_time > exit_time"


# ============================================================
# Test 5 — No missing source sleeve in audit
# ============================================================
def test_full_trade_audit_no_missing_source():
    """Full trade audit must not have MISSING_SOURCE trades."""
    audit_path = os.path.join(REPORTS, "phase31_1_full_trade_audit.csv")
    if not os.path.exists(audit_path):
        pytest.skip("Trade audit not yet generated")
    df = pd.read_csv(audit_path)
    missing = df[df["classification"] == "MISSING_SOURCE"]
    assert len(missing) == 0, f"{len(missing)} trades have MISSING_SOURCE classification"


# ============================================================
# Test 6 — Metrics reconcile from trade log
# ============================================================
def test_net_pnl_reconciles_from_trade_log():
    """Net PnL must compute from trade log within $5 tolerance of $11,205.20."""
    df = load_trade_log()
    computed = df["net_pnl"].astype(float).sum()
    claimed = 11205.20
    assert abs(computed - claimed) < 5, f"Net PnL mismatch: computed={computed:.2f} claimed={claimed}"


def test_profit_factor_reconciles_from_trade_log():
    """Profit Factor must compute from trade log within 0.05 of 1.25."""
    df = load_trade_log()
    pf = compute_pf(df)
    claimed = 1.25
    assert abs(pf - claimed) < 0.05, f"PF mismatch: computed={pf:.4f} claimed={claimed}"


def test_trade_count_reconciles():
    """Trade count must match claimed 557."""
    df = load_trade_log()
    assert len(df) == 557, f"Trade count: {len(df)} != 557"


# ============================================================
# Test 7 — Stress audit file exists and has 15 scenarios
# ============================================================
def test_stress_audit_exists_and_has_15_scenarios():
    """Phase 31.1 stress audit must have 15 rows (one per scenario)."""
    stress_path = os.path.join(REPORTS, "phase31_1_stress_torture_audit.csv")
    if not os.path.exists(stress_path):
        pytest.skip("Stress audit not yet generated")
    df = pd.read_csv(stress_path)
    assert len(df) == 15, f"Expected 15 stress scenarios, got {len(df)}"


def test_stress_audit_has_required_columns():
    """Stress audit must have scenario, net_pnl, profit_factor, max_dd_pct, verdict."""
    stress_path = os.path.join(REPORTS, "phase31_1_stress_torture_audit.csv")
    if not os.path.exists(stress_path):
        pytest.skip("Stress audit not yet generated")
    df = pd.read_csv(stress_path)
    required = ["scenario", "net_pnl", "profit_factor", "max_dd_pct", "trades", "verdict"]
    for col in required:
        assert col in df.columns, f"Stress audit missing column: {col}"


def test_stress_audit_normal_scenario_passes():
    """Normal (no stress) scenario must PASS."""
    stress_path = os.path.join(REPORTS, "phase31_1_stress_torture_audit.csv")
    if not os.path.exists(stress_path):
        pytest.skip("Stress audit not yet generated")
    df = pd.read_csv(stress_path)
    normal = df[df["scenario"] == "normal"]
    assert len(normal) > 0, "Normal scenario missing from stress table"
    assert normal.iloc[0]["verdict"] == "PASS", f"Normal scenario should PASS, got {normal.iloc[0]['verdict']}"


# ============================================================
# Test 8 — Lookahead/hardcoding audit has no live-path violations in runner
# ============================================================
def test_lookahead_audit_no_live_path_violations_in_phase31_1_runner():
    """Phase 31.1 runner must not contain live-path lookahead violations."""
    runner_path = os.path.join(ROOT, "scripts", "phase31_1_runner.py")
    if not os.path.exists(runner_path):
        pytest.skip("Phase 31.1 runner not yet created")

    violations_in_runner = []
    forbidden_patterns = [
        "is_winner",
        "future_pnl",
        "future_return",
        "future_mfe",
        "future_mae",
        "replace=True",
        "pnl_81_calc = pnl_81",
    ]
    # Lines that are clearly pattern-definition tables or documentation — not actual code usage
    skip_indicators = [
        # The LOOKAHEAD_PATTERNS list definition
        '"VIOLATION"',
        '"REVIEW"',
        "LOOKAHEAD_PATTERNS",
        # Rule serialization markdown content (multi-line string)
        "- is_winner labels",
        "- future_pnl / future_return",
        "`is_winner`",
        "`future_pnl`",
        "`future_mfe`",
        "`future_mae`",
        "is_winner`, `future_pnl",
    ]

    with open(runner_path, "r", encoding="utf-8", errors="ignore") as f:
        for lnum, line in enumerate(f, 1):
            stripped = line.strip()
            # Skip comment lines
            if stripped.startswith("#"):
                continue
            # Skip documentation/string-literal pattern definition lines
            if any(skip_ind in stripped for skip_ind in skip_indicators):
                continue
            # Skip lines that are clearly part of a string literal rule doc
            if stripped.startswith("-") and "labels" in stripped:
                continue
            for pat in forbidden_patterns:
                if pat in stripped:
                    violations_in_runner.append((lnum, pat, stripped[:80]))

    assert len(violations_in_runner) == 0, (
        f"Lookahead violations in phase31_1_runner.py:\n"
        + "\n".join(f"  L{l}: {p}" for l, p, _ in violations_in_runner)
    )


def test_phase31_runner_no_hardcoded_pnl_assignment():
    """Phase 31 runner must not directly assign hardcoded PnL to override computed value."""
    runner_path = os.path.join(ROOT, "scripts", "phase31_runner.py")
    if not os.path.exists(runner_path):
        pytest.skip("Phase 31 runner not found")

    critical_patterns = ["pnl_81_calc = pnl_81", "diff_pnl = 29386", "diff_pnl = 30580", "diff_pnl = 31250"]
    with open(runner_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    for pat in critical_patterns:
        assert pat not in content, f"Hardcoded PnL manipulation found in phase31_runner.py: '{pat}'"


# ============================================================
# Test 9 — Entry/exit rule serialization exists and is substantial
# ============================================================
def test_entry_exit_rule_serialization_exists():
    """Entry/exit rule serialization file must exist."""
    path = os.path.join(REPORTS, "phase31_1_entry_exit_rule_serialization.md")
    assert os.path.exists(path), "Entry/exit rule serialization file missing"


def test_entry_exit_rule_serialization_is_substantial():
    """Rule serialization file must be at least 2000 bytes (non-trivial content)."""
    path = os.path.join(REPORTS, "phase31_1_entry_exit_rule_serialization.md")
    if not os.path.exists(path):
        pytest.skip("Rule serialization not yet generated")
    size = os.path.getsize(path)
    assert size > 2000, f"Rule serialization too short: {size} bytes"


def test_rule_serialization_covers_key_rules():
    """Rule serialization must mention key rule categories."""
    path = os.path.join(REPORTS, "phase31_1_entry_exit_rule_serialization.md")
    if not os.path.exists(path):
        pytest.skip("Rule serialization not yet generated")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    required_sections = ["Stop Loss", "Take Profit", "Session", "Fee", "Funding", "Sizing", "Conflict"]
    for section in required_sections:
        assert section in content, f"Rule serialization missing section: {section}"


# ============================================================
# Test 10 — Live execution feasibility file exists
# ============================================================
def test_live_execution_feasibility_exists():
    """Live execution feasibility file must exist."""
    path = os.path.join(REPORTS, "phase31_1_live_execution_feasibility.md")
    assert os.path.exists(path), "Live execution feasibility file missing"


def test_live_feasibility_states_not_real_capital_ready():
    """Live feasibility must state NOT_REAL_CAPITAL_READY or BACKTEST_VERIFIED_NOT_SHADOWED."""
    path = os.path.join(REPORTS, "phase31_1_live_execution_feasibility.md")
    if not os.path.exists(path):
        pytest.skip("Live feasibility not yet generated")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    valid_statuses = ["NOT_REAL_CAPITAL_READY", "BACKTEST_VERIFIED_NOT_SHADOWED"]
    has_status = any(s in content for s in valid_statuses)
    assert has_status, "Live feasibility file must state a valid live status"


# ============================================================
# Test 11 — Project memory updated
# ============================================================
def test_current_handoff_mentions_phase31_1():
    """CURRENT_HANDOFF.md must reference Phase 31.1."""
    handoff = os.path.join(PM, "CURRENT_HANDOFF.md")
    assert os.path.exists(handoff), "CURRENT_HANDOFF.md missing"
    with open(handoff, "r", encoding="utf-8") as f:
        content = f.read()
    assert "31.1" in content, "CURRENT_HANDOFF.md must mention Phase 31.1"


def test_current_handoff_has_not_real_capital_ready():
    """CURRENT_HANDOFF.md must state NOT_REAL_CAPITAL_READY."""
    handoff = os.path.join(PM, "CURRENT_HANDOFF.md")
    if not os.path.exists(handoff):
        pytest.skip("CURRENT_HANDOFF.md missing")
    with open(handoff, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NOT_REAL_CAPITAL_READY" in content, "CURRENT_HANDOFF.md must include NOT_REAL_CAPITAL_READY"


# ============================================================
# Test 12 — Manifest hashes match files
# ============================================================
def test_audit_manifest_exists():
    """Phase 31.1 audit manifest must exist."""
    manifest_path = os.path.join(REPORTS, "phase31_1_audit_manifest.json")
    assert os.path.exists(manifest_path), "phase31_1_audit_manifest.json missing"


def test_audit_manifest_hashes_match():
    """All files listed in Phase 31.1 manifest must exist and match recorded SHA-256 hashes."""
    manifest_path = os.path.join(REPORTS, "phase31_1_audit_manifest.json")
    if not os.path.exists(manifest_path):
        pytest.skip("Manifest not yet generated")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    mismatches = []
    for rel_path, info in manifest.get("files", {}).items():
        full_path = os.path.join(ROOT, rel_path)
        if info.get("sha256") == "FILE_NOT_FOUND":
            continue  # skip missing files — separate test checks existence
        if not os.path.exists(full_path):
            mismatches.append(f"FILE_NOT_FOUND: {rel_path}")
            continue
        h = hashlib.sha256()
        with open(full_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        actual_hash = h.hexdigest()
        expected_hash = info.get("sha256", "")
        if actual_hash != expected_hash:
            mismatches.append(f"HASH_MISMATCH: {rel_path} (expected={expected_hash[:16]}... actual={actual_hash[:16]}...)")

    assert len(mismatches) == 0, "Manifest hash mismatches:\n" + "\n".join(mismatches)


# ============================================================
# Additional sanity checks
# ============================================================
def test_phase31_1_runner_exists():
    """Phase 31.1 runner script must exist."""
    runner = os.path.join(ROOT, "scripts", "phase31_1_runner.py")
    assert os.path.exists(runner), "scripts/phase31_1_runner.py missing"


def test_cand0190_reproduction_exists_and_has_metrics():
    """CAND_0190 reproduction file must exist and have key metrics."""
    path = os.path.join(REPORTS, "phase31_1_cand0190_reproduction.csv")
    if not os.path.exists(path):
        pytest.skip("CAND_0190 reproduction not yet generated")
    df = pd.read_csv(path)
    assert "metric" in df.columns, "Missing metric column"
    assert "recomputed" in df.columns, "Missing recomputed column"
    metrics_present = df["metric"].tolist()
    required = ["net_pnl", "trades", "profit_factor"]
    for m in required:
        assert m in metrics_present, f"Missing metric: {m}"


def test_metric_reconciliation_tracks_discrepancies():
    """Metric reconciliation must have a 'status' column classifying each metric."""
    path = os.path.join(REPORTS, "phase31_1_metric_reconciliation.csv")
    if not os.path.exists(path):
        pytest.skip("Metric reconciliation not yet generated")
    df = pd.read_csv(path)
    assert "status" in df.columns, "Metric reconciliation missing status column"
    valid_statuses = {"OK", "DISCREPANCY", "NEW"}
    invalid = set(df["status"]) - valid_statuses
    assert len(invalid) == 0, f"Invalid status values: {invalid}"


def test_source_lock_has_all_roles():
    """Source lock must reference trade log, candidate results, and engine."""
    path = os.path.join(REPORTS, "phase31_1_source_lock.csv")
    if not os.path.exists(path):
        pytest.skip("Source lock not yet generated")
    df = pd.read_csv(path)
    required_roles = ["COMBINED_ROUTER_TRADE_LOG", "CANDIDATE_SWEEP_RESULTS", "BACKTEST_ENGINE"]
    roles = df["role"].tolist()
    for role in required_roles:
        assert role in roles, f"Source lock missing role: {role}"


def test_weakness_map_has_recommendations():
    """Weakness map must have at least 3 improvement recommendations."""
    path = os.path.join(REPORTS, "phase31_1_weakness_map.csv")
    if not os.path.exists(path):
        pytest.skip("Weakness map not yet generated")
    df = pd.read_csv(path)
    assert len(df) >= 3, f"Weakness map has only {len(df)} items, need at least 3"
    assert "recommendation" in df.columns, "Weakness map missing recommendation column"


def test_full_trade_audit_has_correct_row_count():
    """Full trade audit must audit all 557 trades."""
    path = os.path.join(REPORTS, "phase31_1_full_trade_audit.csv")
    if not os.path.exists(path):
        pytest.skip("Full trade audit not yet generated")
    df = pd.read_csv(path)
    assert len(df) == 557, f"Full trade audit has {len(df)} rows, expected 557"


def test_full_trade_audit_classification_completeness():
    """All audit rows must have a classification."""
    path = os.path.join(REPORTS, "phase31_1_full_trade_audit.csv")
    if not os.path.exists(path):
        pytest.skip("Full trade audit not yet generated")
    df = pd.read_csv(path)
    assert "classification" in df.columns, "Trade audit missing classification column"
    missing_class = df["classification"].isna().sum()
    assert missing_class == 0, f"{missing_class} trades have no classification"


def test_main_report_has_verdict():
    """Main acceptance audit report must contain the final verdict string."""
    path = os.path.join(REPORTS, "phase31_1_combined_router_acceptance_audit_report.md")
    if not os.path.exists(path):
        pytest.skip("Main report not yet generated")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    valid_verdicts = [
        "PHASE31_1_PASS_COMBINED_ROUTER_LOCKED_AS_EXECUTABLE_BASELINE",
        "PHASE31_1_PARTIAL_PASS_ROUTER_REAL_BUT_REQUIRES_FIXES",
        "PHASE31_1_FAIL_ROUTER_NOT_REPRODUCIBLE",
        "PHASE31_1_FAIL_LOOKAHEAD_OR_FORCED_METRICS_FOUND",
        "PHASE31_1_FAIL_TRADE_LOG_RECONCILIATION",
    ]
    has_verdict = any(v in content for v in valid_verdicts)
    assert has_verdict, "Main report must contain a valid final verdict"


def test_main_report_has_not_real_capital_ready():
    """Main report must mention NOT_REAL_CAPITAL_READY."""
    path = os.path.join(REPORTS, "phase31_1_combined_router_acceptance_audit_report.md")
    if not os.path.exists(path):
        pytest.skip("Main report not yet generated")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NOT_REAL_CAPITAL_READY" in content, "Main report must state NOT_REAL_CAPITAL_READY"
