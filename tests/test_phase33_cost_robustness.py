"""Phase 33 cost robustness and fusion upgrade tests."""
import hashlib
import json
import os
import re

import pandas as pd


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS = os.path.join(ROOT, "reports")
PM = os.path.join(ROOT, "project_memory")
INITIAL_CAPITAL = 10000.0


def report_path(name: str) -> str:
    return os.path.join(REPORTS, name)


def memory_path(name: str) -> str:
    return os.path.join(PM, name)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_metrics(df: pd.DataFrame) -> dict[str, float]:
    pnl = df["net_pnl"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]
    equity = INITIAL_CAPITAL + pnl.cumsum()
    peaks = equity.cummax()
    gross_profit = float(wins.sum())
    gross_loss = float(abs(losses.sum()))
    return {
        "net_pnl": round(float(pnl.sum()), 2),
        "trades": int(len(df)),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else 0.0,
        "max_drawdown_pct": round(float(((peaks - equity) / peaks).max() * 100), 4),
    }


def test_phase32_stress_contradiction_corrected_in_memory():
    combined = "\n".join(
        read_text(memory_path(name))
        for name in ["CURRENT_HANDOFF.md", "MASTER_PROJECT_STATE.md", "BENCHMARK_REGISTRY.csv"]
    )
    assert "Stress Fails: 0 / 15" not in combined
    assert "PASS=7 / FAIL=8" in combined
    assert "-$39,138.38" in combined or "-39138.38" in combined
    assert "359.59" in combined
    assert "STRESS_FRAGILE" in combined


def test_cost_sensitivity_trade_audit_exists_and_matches_baseline_count():
    path = report_path("phase33_cost_sensitivity_trade_audit.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert len(df) == 557
    required = {"gross_pnl", "net_pnl", "total_friction_cost", "cost_class", "stress_class"}
    assert required.issubset(df.columns)


def test_stress_failure_root_cause_file_exists():
    path = report_path("phase33_stress_failure_root_cause.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert len(df) > 0
    assert {"scenario", "group_type", "stress_damage"}.issubset(df.columns)


def test_repair_module_results_exist():
    path = report_path("phase33_repair_module_results.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert len(df) >= 10
    assert {"name", "net_pnl", "profit_factor", "stress_pass_count"}.issubset(df.columns)


def test_candidate_registry_has_unique_ids():
    path = report_path("phase33_candidate_registry.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert len(df) >= 3000
    assert df["candidate_id"].nunique() == len(df)
    assert df["candidate_hash"].nunique() == len(df)


def test_candidate_execution_accounting():
    path = report_path("phase33_candidate_results.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    executed = df[df["status"] == "EXECUTED"]
    unexecuted = df[df["status"] == "REGISTERED_NOT_EXECUTED_TIMEBOXED"]
    assert len(executed) >= 750
    assert len(unexecuted) > 0
    for col in ["net_pnl", "trades", "profit_factor", "max_drawdown_pct", "trade_log_hash"]:
        assert executed[col].notna().all(), f"executed candidates missing {col}"
        assert unexecuted[col].isna().all(), f"unexecuted candidates must have blank {col}"


def test_candidate_diversity_report_exists_and_exceeds_target():
    path = report_path("phase33_candidate_diversity_report.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    values = dict(zip(df["metric"], df["value"]))
    assert int(values["executed_behavior_clusters"]) >= 50
    assert values["status"] == "PASS_50_PLUS_CLUSTERS"


def test_finalist_proof_pack_exists():
    path = report_path("phase33_finalist_candidate_proof_pack.md")
    assert os.path.exists(path)
    text = read_text(path)
    assert "Phase 33 Finalist Candidate Proof Pack" in text
    assert "NOT_REAL_CAPITAL_READY" in text


def test_best_fusion_trade_log_exists_and_reconciles_metrics():
    trade_path = report_path("phase33_best_fusion_trade_log.csv")
    fusion_path = report_path("phase33_fusion_results.csv")
    assert os.path.exists(trade_path)
    assert os.path.exists(fusion_path)
    trades = pd.read_csv(trade_path)
    fusion = pd.read_csv(fusion_path)
    best = fusion.sort_values(["stress_pass_count", "profit_factor"], ascending=[False, False]).iloc[0]
    metrics = compute_metrics(trades)
    assert metrics["net_pnl"] == round(float(best["net_pnl"]), 2)
    assert metrics["trades"] == int(best["trades"])
    assert metrics["profit_factor"] == round(float(best["profit_factor"]), 4)
    assert metrics["max_drawdown_pct"] == round(float(best["max_drawdown_pct"]), 4)


def test_stress_table_exists():
    path = report_path("phase33_best_fusion_stress_table.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert len(df) >= 15
    assert {"scenario", "net_pnl", "verdict"}.issubset(df.columns)


def test_no_active_live_path_audit_violations():
    path = report_path("phase32_audit_allowlist_review.csv")
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert len(df[df["verdict"] == "VIOLATION"]) == 0


def test_live_readiness_delta_exists_and_not_real_capital_ready():
    path = report_path("phase33_live_execution_readiness_delta.md")
    assert os.path.exists(path)
    text = read_text(path)
    assert "BACKTEST_VERIFIED_NOT_SHADOWED" in text
    assert "NOT_REAL_CAPITAL_READY" in text


def test_phase33_runner_has_no_forbidden_construction_patterns():
    text = read_text(os.path.join(ROOT, "scripts", "phase33_cost_robustness.py"))
    assert ".sample(" not in text
    assert "replace=True" not in text
    for pattern in ["is_winner", "future_pnl", "future_R", "future_mfe", "future_mae"]:
        assert pattern not in text
    forbidden_assignment = re.compile(r"(target_pnl|forced_pnl|target_pf|forced_pf|target_dd|forced_dd)\s*=")
    assert not forbidden_assignment.search(text)


def test_manifest_hashes_match_disk_files():
    manifest_path = report_path("phase33_audit_manifest.json")
    assert os.path.exists(manifest_path)
    manifest = json.loads(read_text(manifest_path))
    for name, meta in manifest["files"].items():
        path = report_path(name)
        assert os.path.exists(path), f"manifest file missing: {name}"
        assert sha256_file(path) == meta["sha256"], f"hash mismatch for {name}"
