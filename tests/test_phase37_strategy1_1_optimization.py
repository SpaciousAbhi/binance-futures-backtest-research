import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PM = ROOT / "project_memory"
SCRIPT = ROOT / "scripts" / "phase37_strategy1_1_second_stage_optimization.py"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def report(name: str) -> Path:
    return REPORTS / name


def metrics_from_trade_log(path: Path) -> dict:
    trades = pd.read_csv(path)
    pnl = trades["net_pnl"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]
    equity = 10000.0 + pnl.cumsum()
    dd = ((equity.cummax() - equity) / equity.cummax()).fillna(0.0)
    return {
        "net_pnl": round(float(pnl.sum()), 2),
        "trades": int(len(trades)),
        "profit_factor": round(float(wins.sum() / abs(losses.sum())), 4),
        "max_drawdown_pct": round(float(dd.max() * 100), 4),
    }


def test_required_phase37_files_exist():
    required = [
        "phase37_ai_sync_and_workspace_state.csv",
        "phase37_strategy1_reproduction_lock.csv",
        "phase37_candidate_registry.csv",
        "phase37_candidate_results.csv",
        "phase37_execution_queue_status.csv",
        "phase37_multi_objective_leaderboard.csv",
        "phase37_top_candidate_integrity_audit.csv",
        "phase37_top_candidate_stress_results.csv",
        "phase37_strategy1_1_selection_decision.md",
        "phase37_strategy1_1_trade_log.csv",
        "phase37_strategy1_vs_strategy1_1_comparison.csv",
        "phase37_strategy1_1_mini_vault.md",
        "phase37_research_candidate_vaults.md",
        "phase37_strategy1_1_second_stage_optimization_report.md",
        "phase37_audit_manifest.json",
    ]
    for name in required:
        assert report(name).exists(), name


def test_strategy1_reproduction_lock_passes():
    lock = pd.read_csv(report("phase37_strategy1_reproduction_lock.csv"))
    assert lock["status"].eq("PASS").all()
    observed = dict(zip(lock["metric"], lock["observed"]))
    assert float(observed["net_pnl"]) == 11205.20
    assert int(observed["trades"]) == 557
    assert float(observed["profit_factor"]) == 1.2522
    assert float(observed["max_drawdown_pct"]) == 16.2186


def test_candidate_registry_and_execution_accounting():
    registry = pd.read_csv(report("phase37_candidate_registry.csv"))
    results = pd.read_csv(report("phase37_candidate_results.csv"))
    queue = pd.read_csv(report("phase37_execution_queue_status.csv"))
    assert len(registry) >= 3000
    assert registry["candidate_id"].is_unique
    assert registry["candidate_hash"].is_unique
    executed = results[results["execution_status"] == "ENGINE_EXECUTED"]
    unexecuted = results[results["execution_status"] == "REGISTERED_NOT_EXECUTED_RUNTIME_LIMIT"]
    assert len(executed) == 500
    assert len(unexecuted) == len(registry) - 500
    assert executed["net_pnl"].notna().all()
    assert unexecuted["net_pnl"].isna().all()
    assert int(queue.loc[queue["status"] == "engine_executed", "count"].iloc[0]) == 500


def test_strategy11_selected_candidate_metrics_reconcile():
    decision = report("phase37_strategy1_1_selection_decision.md").read_text(encoding="utf-8")
    assert "P37_CAND_0357" in decision
    assert "HIGH_PNL_PROMOTION" in decision
    results = pd.read_csv(report("phase37_candidate_results.csv"))
    selected = results[results["candidate_id"] == "P37_CAND_0357"].iloc[0]
    metrics = metrics_from_trade_log(report("phase37_strategy1_1_trade_log.csv"))
    assert metrics["net_pnl"] == round(float(selected["net_pnl"]), 2)
    assert metrics["trades"] == int(selected["trades"])
    assert metrics["profit_factor"] == round(float(selected["profit_factor"]), 4)
    assert metrics["max_drawdown_pct"] == round(float(selected["max_drawdown_pct"]), 4)
    assert float(selected["net_pnl"]) > 11205.20
    assert float(selected["profit_factor"]) >= 1.30
    assert float(selected["max_drawdown_pct"]) <= 14
    assert int(float(selected["stress_pass_count"])) >= 8


def test_strategy1_vs_strategy11_comparison_improves_required_fields():
    comparison = pd.read_csv(report("phase37_strategy1_vs_strategy1_1_comparison.csv"))
    values = {row.metric: row for row in comparison.itertuples(index=False)}
    assert values["net_pnl"].strategy1_1 > values["net_pnl"].strategy1
    assert values["profit_factor"].strategy1_1 > values["profit_factor"].strategy1
    assert values["max_drawdown_pct"].strategy1_1 < values["max_drawdown_pct"].strategy1
    assert values["stress_pass_count"].strategy1_1 >= 8
    assert values["combined_adverse_pnl"].strategy1_1 > values["combined_adverse_pnl"].strategy1


def test_top_candidate_integrity_and_stress_exist():
    audit = pd.read_csv(report("phase37_top_candidate_integrity_audit.csv"))
    stress = pd.read_csv(report("phase37_top_candidate_stress_results.csv"))
    assert audit["status"].eq("PASS").all()
    assert stress.groupby("system")["scenario"].nunique().eq(15).all()
    assert "P37_CAND_0357" in set(stress["system"])


def test_phase37_script_has_no_forbidden_construction_patterns():
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        ".sample(",
        "replace=True",
        "is_winner",
        "future_pnl",
        "future_return",
        "future_mfe",
        "future_mae",
        "forced_pnl",
        "pnl_81_calc",
    ]
    for pattern in forbidden:
        assert pattern not in text


def test_manifest_hashes_match_disk_files():
    manifest = json.loads(report("phase37_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["verdict"] == "PHASE37_PASS_STRATEGY1_1_PROMOTED"
    assert manifest["rules"]["no_forced_metrics"] is True
    assert manifest["rules"]["no_trade_log_only_promotion"] is True
    assert manifest["rules"]["strategy1_reproduced"] is True
    for name, expected_hash in manifest["files"].items():
        path = report(name)
        assert path.exists(), name
        assert sha256_file(path) == expected_hash


def test_project_memory_updated_for_phase37():
    handoff = (PM / "CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    next_plan = (PM / "NEXT_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "Latest Completed Phase: Phase 37" in handoff
    assert "Strategy #1 remains Combined Router v1" in handoff
    assert "Strategy #1.1 promoted: P37_CAND_0357" in handoff
    assert "NOT_REAL_CAPITAL_READY" in handoff
    assert "Phase 38" in next_plan or "Latest Completed Phase: Phase 38" in handoff
