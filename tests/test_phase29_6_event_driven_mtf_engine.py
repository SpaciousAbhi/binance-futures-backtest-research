import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNNER = ROOT / "scripts" / "phase29_6_event_driven_mtf_engine.py"

REQUIRED = [
    "phase29_6_true_5m_event_driven_mtf_engine_report.md",
    "phase29_6_execution_rule_recovery_audit.csv",
    "phase29_6_mtf_data_alignment_audit.csv",
    "phase29_6_engine_design_spec.md",
    "phase29_6_entry_model_results.csv",
    "phase29_6_exit_model_results.csv",
    "phase29_6_router_conflict_audit.csv",
    "phase29_6_variant_c_mtf_engine_results.csv",
    "phase29_6_variant_b_mtf_engine_results.csv",
    "phase29_6_pf12_mtf_engine_results.csv",
    "phase29_6_pf12_mtf_trade_log.csv",
    "phase29_6_pf8_sleeve_results.csv",
    "phase29_6_finalist_stress_results.csv",
    "phase29_6_monthly_yearly_tables.csv",
    "phase29_6_trade_traceability.csv",
    "phase29_6_live_automation_audit.md",
    "phase29_6_audit_manifest.json",
]


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (REPORTS / name).open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_phase29_6_required_files_exist():
    for name in REQUIRED:
        assert (REPORTS / name).exists(), f"missing {name}"


def test_phase29_6_manifest_hashes_match_disk():
    manifest = json.loads((REPORTS / "phase29_6_audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["final_verdict"] == "PF12_MTF_ENGINE_MAJOR_PROGRESS_BUT_NOT_RECOVERED"
    assert manifest["rules"]["accepted_trade_source"] == "FiveMinuteEventEngine"
    for name, meta in manifest["files"].items():
        assert name != "phase29_6_audit_manifest.json"
        assert file_hash(REPORTS / name) == meta["sha256"]


def test_phase29_6_runner_has_no_forced_metrics_or_fake_sampling():
    source = RUNNER.read_text(encoding="utf-8")
    for forbidden in [
        "29386.59",
        "30580.40",
        "31250.80",
        "21684.99",
        "19589.91",
        "20455.48",
        ".sample(",
        "is_winner",
        "future_pnl",
        "future_r",
        "future_mfe",
        "future_mae",
        "selected_trade_ids",
        "forced_pnl",
    ]:
        assert forbidden not in source


def test_phase29_6_execution_rule_and_design_files_document_sl_first():
    rules = read_csv("phase29_6_execution_rule_recovery_audit.csv")
    assert rules
    assert any(r["rule_type"] == "same_candle" for r in rules)
    design = (REPORTS / "phase29_6_engine_design_spec.md").read_text(encoding="utf-8")
    assert "same-candle priority is SL_FIRST" in design


def test_phase29_6_mtf_alignment_file_has_no_failed_samples():
    rows = read_csv("phase29_6_mtf_data_alignment_audit.csv")
    assert rows
    dataset_rows = [r for r in rows if r["row_type"] == "dataset"]
    assert {r["timeframe"] for r in dataset_rows} >= {"1h", "15m", "5m"}
    assert all(int(r["duplicate_candles"]) == 0 for r in dataset_rows)
    sample_rows = [r for r in rows if r["row_type"] == "sample_alignment"]
    assert sample_rows
    assert all(r["alignment_status"] == "PASS_NO_TRIGGER_BEFORE_SETUP_CLOSE" for r in sample_rows)


def test_phase29_6_pf12_trade_log_obeys_event_ordering_and_has_risk_levels():
    trades = read_csv("phase29_6_pf12_mtf_trade_log.csv")
    assert trades
    for row in trades:
        assert int(float(row["setup_close_time"])) <= int(float(row["trigger_time"]))
        assert int(float(row["trigger_time"])) >= int(float(row["setup_close_time"]))
        assert int(float(row["entry_time"])) >= int(float(row["trigger_close_time"]))
        assert int(float(row["exit_time"])) >= int(float(row["entry_time"]))
        assert row["stop_loss"] not in {"", "nan"}
        assert row["take_profit"] not in {"", "nan"}
        assert row["same_candle_priority"] == "SL_FIRST"


def test_phase29_6_pf12_metrics_reconcile_with_trade_log():
    metrics = read_csv("phase29_6_pf12_mtf_engine_results.csv")[0]
    trades = read_csv("phase29_6_pf12_mtf_trade_log.csv")
    assert int(float(metrics["trades"])) == len(trades)
    pnl = sum(float(r["net_pnl"]) for r in trades)
    assert abs(pnl - float(metrics["net_pnl"])) < 0.01
    assert metrics["status"] == "EVENT_DRIVEN_5M_ENGINE"


def test_phase29_6_monthly_table_sums_to_trade_log():
    trades = read_csv("phase29_6_pf12_mtf_trade_log.csv")
    table = read_csv("phase29_6_monthly_yearly_tables.csv")
    monthly = [r for r in table if r["table_type"] == "monthly"]
    assert monthly
    trade_pnl = sum(float(r["net_pnl"]) for r in trades)
    month_pnl = sum(float(r["pnl"]) for r in monthly)
    assert abs(trade_pnl - month_pnl) < 0.01


def test_phase29_6_stress_and_conflict_outputs_exist():
    stress = read_csv("phase29_6_finalist_stress_results.csv")
    assert len(stress) >= 15
    scenarios = {r["scenario"] for r in stress}
    assert {"normal", "double fees", "triple fees", "double slippage", "triple slippage", "combined adverse"} <= scenarios
    conflicts = read_csv("phase29_6_router_conflict_audit.csv")
    assert conflicts
    assert any(r.get("decision") == "ACCEPTED_FILLED" for r in conflicts)


def test_phase29_6_live_audit_not_real_capital_ready():
    text = (REPORTS / "phase29_6_live_automation_audit.md").read_text(encoding="utf-8")
    assert "NOT_REAL_CAPITAL_READY" in text
    assert "no exchange order ledger exists" in text
