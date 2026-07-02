"""
tests/test_phase32_quality_hardening.py

Phase 32 acceptance tests:
1. audit allowlist exists and has classifications
2. active source registry exists
3. no active live-path audit violations
4. Combined Router v1 truth lock exists
5. trade forensics file exists and has 557 rows
6. candidate registry has unique IDs
7. executed candidates have metrics
8. unexecuted candidates have blank metrics
9. candidate diversity report exists
10. finalist proof pack exists
11. best fusion trade log exists if fusion selected
12. best fusion metrics compute from trade log
13. stress audit exists
14. live execution delta exists
15. project memory updated
16. manifest hashes match
"""
import os
import json
import hashlib
import pandas as pd
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS = os.path.join(ROOT_DIR, "reports")
PM = os.path.join(ROOT_DIR, "project_memory")
INITIAL_CAPITAL = 10000.0


def _path(fname):
    return os.path.join(REPORTS, fname)


def _pm(fname):
    return os.path.join(PM, fname)


# ── Test 1: Audit allowlist exists and has classifications ─────────────────

def test_audit_allowlist_exists():
    p = _pm("AUDIT_ALLOWLIST.csv")
    assert os.path.exists(p), "AUDIT_ALLOWLIST.csv must exist in project_memory/"


def test_audit_allowlist_has_classification_column():
    p = _pm("AUDIT_ALLOWLIST.csv")
    if not os.path.exists(p):
        pytest.skip("AUDIT_ALLOWLIST.csv not found")
    df = pd.read_csv(p)
    assert "classification" in df.columns, "AUDIT_ALLOWLIST must have classification column"


def test_audit_allowlist_entries_are_safe():
    p = _pm("AUDIT_ALLOWLIST.csv")
    if not os.path.exists(p):
        pytest.skip("AUDIT_ALLOWLIST.csv not found")
    df = pd.read_csv(p)
    # All entries should be EVIDENCE_ONLY or similar — not live path
    for _, row in df.iterrows():
        cls = str(row.get("classification", ""))
        can_import = str(row.get("can_import_active_strategy", "")).upper()
        assert can_import != "YES" or "ACTIVE" in cls, (
            f"Allowlist entry {row.get('file_path')} claims can_import_active=YES but is not active classification"
        )


# ── Test 2: Active source registry exists ─────────────────────────────────

def test_source_classification_registry_exists():
    p = _pm("SOURCE_CLASSIFICATION_REGISTRY.csv")
    assert os.path.exists(p), "SOURCE_CLASSIFICATION_REGISTRY.csv must exist in project_memory/"


def test_source_registry_has_required_columns():
    p = _pm("SOURCE_CLASSIFICATION_REGISTRY.csv")
    if not os.path.exists(p):
        pytest.skip("SOURCE_CLASSIFICATION_REGISTRY.csv not found")
    df = pd.read_csv(p)
    required = ["file_path", "role", "classification"]
    for col in required:
        assert col in df.columns, f"Source registry missing column: {col}"


def test_source_registry_has_active_and_historical():
    p = _pm("SOURCE_CLASSIFICATION_REGISTRY.csv")
    if not os.path.exists(p):
        pytest.skip("SOURCE_CLASSIFICATION_REGISTRY.csv not found")
    df = pd.read_csv(p)
    has_active = df["classification"].str.contains("ACTIVE", na=False).any()
    assert has_active, "Source registry must contain at least one ACTIVE entry"


# ── Test 3: No active live-path audit violations ───────────────────────────

def test_no_active_live_path_violations():
    p = _path("phase32_audit_allowlist_review.csv")
    if not os.path.exists(p):
        pytest.skip("phase32_audit_allowlist_review.csv not found — run phase32_runner.py first")
    df = pd.read_csv(p)
    violations = df[df["verdict"] == "VIOLATION"]
    assert len(violations) == 0, (
        f"Found {len(violations)} live-path violations:\n"
        + violations[["file", "line", "pattern", "verdict"]].to_string()
    )


def test_infra_audit_report_exists():
    p = _path("phase32_infrastructure_anti_bias_audit.md")
    assert os.path.exists(p), "phase32_infrastructure_anti_bias_audit.md must exist"


def test_infra_audit_report_states_clean():
    p = _path("phase32_infrastructure_anti_bias_audit.md")
    if not os.path.exists(p):
        pytest.skip("Infra audit report not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "INFRA_CLEAN" in content or "NO LIVE-PATH VIOLATIONS" in content, (
        "Infra audit must state INFRA_CLEAN or NO LIVE-PATH VIOLATIONS"
    )


# ── Test 4: Combined Router v1 truth lock exists ───────────────────────────

def test_combined_router_v1_truth_lock_exists():
    p = _path("phase32_combined_router_v1_truth_lock.csv")
    assert os.path.exists(p), "phase32_combined_router_v1_truth_lock.csv must exist"


def test_combined_router_v1_truth_lock_has_required_metrics():
    p = _path("phase32_combined_router_v1_truth_lock.csv")
    if not os.path.exists(p):
        pytest.skip("Truth lock file not found")
    df = pd.read_csv(p)
    required_metrics = {"net_pnl", "trades", "profit_factor", "max_drawdown_pct"}
    actual_metrics = set(df["metric"].tolist()) if "metric" in df.columns else set()
    missing = required_metrics - actual_metrics
    assert len(missing) == 0, f"Truth lock missing metrics: {missing}"


def test_combined_router_v1_locked_or_drift_documented():
    p = _path("phase32_combined_router_v1_truth_lock.csv")
    if not os.path.exists(p):
        pytest.skip("Truth lock file not found")
    df = pd.read_csv(p)
    assert "status" in df.columns, "Truth lock must have status column"
    statuses = df["status"].unique().tolist()
    for s in statuses:
        assert s in ("LOCKED", "DRIFT_DETECTED"), f"Unknown status in truth lock: {s}"


# ── Test 5: Trade forensics file exists and has 557 rows ──────────────────

def test_trade_forensics_exists():
    p = _path("phase32_full_trade_quality_forensics.csv")
    assert os.path.exists(p), "phase32_full_trade_quality_forensics.csv must exist"


def test_trade_forensics_has_557_rows():
    p = _path("phase32_full_trade_quality_forensics.csv")
    if not os.path.exists(p):
        pytest.skip("Trade forensics file not found")
    df = pd.read_csv(p)
    assert len(df) == 557, f"Trade forensics must have 557 rows, found {len(df)}"


def test_trade_forensics_has_classification_column():
    p = _path("phase32_full_trade_quality_forensics.csv")
    if not os.path.exists(p):
        pytest.skip("Trade forensics file not found")
    df = pd.read_csv(p)
    assert "trade_class" in df.columns, "Trade forensics must have trade_class column"


def test_trade_forensics_all_trades_classified():
    p = _path("phase32_full_trade_quality_forensics.csv")
    if not os.path.exists(p):
        pytest.skip("Trade forensics file not found")
    df = pd.read_csv(p)
    valid_classes = {
        "ELITE_WINNER", "ACCEPTABLE_WINNER", "WEAK_WINNER",
        "AVOIDABLE_LOSER", "NORMAL_LOSER", "TOXIC_LOSER", "AMBIGUOUS_EXECUTION"
    }
    unclassified = df[~df["trade_class"].isin(valid_classes)]
    assert len(unclassified) == 0, f"{len(unclassified)} trades have invalid classification"


# ── Test 6: Candidate registry has unique IDs ─────────────────────────────

def test_candidate_registry_exists():
    p = _path("phase32_candidate_registry.csv")
    assert os.path.exists(p), "phase32_candidate_registry.csv must exist"


def test_candidate_registry_has_unique_ids():
    p = _path("phase32_candidate_registry.csv")
    if not os.path.exists(p):
        pytest.skip("Candidate registry not found")
    df = pd.read_csv(p)
    assert "candidate_id" in df.columns, "Candidate registry must have candidate_id column"
    assert df["candidate_id"].nunique() == len(df), (
        f"Candidate IDs are not unique: {len(df)} rows, {df['candidate_id'].nunique()} unique"
    )


def test_candidate_registry_has_multiple_families():
    p = _path("phase32_candidate_registry.csv")
    if not os.path.exists(p):
        pytest.skip("Candidate registry not found")
    df = pd.read_csv(p)
    if "family" not in df.columns:
        pytest.skip("family column not in registry")
    n_families = df["family"].nunique()
    assert n_families >= 3, f"Must have at least 3 candidate families, found {n_families}"


# ── Test 7: Executed candidates have metrics ──────────────────────────────

def test_executed_candidates_have_metrics():
    p = _path("phase32_candidate_results.csv")
    if not os.path.exists(p):
        pytest.skip("Candidate results not found")
    df = pd.read_csv(p)
    if len(df) == 0:
        pytest.skip("No executed candidates")
    required = ["net_pnl", "profit_factor", "max_drawdown_pct", "trades"]
    for col in required:
        assert col in df.columns, f"Candidate results missing column: {col}"
        non_empty = df[col].notna() & (df[col].astype(str) != "")
        assert non_empty.any(), f"All executed candidates have blank {col}"


def test_executed_candidates_have_trade_log_hash():
    p = _path("phase32_candidate_results.csv")
    if not os.path.exists(p):
        pytest.skip("Candidate results not found")
    df = pd.read_csv(p)
    if len(df) == 0:
        pytest.skip("No executed candidates")
    if "trade_log_hash" not in df.columns:
        pytest.skip("trade_log_hash column not present")
    missing_hash = df[df["trade_log_hash"].isna() | (df["trade_log_hash"].astype(str) == "")]
    assert len(missing_hash) == 0, f"{len(missing_hash)} executed candidates have no trade log hash"


# ── Test 8: Unexecuted candidates have blank metrics ──────────────────────

def test_unexecuted_candidates_have_blank_metrics():
    p = _path("phase32_candidate_registry.csv")
    if not os.path.exists(p):
        pytest.skip("Candidate registry not found")
    df = pd.read_csv(p)
    if "executed" not in df.columns:
        pytest.skip("executed column not in registry")
    unexecuted = df[df["executed"] == False]
    if len(unexecuted) == 0:
        pytest.skip("No unexecuted candidates")
    # For unexecuted candidates, net_pnl should be blank/NaN
    if "net_pnl" in unexecuted.columns:
        non_blank = unexecuted[unexecuted["net_pnl"].notna() & (unexecuted["net_pnl"].astype(str) != "")]
        assert len(non_blank) == 0, f"{len(non_blank)} unexecuted candidates have non-blank net_pnl"


# ── Test 9: Candidate diversity report exists ─────────────────────────────

def test_candidate_diversity_report_exists():
    p = _path("phase32_candidate_diversity_report.csv")
    assert os.path.exists(p), "phase32_candidate_diversity_report.csv must exist"


def test_candidate_diversity_has_multiple_families():
    p = _path("phase32_candidate_diversity_report.csv")
    if not os.path.exists(p):
        pytest.skip("Diversity report not found")
    df = pd.read_csv(p)
    assert len(df) >= 2, f"Diversity report must have at least 2 families, found {len(df)}"


# ── Test 10: Finalist proof pack exists ───────────────────────────────────

def test_finalist_proof_pack_exists():
    p = _path("phase32_finalist_candidate_proof_pack.md")
    assert os.path.exists(p), "phase32_finalist_candidate_proof_pack.md must exist"


def test_finalist_proof_pack_has_substantial_content():
    p = _path("phase32_finalist_candidate_proof_pack.md")
    if not os.path.exists(p):
        pytest.skip("Proof pack not found")
    size = os.path.getsize(p)
    assert size >= 200, f"Proof pack is too small ({size} bytes) — may be empty"


def test_finalist_proof_pack_mentions_not_real_capital_ready():
    p = _path("phase32_finalist_candidate_proof_pack.md")
    if not os.path.exists(p):
        pytest.skip("Proof pack not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NOT_REAL_CAPITAL_READY" in content, "Proof pack must state NOT_REAL_CAPITAL_READY"


# ── Test 11: Best fusion trade log exists if fusion selected ──────────────

def test_fusion_results_exist():
    p = _path("phase32_fusion_results.csv")
    assert os.path.exists(p), "phase32_fusion_results.csv must exist"


def test_best_fusion_trade_log_exists():
    p = _path("phase32_best_fusion_trade_log.csv")
    assert os.path.exists(p), "phase32_best_fusion_trade_log.csv must exist"


def test_best_fusion_trade_log_has_required_columns():
    p = _path("phase32_best_fusion_trade_log.csv")
    if not os.path.exists(p):
        pytest.skip("Best fusion trade log not found")
    df = pd.read_csv(p)
    required = ["entry_time", "exit_time", "net_pnl", "entry_price", "stop_loss", "take_profit"]
    for col in required:
        assert col in df.columns, f"Fusion trade log missing column: {col}"


def test_best_fusion_monthly_table_exists():
    p = _path("phase32_best_fusion_monthly_table.csv")
    assert os.path.exists(p), "phase32_best_fusion_monthly_table.csv must exist"


# ── Test 12: Best fusion metrics compute from trade log ───────────────────

def test_best_fusion_pnl_computes_from_trade_log():
    trade_log_path = _path("phase32_best_fusion_trade_log.csv")
    results_path = _path("phase32_fusion_results.csv")
    if not os.path.exists(trade_log_path) or not os.path.exists(results_path):
        pytest.skip("Fusion files not found")

    df_trades = pd.read_csv(trade_log_path)
    computed_pnl = round(df_trades["net_pnl"].astype(float).sum(), 2)

    df_results = pd.read_csv(results_path)
    executed = df_results[df_results["status"] == "EXECUTED"]
    if len(executed) == 0:
        pytest.skip("No executed fusions in results")

    # Find best fusion by composite score
    executed["composite_score"] = pd.to_numeric(executed.get("composite_score", 0), errors="coerce").fillna(0)
    best = executed.loc[executed["composite_score"].idxmax()]
    reported_pnl = float(best["net_pnl"])

    # The trade log should correspond to the best fusion — allow ±50 tolerance
    assert abs(computed_pnl - reported_pnl) <= 50.0, (
        f"Fusion PnL from trade log ({computed_pnl:.2f}) does not match reported ({reported_pnl:.2f})"
    )


def test_best_fusion_pf_computes_from_trade_log():
    p = _path("phase32_best_fusion_trade_log.csv")
    if not os.path.exists(p):
        pytest.skip("Best fusion trade log not found")
    df = pd.read_csv(p)
    pnl = df["net_pnl"].astype(float)
    gp = pnl[pnl > 0].sum()
    gl = abs(pnl[pnl <= 0].sum())
    computed_pf = round(gp / gl, 4) if gl > 0 else float("inf")
    assert computed_pf > 1.0, f"Best fusion PF computed from trade log is {computed_pf:.4f} — must be > 1.0"


def test_best_fusion_entry_prices_positive():
    p = _path("phase32_best_fusion_trade_log.csv")
    if not os.path.exists(p):
        pytest.skip("Best fusion trade log not found")
    df = pd.read_csv(p)
    bad = df[df["entry_price"].astype(float) <= 0]
    assert len(bad) == 0, f"{len(bad)} trades have non-positive entry prices"


def test_best_fusion_timestamp_ordering():
    p = _path("phase32_best_fusion_trade_log.csv")
    if not os.path.exists(p):
        pytest.skip("Best fusion trade log not found")
    df = pd.read_csv(p)
    bad = df[df["entry_time"].astype(float) > df["exit_time"].astype(float)]
    assert len(bad) == 0, f"{len(bad)} trades have entry_time > exit_time"


# ── Test 13: Stress audit exists ──────────────────────────────────────────

def test_stress_audit_exists():
    p = _path("phase32_stress_audit.csv")
    assert os.path.exists(p), "phase32_stress_audit.csv must exist"


def test_stress_audit_has_15_scenarios():
    p = _path("phase32_stress_audit.csv")
    if not os.path.exists(p):
        pytest.skip("Stress audit not found")
    df = pd.read_csv(p)
    assert len(df) == 15, f"Stress audit must have 15 scenarios, found {len(df)}"


def test_stress_audit_has_required_columns():
    p = _path("phase32_stress_audit.csv")
    if not os.path.exists(p):
        pytest.skip("Stress audit not found")
    df = pd.read_csv(p)
    required = ["scenario", "net_pnl", "profit_factor", "verdict"]
    for col in required:
        assert col in df.columns, f"Stress audit missing column: {col}"


def test_stress_audit_normal_scenario_passes():
    p = _path("phase32_stress_audit.csv")
    if not os.path.exists(p):
        pytest.skip("Stress audit not found")
    df = pd.read_csv(p)
    normal = df[df["scenario"] == "normal"]
    assert len(normal) > 0, "Stress audit must include 'normal' scenario"
    assert normal.iloc[0]["verdict"] == "PASS", "Normal scenario must PASS"


# ── Test 14: Live execution delta exists ───────────────────────────────────

def test_live_execution_delta_exists():
    p = _path("phase32_live_execution_readiness_delta.md")
    assert os.path.exists(p), "phase32_live_execution_readiness_delta.md must exist"


def test_live_execution_delta_states_not_real_capital_ready():
    p = _path("phase32_live_execution_readiness_delta.md")
    if not os.path.exists(p):
        pytest.skip("Live execution delta not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NOT_REAL_CAPITAL_READY" in content, "Live execution delta must state NOT_REAL_CAPITAL_READY"


def test_live_execution_delta_states_backtest_verified():
    p = _path("phase32_live_execution_readiness_delta.md")
    if not os.path.exists(p):
        pytest.skip("Live execution delta not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "BACKTEST_VERIFIED_NOT_SHADOWED" in content, "Live execution delta must state BACKTEST_VERIFIED_NOT_SHADOWED"


# ── Test 15: Project memory updated ───────────────────────────────────────

def test_current_handoff_mentions_phase32():
    p = os.path.join(os.path.dirname(REPORTS), "project_memory", "CURRENT_HANDOFF.md")
    if not os.path.exists(p):
        pytest.skip("CURRENT_HANDOFF.md not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Phase 32" in content, "CURRENT_HANDOFF.md must mention Phase 32"


def test_current_handoff_has_not_real_capital_ready():
    p = os.path.join(os.path.dirname(REPORTS), "project_memory", "CURRENT_HANDOFF.md")
    if not os.path.exists(p):
        pytest.skip("CURRENT_HANDOFF.md not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NOT_REAL_CAPITAL_READY" in content, "CURRENT_HANDOFF.md must state NOT_REAL_CAPITAL_READY"


def test_benchmark_registry_has_phase32_entry():
    p = os.path.join(os.path.dirname(REPORTS), "project_memory", "BENCHMARK_REGISTRY.csv")
    if not os.path.exists(p):
        pytest.skip("BENCHMARK_REGISTRY.csv not found")
    df = pd.read_csv(p)
    phase32 = df[df["benchmark_name"].str.contains("Phase 32", na=False)]
    assert len(phase32) >= 1, "BENCHMARK_REGISTRY must have at least 1 Phase 32 entry"


def test_next_phase_plan_mentions_phase33():
    p = os.path.join(os.path.dirname(REPORTS), "project_memory", "NEXT_PHASE_PLAN.md")
    if not os.path.exists(p):
        pytest.skip("NEXT_PHASE_PLAN.md not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Phase 33" in content, "NEXT_PHASE_PLAN.md must reference Phase 33"


# ── Test 16: Manifest hashes match ────────────────────────────────────────

def test_phase32_manifest_exists():
    p = _path("phase32_audit_manifest.json")
    assert os.path.exists(p), "phase32_audit_manifest.json must exist"


def test_phase32_manifest_has_verdict():
    p = _path("phase32_audit_manifest.json")
    if not os.path.exists(p):
        pytest.skip("Manifest not found")
    with open(p, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert "verdict" in manifest, "Manifest must have verdict"
    valid_verdicts = {
        "PHASE32_PASS_BEST_FUSION_IMPROVES_EXECUTABLE_BASELINE",
        "PHASE32_PARTIAL_PASS_ROUTER_HARDENED_NO_BETTER_FUSION",
        "PHASE32_PARTIAL_PASS_INFRA_FIXED_STRATEGY_NOT_IMPROVED",
        "PHASE32_FAIL_ACTIVE_PATH_AUDIT_VIOLATION",
        "PHASE32_FAIL_METRIC_RECONCILIATION",
    }
    assert manifest["verdict"] in valid_verdicts, f"Unknown verdict: {manifest['verdict']}"


def test_phase32_manifest_hashes_match():
    manifest_path = _path("phase32_audit_manifest.json")
    if not os.path.exists(manifest_path):
        pytest.skip("Manifest not found")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    mismatches = []
    root = os.path.dirname(REPORTS)
    for rel_path, info in manifest.get("files", {}).items():
        if isinstance(info, dict):
            expected_hash = info.get("sha256", "")
            if expected_hash == "FILE_NOT_FOUND":
                continue  # Expected missing file
            full_path = os.path.join(root, rel_path)
            if not os.path.exists(full_path):
                mismatches.append(f"FILE_MISSING: {rel_path}")
                continue
            h = hashlib.sha256()
            with open(full_path, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            actual = h.hexdigest()
            if actual != expected_hash:
                mismatches.append(f"HASH_MISMATCH: {rel_path}")

    assert len(mismatches) == 0, f"Manifest hash mismatches:\n" + "\n".join(mismatches)


# ── Additional quality tests ───────────────────────────────────────────────

def test_main_phase32_report_exists():
    p = _path("phase32_combined_router_quality_hardening_and_fusion_expansion_report.md")
    assert os.path.exists(p), "Phase 32 main report must exist"


def test_main_phase32_report_has_verdict():
    p = _path("phase32_combined_router_quality_hardening_and_fusion_expansion_report.md")
    if not os.path.exists(p):
        pytest.skip("Main report not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    valid = [
        "PHASE32_PASS_BEST_FUSION_IMPROVES_EXECUTABLE_BASELINE",
        "PHASE32_PARTIAL_PASS_ROUTER_HARDENED_NO_BETTER_FUSION",
        "PHASE32_PARTIAL_PASS_INFRA_FIXED_STRATEGY_NOT_IMPROVED",
        "PHASE32_FAIL_ACTIVE_PATH_AUDIT_VIOLATION",
        "PHASE32_FAIL_METRIC_RECONCILIATION",
    ]
    found = any(v in content for v in valid)
    assert found, "Phase 32 main report must contain a valid PHASE32_ verdict"


def test_main_phase32_report_not_real_capital_ready():
    p = _path("phase32_combined_router_quality_hardening_and_fusion_expansion_report.md")
    if not os.path.exists(p):
        pytest.skip("Main report not found")
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NOT_REAL_CAPITAL_READY" in content


def test_repair_module_results_exist():
    p = _path("phase32_repair_module_results.csv")
    assert os.path.exists(p), "phase32_repair_module_results.csv must exist"


def test_repair_module_results_has_v1_baseline():
    p = _path("phase32_repair_module_results.csv")
    if not os.path.exists(p):
        pytest.skip("Repair results not found")
    df = pd.read_csv(p)
    has_v1 = df["repair_module"].str.contains("v1_baseline", na=False).any()
    assert has_v1, "Repair results must include v1_baseline for comparison"


def test_benchmark_comparison_exists():
    p = _path("phase32_benchmark_comparison.csv")
    assert os.path.exists(p), "phase32_benchmark_comparison.csv must exist"


def test_benchmark_comparison_has_v1_and_best_fusion():
    p = _path("phase32_benchmark_comparison.csv")
    if not os.path.exists(p):
        pytest.skip("Benchmark comparison not found")
    df = pd.read_csv(p)
    strategies = " ".join(df["strategy"].tolist())
    assert "Combined Router v1" in strategies or "v1" in strategies.lower(), (
        "Benchmark comparison must include Combined Router v1"
    )
    assert "Phase 32" in strategies or "fusion" in strategies.lower(), (
        "Benchmark comparison must include Phase 32 fusion"
    )


def test_phase32_runner_exists_and_has_no_forced_metrics():
    runner_path = os.path.join(os.path.dirname(REPORTS), "scripts", "phase32_runner.py")
    assert os.path.exists(runner_path), "scripts/phase32_runner.py must exist"
    with open(runner_path, "r", encoding="utf-8") as f:
        content = f.read()
    # These patterns should not appear in the runner as assignments
    forbidden = [
        "pnl_81_calc = pnl_81",
        "diff_pnl = 29386",
        "profit_factor = 1.25",  # direct assignment outside strings/comments
        "replace=True",
    ]
    for pattern in forbidden:
        # Skip if the pattern is inside a string literal (checking patterns)
        if pattern in content:
            lines = [l for l in content.split("\n") if pattern in l and not l.strip().startswith("#")]
            # Allow in string literals (quote-wrapped)
            real_violations = [l for l in lines if not ('"' + pattern + '"' in l or "'" + pattern + "'" in l)]
            assert len(real_violations) == 0, (
                f"Forbidden pattern '{pattern}' found in phase32_runner.py:\n" + "\n".join(real_violations)
            )
