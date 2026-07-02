"""Phase 34 Strategy #1 vault and candidate discovery tests."""
import hashlib
import json
import os

import pandas as pd


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS = os.path.join(ROOT, "reports")
PM = os.path.join(ROOT, "project_memory")
INITIAL_CAPITAL = 10000.0


def report(name: str) -> str:
    return os.path.join(REPORTS, name)


def memory(name: str) -> str:
    return os.path.join(PM, name)


def read(path: str) -> str:
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
    drawdown = ((equity.cummax() - equity) / equity.cummax()).max() * 100
    return {
        "net_pnl": round(float(pnl.sum()), 2),
        "trades": int(len(df)),
        "profit_factor": round(float(wins.sum()) / abs(float(losses.sum())), 4),
        "max_drawdown_pct": round(float(drawdown), 4),
        "winning_trades": int((pnl > 0).sum()),
        "losing_trades": int((pnl <= 0).sum()),
    }


def test_strategy_1_vault_exists_and_identifies_strategy():
    path = report("phase34_strategy_1_combined_router_v1_vault.md")
    assert os.path.exists(path)
    text = read(path)
    assert "Strategy #1" in text
    assert "Combined Router v1" in text
    assert "NOT_REAL_CAPITAL_READY" in text
    assert "CAND_0190 exact parameters" in text


def test_strategy_1_trade_log_copy_is_exact_and_reconciles():
    copy_path = report("phase34_strategy_1_trade_log_copy.csv")
    source_path = report("phase33_1_baseline_recovery_trade_log.csv")
    assert os.path.exists(copy_path)
    assert os.path.exists(source_path)
    assert sha256_file(copy_path) == sha256_file(source_path)
    metrics = compute_metrics(pd.read_csv(copy_path))
    assert metrics["net_pnl"] == 11205.2
    assert metrics["trades"] == 557
    assert metrics["profit_factor"] == 1.2522
    assert metrics["max_drawdown_pct"] == 16.2186
    assert metrics["winning_trades"] == 301
    assert metrics["losing_trades"] == 256


def test_reproduction_metrics_confirm_strategy_1():
    df = pd.read_csv(report("phase34_strategy_1_reproduction_metrics.csv"))
    values = dict(zip(df["metric"], df["value"].astype(str)))
    assert float(values["net_pnl"]) == 11205.2
    assert int(float(values["trades"])) == 557
    assert float(values["profit_factor"]) == 1.2522
    assert float(values["max_drawdown_pct"]) == 16.2186
    assert int(float(values["positive_months"])) == 52
    assert int(float(values["negative_months"])) == 25
    assert int(float(values["zero_months"])) == 0


def test_integrity_and_live_audit_exist():
    integrity = pd.read_csv(report("phase34_strategy_1_integrity_audit.csv"))
    assert not integrity[integrity["status"] == "FAIL"].any().any()
    live = read(report("phase34_strategy_1_live_execution_audit.md"))
    assert "BACKTEST_VERIFIED_NOT_SHADOWED" in live
    assert "NOT_REAL_CAPITAL_READY" in live


def test_stress_retest_truth_is_locked():
    df = pd.read_csv(report("phase34_strategy_1_stress_retest.csv"))
    assert len(df) == 15
    assert int((df["verdict"] == "PASS").sum()) == 7
    assert int((df["verdict"] == "FAIL").sum()) == 8
    combined = df[df["scenario"] == "combined adverse"].iloc[0]
    assert round(float(combined["net_pnl"]), 2) == -39138.38


def test_candidate_registry_and_results_counts():
    registry = pd.read_csv(report("phase34_candidate_registry.csv"))
    results = pd.read_csv(report("phase34_candidate_results.csv"))
    assert len(registry) >= 2000
    assert registry["candidate_id"].nunique() == len(registry)
    assert registry["candidate_hash"].nunique() == len(registry)
    executed = results[results["execution_status"] == "ENGINE_TRADE_LOG_EXECUTED_FILTER_REPLAY"]
    unexecuted = results[results["execution_status"] == "REGISTERED_NOT_EXECUTED"]
    assert len(executed) >= 300
    assert len(unexecuted) >= 1700
    assert executed["net_pnl"].notna().all()
    assert unexecuted["net_pnl"].isna().all()


def test_cluster_diversity_exceeds_target():
    clusters = pd.read_csv(report("phase34_candidate_cluster_report.csv"))
    assert clusters["behavior_cluster"].nunique() >= 50


def test_selected_candidate_building_blocks_have_unique_trade_logs():
    summary = pd.read_csv(report("phase34_top_candidate_trade_logs_summary.csv"))
    assert len(summary) >= 4
    assert summary["trade_log_hash"].nunique() == len(summary)
    for _, row in summary.iterrows():
        path = os.path.join(ROOT, row["selected_trade_log_path"])
        assert os.path.exists(path)
        trades = pd.read_csv(path)
        assert len(trades) == int(row["trades"])
        assert sha256_file(path) == row["trade_log_hash"]


def test_selected_candidate_report_and_diagnostic_preview_exist():
    selected = read(report("phase34_selected_candidate_building_blocks.md"))
    assert "Phase 34 Selected Candidate Building Blocks" in selected
    assert "not yet a standalone signal generator" in selected
    preview = pd.read_csv(report("phase34_diagnostic_fusion_preview.csv"))
    assert "DIAGNOSTIC_ONLY_NOT_PROMOTED" in set(preview["classification"])


def test_project_memory_mentions_phase34_vault_and_no_promotion():
    handoff = read(memory("CURRENT_HANDOFF.md"))
    assert "Strategy #1 remains Combined Router v1" in handoff or "Strategy #1 is Combined Router v1" in handoff
    assert "phase34_strategy_1_combined_router_v1_vault.md" in handoff
    assert "No final fusion was promoted" in handoff
    assert "NOT_REAL_CAPITAL_READY" in handoff


def test_manifest_hashes_match_disk_files():
    manifest = json.loads(read(report("phase34_audit_manifest.json")))
    assert manifest["verdict"] == "PHASE34_PASS_STRATEGY1_VAULT_LOCKED_AND_CANDIDATES_FOUND"
    for name, meta in manifest["files"].items():
        path = report(name)
        assert os.path.exists(path), name
        assert sha256_file(path) == meta["sha256"], name
