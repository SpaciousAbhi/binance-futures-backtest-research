import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PM = ROOT / "project_memory"
SCRIPT = ROOT / "scripts" / "phase36_strategy1_decomposition_repair.py"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def report(name: str) -> Path:
    return REPORTS / name


def test_required_phase36_files_exist():
    required = [
        "phase36_ai_sync_and_workspace_state.csv",
        "phase36_strategy1_reproduction_lock.csv",
        "phase36_strategy1_internal_decomposition.csv",
        "phase36_strategy1_edge_map.md",
        "phase36_ablation_results.csv",
        "phase36_repair_module_results.csv",
        "phase36_strategy1_1_candidate_results.csv",
        "phase36_candidate_expansion_registry.csv",
        "phase36_candidate_expansion_results.csv",
        "phase36_candidate_expansion_top_trade_logs_index.csv",
        "phase36_integrity_audit.csv",
        "phase36_stress_comparison.csv",
        "phase36_monthly_comparison.csv",
        "phase36_strategy1_1_mini_vault.md",
        "phase36_strategy1_decomposition_repair_and_breakthrough_search_report.md",
        "phase36_audit_manifest.json",
    ]
    for name in required:
        assert report(name).exists(), name


def test_strategy1_reproduction_lock_passes_exactly():
    lock = pd.read_csv(report("phase36_strategy1_reproduction_lock.csv"))
    assert lock["status"].eq("PASS").all()
    observed = dict(zip(lock["metric"], lock["observed"]))
    assert float(observed["net_pnl"]) == 11205.20
    assert int(observed["trades"]) == 557
    assert float(observed["profit_factor"]) == 1.2522
    assert float(observed["max_drawdown_pct"]) == 16.2186
    assert int(observed["zero_months"]) == 0


def test_decomposition_identifies_live_known_edge_and_weakness():
    decomposition = pd.read_csv(report("phase36_strategy1_internal_decomposition.csv"))
    source = decomposition[decomposition["group"] == "source_sleeve"]
    assert not source.empty
    bb_long = source[source["bucket"] == "BB Expansion Long"].iloc[0]
    low_activity_long = source[source["bucket"] == "Low-Activity Filler Long"].iloc[0]
    assert float(bb_long["net_pnl"]) > 0
    assert float(low_activity_long["net_pnl"]) < 0


def test_ablation_and_repair_outputs_are_engine_runs():
    ablation = pd.read_csv(report("phase36_ablation_results.csv"))
    repair = pd.read_csv(report("phase36_repair_module_results.csv"))
    assert len(ablation) >= 16
    assert len(repair) >= 8
    assert ablation["live_known"].eq("YES").all()
    assert repair["live_known"].eq("YES").all()
    assert (ablation["trades"].astype(int) > 0).all()
    assert (repair["trades"].astype(int) > 0).all()


def test_strategy11_candidates_have_trade_logs_and_are_not_promoted():
    results = pd.read_csv(report("phase36_strategy1_1_candidate_results.csv"))
    assert len(results) >= 4
    assert results["promotion_status"].eq("RESEARCH_ONLY_NOT_PROMOTED").all()
    for row in results.itertuples(index=False):
        path = ROOT / row.trade_log_path
        assert path.exists(), row.trade_log_path
        trades = pd.read_csv(path)
        assert len(trades) == int(row.trades)
        assert round(float(trades["net_pnl"].sum()), 2) == round(float(row.net_pnl), 2)
        assert (trades["exit_time"] >= trades["entry_time"]).all()


def test_candidate_registry_and_execution_accounting():
    registry = pd.read_csv(report("phase36_candidate_expansion_registry.csv"))
    results = pd.read_csv(report("phase36_candidate_expansion_results.csv"))
    assert len(registry) >= 2000
    assert registry["candidate_id"].is_unique
    assert registry["candidate_hash"].is_unique
    executed = results[results["execution_status"] == "ENGINE_EXECUTED"]
    unexecuted = results[results["execution_status"] == "REGISTERED_NOT_EXECUTED_RUNTIME_LIMIT"]
    assert len(executed) == 20
    assert len(unexecuted) == len(results) - len(executed)
    assert executed["net_pnl"].notna().all()
    assert unexecuted["net_pnl"].isna().all()


def test_integrity_and_live_status():
    audit = pd.read_csv(report("phase36_integrity_audit.csv"))
    assert audit["status"].eq("PASS").all()
    assert "no_trade_log_filter_promotion" in set(audit["check"])
    assert "not_real_capital_ready" in set(audit["check"])
    main_report = report("phase36_strategy1_decomposition_repair_and_breakthrough_search_report.md").read_text(encoding="utf-8")
    assert "NOT_REAL_CAPITAL_READY" in main_report
    assert "No benchmark replacement occurred" in main_report


def test_phase36_script_has_no_forbidden_construction_patterns():
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
    manifest = json.loads(report("phase36_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["verdict"] == "PHASE36_PARTIAL_PASS_INTERNAL_EDGE_MAPPED_NO_UPGRADE"
    assert manifest["rules"]["no_forced_metrics"] is True
    assert manifest["rules"]["no_trade_log_only_promotion"] is True
    assert manifest["rules"]["strategy1_reproduced"] is True
    for name, expected_hash in manifest["files"].items():
        path = report(name)
        assert path.exists(), name
        assert sha256_file(path) == expected_hash


def test_project_memory_updated_for_phase36():
    handoff = (PM / "CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    next_plan = (PM / "NEXT_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "Latest Completed Phase: Phase 36" in handoff or "Latest Completed Phase: Phase 37" in handoff
    assert "Strategy #1 remains Combined Router v1" in handoff
    assert "Strategy #1.1 promoted: NO" in handoff or "Strategy #1.1 promoted: P37_CAND_0357" in handoff
    assert "NOT_REAL_CAPITAL_READY" in handoff
    assert "Phase 37" in next_plan
