import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PM = ROOT / "project_memory"
SCRIPT = ROOT / "scripts" / "phase35_independent_sleeve_conversion.py"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def report(name: str) -> Path:
    return REPORTS / name


def compute_metrics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"net_pnl": 0.0, "trades": 0, "profit_factor": 0.0, "max_drawdown_pct": 0.0}
    pnl = trades["net_pnl"].astype(float)
    gp = pnl[pnl > 0].sum()
    gl = abs(pnl[pnl < 0].sum())
    equity = 10000 + pnl.cumsum()
    dd = ((equity.cummax() - equity) / equity.cummax()).max() * 100
    return {
        "net_pnl": round(float(pnl.sum()), 2),
        "trades": int(len(trades)),
        "profit_factor": round(float(gp / gl), 4) if gl else 0.0,
        "max_drawdown_pct": round(float(dd), 4),
    }


def test_required_phase35_files_exist():
    required = [
        "phase35_building_block_decoder.csv",
        "phase35_signal_level_sleeve_specs.md",
        "phase35_independent_sleeve_results.csv",
        "phase35_independent_sleeve_trade_log_index.csv",
        "phase35_independent_sleeve_stress_summary.csv",
        "phase35_independent_sleeve_monthly_summary.csv",
        "phase35_independent_sleeve_integrity_audit.csv",
        "phase35_strategy_2_to_6_candidate_vaults.md",
        "phase35_strategy_correlation_and_complementarity.csv",
        "phase35_diagnostic_fusion_preview.csv",
        "phase35_independent_sleeve_conversion_and_fusion_readiness_report.md",
        "phase35_audit_manifest.json",
    ]
    for name in required:
        assert report(name).exists(), name


def test_strategy1_remains_reconciled_from_phase34_trade_log():
    trades = pd.read_csv(report("phase34_strategy_1_trade_log_copy.csv"))
    metrics = compute_metrics(trades)
    assert metrics["net_pnl"] == 11205.20
    assert metrics["trades"] == 557
    assert metrics["profit_factor"] == 1.2522
    assert metrics["max_drawdown_pct"] == 16.2186


def test_building_block_decoder_covers_selected_phase34_ids():
    decoder = pd.read_csv(report("phase35_building_block_decoder.csv"))
    assert set(decoder["phase34_candidate_id"]) == {"P34_0217", "P34_0007", "P34_0219", "P34_0218", "P34_0002"}
    assert decoder["critical_caveat"].str.contains("Phase 34 result was a deterministic gate").all()


def test_independent_sleeve_results_are_engine_runs_and_not_promoted():
    results = pd.read_csv(report("phase35_independent_sleeve_results.csv"))
    assert len(results) >= 6
    assert results["execution_status"].eq("INDEPENDENT_SIGNAL_LEVEL_ENGINE_RUN").all()
    assert not results["candidate_status"].isin(["PRIMARY_CANDIDATE_PASS", "SECONDARY_CANDIDATE_PASS"]).any()
    assert (results["candidate_status"] == "RESEARCH_ONLY_NOT_SELECTED").all()


def test_sleeve_trade_logs_exist_and_metrics_reconcile():
    results = pd.read_csv(report("phase35_independent_sleeve_results.csv"))
    for row in results.itertuples(index=False):
        path = ROOT / row.trade_log_path
        assert path.exists(), row.trade_log_path
        trades = pd.read_csv(path)
        metrics = compute_metrics(trades)
        assert metrics["trades"] == int(row.trades)
        assert metrics["net_pnl"] == round(float(row.net_pnl), 2)
        assert metrics["profit_factor"] == round(float(row.profit_factor), 4)
        assert metrics["max_drawdown_pct"] == round(float(row.max_drawdown_pct), 4)
        if not trades.empty:
            assert (trades["exit_time"] >= trades["entry_time"]).all()


def test_integrity_audit_passes_for_all_sleeves():
    audit = pd.read_csv(report("phase35_independent_sleeve_integrity_audit.csv"))
    assert not audit.empty
    assert audit["status"].eq("PASS").all()
    assert "independent_signal_level_execution" in set(audit["check"])
    assert "no_trade_log_filter_promotion" in set(audit["check"])


def test_stress_summary_exists_for_all_scenarios():
    stress = pd.read_csv(report("phase35_independent_sleeve_stress_summary.csv"))
    results = pd.read_csv(report("phase35_independent_sleeve_results.csv"))
    assert set(stress["system"]) == set(results["sleeve_id"])
    assert stress.groupby("system")["scenario"].nunique().eq(15).all()


def test_candidate_vaults_report_no_strategy_assignment():
    text = report("phase35_strategy_2_to_6_candidate_vaults.md").read_text(encoding="utf-8")
    assert "No independent sleeve passed" in text
    assert "No Strategy #2-#6 candidate was assigned" in text


def test_diagnostic_fusion_is_not_promoted():
    preview = pd.read_csv(report("phase35_diagnostic_fusion_preview.csv"))
    assert len(preview) == 1
    row = preview.iloc[0]
    assert row["fusion_name"] == "NO_PASSING_SLEEVES"
    assert row["classification"] == "DIAGNOSTIC_ONLY_NOT_PROMOTED"


def test_phase35_script_has_no_forbidden_construction_patterns():
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
    manifest = json.loads(report("phase35_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["verdict"] == "PHASE35_RESEARCH_ONLY_BUILDING_BLOCKS_NOT_YET_EXECUTABLE"
    assert manifest["rules"]["no_trade_log_only_filter_promotion"] is True
    for name, expected_hash in manifest["files"].items():
        path = report(name)
        assert path.exists(), name
        assert sha256_file(path) == expected_hash


def test_project_memory_updated_for_phase35():
    handoff = (PM / "CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    next_plan = (PM / "NEXT_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert any(
        marker in handoff
        for marker in ["Latest Completed Phase: Phase 35", "Latest Completed Phase: Phase 36", "Latest Completed Phase: Phase 37"]
    )
    assert "Strategy #1 remains Combined Router v1" in handoff
    assert "Selected Strategy #2-#6 candidates: none" in handoff or "Phase 35 selected Strategy #2-#6 candidates: none" in handoff
    assert "NOT_REAL_CAPITAL_READY" in handoff
    assert any(marker in next_plan for marker in ["Phase 36", "Phase 37", "Phase 38"])
