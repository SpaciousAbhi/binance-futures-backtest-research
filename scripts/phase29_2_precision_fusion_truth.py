"""
Phase 29.2 precision-fusion truth reconstruction.

This runner deliberately separates:
- protected PF 1.2 trade-set reconstruction evidence
- the current executable fusion strategy object
- dirty PF8 research material
- genuinely engine-executed recovery candidates
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUTPUTS = ROOT.parents[1] / "outputs"
sys.path.insert(0, str(ROOT))

from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.research.phase12_runner import build_p10_1_strategy
from src.research.phase28_runner import reconstruct_pf12, run_stress_scenario
from src.strategies.candidates import UniversalStrategyTemplate
from scripts.phase29_1_truth_first_recovery import (
    GenuineRecoveryRouter,
    PullbackReclaimSleeve,
    SecondRetestSleeve,
    SessionBreakoutSleeve,
    VWAPReclaimSleeve,
    add_recovery_features,
    metrics_from_trades,
    monthly_table,
    standard_stress,
)

REQUIRED_FILES = [
    "phase29_2_precision_fusion_truth_reconstruction_report.md",
    "phase29_2_pf12_fusion_lineage_map.csv",
    "phase29_2_pf12_executable_rebuild_results.csv",
    "phase29_2_pf12_trade_diff_audit.csv",
    "phase29_2_precision_fusion_compiler_spec.md",
    "phase29_2_dirty_pf8_trade_quality_audit.csv",
    "phase29_2_dirty_pf8_cluster_report.md",
    "phase29_2_multitimeframe_data_audit.csv",
    "phase29_2_sleeve_standalone_results.csv",
    "phase29_2_candidate_registry.csv",
    "phase29_2_candidate_results.csv",
    "phase29_2_recovered_router_trade_log.csv",
    "phase29_2_recovered_router_monthly_table.csv",
    "phase29_2_recovered_router_stress_table.csv",
    "phase29_2_benchmark_comparison_matrix.csv",
    "phase29_2_live_automation_readiness_audit.md",
    "phase29_2_no_lookahead_hardcoding_scan.csv",
    "phase29_2_final_status_correction.md",
    "phase29_2_audit_manifest.json",
]

METRIC_COLUMNS = [
    "net_pnl",
    "trades",
    "profit_factor",
    "max_dd_pct",
    "positive_months",
    "negative_months",
    "zero_months",
    "win_rate",
    "winners",
    "losers",
    "average_winner",
    "average_loser",
    "expectancy",
    "avg_r",
    "best_trade",
    "worst_trade",
    "combined_adverse",
]

ENGINE_SETTINGS = {
    "initial_capital": 10000.0,
    "maker_fee": 0.0002,
    "taker_fee": 0.0005,
    "slippage": 0.0005,
    "max_positions": 1,
    "cooldown_candles": 5,
}
RISK_SETTINGS = {
    "risk_limit_pct": 1.0,
    "monthly_risk_limit": 0.025,
    "risk_throttle_mode": "no_throttle",
    "emergency_pause_threshold": 0.025,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def df_hash(df: pd.DataFrame) -> str:
    if df is None:
        return sha16("NONE")
    return hashlib.sha256(df.to_csv(index=False).encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows, pd.DataFrame):
        rows = rows.to_dict("records")
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_processed(asset: str, timeframe: str) -> pd.DataFrame | None:
    path = ROOT / "data" / "processed" / f"{asset}_{timeframe}_processed.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def load_btc_1h() -> pd.DataFrame:
    df_raw = load_processed("BTCUSDT", "1h")
    if df_raw is None:
        raise FileNotFoundError("data/processed/BTCUSDT_1h_processed.csv")
    return add_recovery_features(add_indicators(df_raw))


def run_engine(df: pd.DataFrame, strategy: Any) -> dict[str, Any]:
    engine = MultiPositionBacktestEngine(**ENGINE_SETTINGS)
    return engine.run(df, strategy, RISK_SETTINGS)


def combined_adverse(trades: pd.DataFrame) -> float:
    return float(run_stress_scenario(trades, fee_mult=2.0, slip_mult=2.0, delay_slip=0.0005, missed_fill_pct=0.10)[0])


def metrics_with_stress(trades: pd.DataFrame) -> dict[str, Any]:
    m = metrics_from_trades(trades)
    m["combined_adverse"] = combined_adverse(trades)
    m["trade_log_hash"] = df_hash(trades)
    return m


def metric_row(system: str, status: str, trades: pd.DataFrame, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {"system": system, "status": status}
    row.update(metrics_with_stress(trades))
    if extra:
        row.update(extra)
    return row


def clean_metrics(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in METRIC_COLUMNS:
        out.setdefault(key, "")
    return out


def trade_key_rows(df: pd.DataFrame) -> set[tuple[Any, ...]]:
    if df is None or df.empty:
        return set()
    out = set()
    for _, row in df.iterrows():
        out.add((
            int(row.get("entry_time", 0)),
            str(row.get("side", "")),
            round(float(row.get("entry_price", 0.0)), 4),
        ))
    return out


def build_pf12_truth(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    floor = run_engine(df, build_p10_1_strategy())["trades"].copy()
    pf12 = reconstruct_pf12(floor.copy())
    if isinstance(pf12, tuple):
        pf12 = pf12[0]
    return floor, pf12.copy(), pf12.copy()


def pf12_lineage_map() -> list[dict[str, Any]]:
    return [
        {
            "source_phase": "Phase 12",
            "source_file": "src/research/phase12_runner.py",
            "candidate_family": "Precision Fusion floor fusion",
            "candidate_id_or_hash": "build_p10_1_strategy",
            "entry_rules": "A/C/D/F/G UniversalStrategyTemplate sleeves inside quality_core/activity/defensive/zero_rescue fusions",
            "exit_rules": "engine ATR TP/SL from UniversalStrategyTemplate signals",
            "filters": "Portfolio/FusionOfFusions live_metrics routing, zero-month rescue, conflict cancel",
            "timeframe": "BTCUSDT 1h",
            "router_priority": "FusionOfFusionsStrategy: activity/zero_rescue/defensive gating then union conflict cancel",
            "why_included": "Only directly executable PF-family strategy object found in code",
            "proof_artifact": "src/research/phase12_runner.py:63-86",
            "live_known_status": "EXECUTABLE_FLOOR_ONLY",
            "blocking_gap": "Does not reproduce PF1.2 protected metrics exactly",
        },
        {
            "source_phase": "Phase 17.3",
            "source_file": "src/research/phase17_3_runner.py",
            "candidate_family": "Variant C reconstructed quality core",
            "candidate_id_or_hash": "t_c from floor trade log",
            "entry_rules": "Derived by sorting completed floor trades by net_pnl, removing bottom 80, sampling 318, then shifting entry price",
            "exit_rules": "Inherited completed floor exits with synthetic entry adjustment",
            "filters": "Completed-trade net_pnl ranking",
            "timeframe": "BTCUSDT 1h trade log",
            "router_priority": "Base layer of PF1.2 reconstructed trade set",
            "why_included": "Provides 318 of 325 protected PF1.2 rows",
            "proof_artifact": "src/research/phase17_3_runner.py:174-191",
            "live_known_status": "NOT_LIVE_EXECUTABLE",
            "blocking_gap": "Uses completed trade PnL ordering and trade-log transformation",
        },
        {
            "source_phase": "Phase 17.3",
            "source_file": "src/research/phase17_3_runner.py",
            "candidate_family": "Variant B rescue overlay",
            "candidate_id_or_hash": "B-unique rows with R threshold",
            "entry_rules": "B reconstructed from floor trade log, then B-unique rows are selected when trade-record R is above threshold",
            "exit_rules": "Inherited completed floor exits with synthetic entry adjustment",
            "filters": "Post-trade R field from completed trade record",
            "timeframe": "BTCUSDT 1h trade log",
            "router_priority": "Append accepted B-unique rescue rows to Variant C",
            "why_included": "Adds 7 rows that turn Variant C into protected PF1.2",
            "proof_artifact": "src/research/phase17_3_runner.py:200-221",
            "live_known_status": "NOT_LIVE_EXECUTABLE",
            "blocking_gap": "The code calls the R filter expected-R, but it reads the completed trade R column",
        },
        {
            "source_phase": "Phase 21-28",
            "source_file": "src/research/phase21_runner.py and later copied reconstruct_pf12 functions",
            "candidate_family": "PF1.2 truth-lock reconstruction",
            "candidate_id_or_hash": "reconstruct_pf12",
            "entry_rules": "Replay Phase17.3 Variant C plus accepted B-unique trade-set transformation",
            "exit_rules": "Inherited completed exits",
            "filters": "Completed-trade net_pnl ranking plus completed-trade R threshold",
            "timeframe": "BTCUSDT 1h trade log",
            "router_priority": "Reconstructed DataFrame sorted by entry_time",
            "why_included": "Exactly reproduces PF1.2 headline values and proof hashes",
            "proof_artifact": "reports/phase29_1_pf12_truth_lock.csv",
            "live_known_status": "TRADESET_RECONSTRUCTED_EXACT",
            "blocking_gap": "No saved rule/config/router can regenerate identical trades from raw candles without trade-log reconstruction",
        },
    ]


def write_pf12_rebuild(df: pd.DataFrame, floor: pd.DataFrame, pf12: pd.DataFrame) -> tuple[dict[str, Any], str]:
    protected = metric_row(
        "PF1.2 protected reconstructed trade set",
        "TRADESET_RECONSTRUCTED_EXACT",
        pf12,
        {"proof_type": "reconstruct_pf12 replay"},
    )
    executable = metric_row(
        "PF1.2 executable floor fusion rebuild",
        "EXECUTABLE_FUSION_RUN_NOT_EXACT",
        floor,
        {"proof_type": "build_p10_1_strategy through MultiPositionBacktestEngine"},
    )

    p_keys = trade_key_rows(pf12)
    e_keys = trade_key_rows(floor)
    missing = sorted(p_keys - e_keys)
    extra = sorted(e_keys - p_keys)
    common = len(p_keys & e_keys)
    status = "PF12_TRADESET_RECONSTRUCTED_BUT_EXECUTABLE_FUSION_NOT_PROVEN"
    if len(missing) == 0 and len(extra) == 0 and round(protected["net_pnl"], 2) == round(executable["net_pnl"], 2):
        status = "PF12_EXECUTABLE_FUSION_EXACTLY_PROVEN"

    rows = [protected, executable]
    write_csv(REPORTS / "phase29_2_pf12_executable_rebuild_results.csv", rows)

    diff_rows = [
        {
            "diff_type": "summary",
            "protected_trades": len(pf12),
            "executable_trades": len(floor),
            "common_entry_side_price_keys": common,
            "missing_from_executable": len(missing),
            "extra_in_executable": len(extra),
            "status": status,
            "note": "Key uses entry_time, side, rounded entry price; adjusted reconstructed entries make exact key matching intentionally strict.",
        }
    ]
    for key in missing[:50]:
        diff_rows.append({"diff_type": "missing_protected_key", "key": json.dumps(key), "status": status})
    for key in extra[:50]:
        diff_rows.append({"diff_type": "extra_executable_key", "key": json.dumps(key), "status": status})
    write_csv(REPORTS / "phase29_2_pf12_trade_diff_audit.csv", diff_rows)
    return {"protected": protected, "executable": executable, "diff_status": status}, status


def enrich_dirty_trades(dirty: pd.DataFrame, df: pd.DataFrame) -> list[dict[str, Any]]:
    candles = df.copy()
    candles["_dt"] = pd.to_datetime(candles["open_time"], unit="ms", utc=True)
    candles = candles.set_index("_dt").sort_index()
    atr_q33 = float(candles["atr_14"].quantile(0.33)) if "atr_14" in candles else 0.0
    atr_q66 = float(candles["atr_14"].quantile(0.66)) if "atr_14" in candles else 0.0
    rows: list[dict[str, Any]] = []
    steps = [1, 3, 6, 12, 24]
    for idx, trade in dirty.reset_index(drop=True).iterrows():
        entry_text = trade.get("entry_datetime", "")
        try:
            entry_dt = pd.to_datetime(entry_text, utc=True)
        except Exception:
            entry_dt = pd.to_datetime(int(trade.get("entry_time", 0)), unit="ms", utc=True)
        pos = candles.index.searchsorted(entry_dt)
        candle = candles.iloc[min(max(pos, 0), len(candles) - 1)]
        side = str(trade.get("side", ""))
        entry_price = float(trade.get("entry_price", 0.0))
        net = float(trade.get("net_pnl", 0.0))
        r_val = float(trade.get("R", 0.0))
        hour = int(entry_dt.hour)
        session = "tokyo" if 0 <= hour < 8 else "london" if 8 <= hour < 13 else "ny" if 13 <= hour < 21 else "off"
        funding = float(candle.get("fundingRate", 0.0))
        atr = float(candle.get("atr_14", 0.0))
        adx = float(candle.get("adx", candle.get("adx_14", 0.0)))
        vwap = float(candle.get("vwap", candle.get("close", entry_price)))
        close = float(candle.get("close", entry_price))
        vwap_distance_atr = (entry_price - vwap) / atr if atr else 0.0
        bb_state = "inside"
        if "bb_upper" in candle and close > float(candle["bb_upper"]):
            bb_state = "above_upper"
        elif "bb_lower" in candle and close < float(candle["bb_lower"]):
            bb_state = "below_lower"
        if atr <= atr_q33:
            atr_regime = "low"
        elif atr >= atr_q66:
            atr_regime = "high"
        else:
            atr_regime = "mid"
        if adx >= 25:
            adx_regime = "trend"
        elif adx <= 15:
            adx_regime = "range"
        else:
            adx_regime = "neutral"

        mfe = 0.0
        mae = 0.0
        for step in steps:
            j = pos + step
            if 0 <= j < len(candles):
                future = candles.iloc[j]
                if side == "Long":
                    fav = float(future["high"]) - entry_price
                    adv = float(future["low"]) - entry_price
                else:
                    fav = entry_price - float(future["low"])
                    adv = entry_price - float(future["high"])
                mfe = max(mfe, fav)
                mae = min(mae, adv)
        stress_net = (
            float(trade.get("gross_pnl", net))
            - 2.0 * float(trade.get("fees", 0.0))
            - 2.0 * float(trade.get("slippage", 0.0))
            - float(trade.get("funding", 0.0))
        )
        if net > 200 and r_val >= 1.25:
            quality = "elite_winner"
        elif net > 75:
            quality = "acceptable_winner"
        elif net > 0:
            quality = "weak_winner"
        elif net <= -150 or stress_net <= -180:
            quality = "toxic_loser"
        elif net < 0:
            quality = "avoidable_loser"
        else:
            quality = "flat"
        source = "pf12_reconstructed_core" if str(trade.get("adjusted_entry", "")).strip() else "dirty_pf8_added_floor_trade"
        time_shift_ms = None
        try:
            time_shift_ms = int(trade.get("entry_time", 0)) - int(entry_dt.value // 1_000_000)
        except Exception:
            time_shift_ms = None
        rows.append(
            {
                "trade_id": idx,
                "source_sleeve": source,
                "entry_type": str(trade.get("strategy", "")),
                "entry_datetime": str(entry_dt),
                "session": session,
                "side": side,
                "funding_condition": "extreme" if abs(funding) >= 0.0003 else "normal",
                "funding_rate": funding,
                "adx_regime": adx_regime,
                "atr_regime": atr_regime,
                "vwap_distance_atr": vwap_distance_atr,
                "bollinger_state": bb_state,
                "retest_quality": "audit_only_not_signal",
                "time_in_trade": trade.get("hold_candles", ""),
                "mfe_path_24h": mfe,
                "mae_path_24h": mae,
                "outcome": "win" if net > 0 else "loss" if net < 0 else "flat",
                "r_multiple": r_val,
                "net_pnl": net,
                "stress_net_estimate": stress_net,
                "stress_sensitivity": stress_net - net,
                "month": str(entry_dt.to_period("M")),
                "trade_quality_bucket": quality,
                "timestamp_consistency": "SHIFTED_ENTRY_TIME" if time_shift_ms not in (0, None) else "OK",
                "time_shift_ms": time_shift_ms,
            }
        )
    write_csv(REPORTS / "phase29_2_dirty_pf8_trade_quality_audit.csv", rows)
    return rows


def write_dirty_cluster_report(rows: list[dict[str, Any]]) -> None:
    df = pd.DataFrame(rows)
    source = df.groupby("source_sleeve").agg(trades=("trade_id", "count"), pnl=("net_pnl", "sum"), stress=("stress_net_estimate", "sum")).reset_index()
    quality = df.groupby("trade_quality_bucket").agg(trades=("trade_id", "count"), pnl=("net_pnl", "sum"), stress=("stress_net_estimate", "sum")).reset_index()
    session = df.groupby("session").agg(trades=("trade_id", "count"), pnl=("net_pnl", "sum"), stress=("stress_net_estimate", "sum")).reset_index()

    def md_table(frame: pd.DataFrame) -> str:
        lines = ["| " + " | ".join(frame.columns) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
        for _, row in frame.iterrows():
            vals = []
            for value in row:
                vals.append(f"{value:.2f}" if isinstance(value, float) else str(value))
            lines.append("| " + " | ".join(vals) + " |")
        return "\n".join(lines)

    text = [
        "# Phase 29.2 Dirty PF8 Cluster Report",
        "",
        "Dirty PF8 is research material, not an accepted benchmark. The audit below is post-trade forensics only; no recovered live router is allowed to remove trades by these labels.",
        "",
        "## Source Contribution",
        md_table(source),
        "",
        "## Quality Buckets",
        md_table(quality),
        "",
        "## Session Buckets",
        md_table(session),
        "",
        "## Main Finding",
        "The extra dirty PF8 rows increase activity and gross PnL potential, but many rows carry shifted timestamps inherited from trade-frame surgery. This makes the dirty frame useful for diagnostics, not as a clean executable router.",
    ]
    write_text(REPORTS / "phase29_2_dirty_pf8_cluster_report.md", "\n".join(text) + "\n")


def multitimeframe_audit() -> list[dict[str, Any]]:
    assets = [("BTCUSDT", "1h"), ("BTCUSDT", "15m"), ("BTCUSDT", "5m"), ("ETHUSDT", "1h"), ("BNBUSDT", "1h"), ("SOLUSDT", "1h")]
    rows: list[dict[str, Any]] = []
    for asset, tf in assets:
        path = ROOT / "data" / "processed" / f"{asset}_{tf}_processed.csv"
        if not path.exists():
            rows.append({"asset": asset, "timeframe": tf, "exists": "NO", "rows": 0, "start": "", "end": "", "sha256": "", "phase29_2_use": "MISSING_NOT_USED"})
            continue
        df = pd.read_csv(path)
        start = pd.to_datetime(df["open_time"].iloc[0], unit="ms", utc=True) if len(df) else ""
        end = pd.to_datetime(df["open_time"].iloc[-1], unit="ms", utc=True) if len(df) else ""
        use = "USED_1H_ENGINE" if asset == "BTCUSDT" and tf == "1h" else "AVAILABLE_NOT_WIRED"
        if asset == "BTCUSDT" and tf == "15m":
            use = "AVAILABLE_FOR_FUTURE_CONFIRMATION_NOT_EXECUTED_IN_29_2"
        rows.append({"asset": asset, "timeframe": tf, "exists": "YES", "rows": len(df), "start": str(start), "end": str(end), "sha256": sha256_file(path), "phase29_2_use": use})
    write_csv(REPORTS / "phase29_2_multitimeframe_data_audit.csv", rows)
    return rows


def sleeve_standalone(df: pd.DataFrame) -> list[dict[str, Any]]:
    sleeves = [
        ("second_retest_1h", SecondRetestSleeve({"min_expected_r": 1.4, "retest_depth": 0.15, "tp_atr_mult": 2.2, "sl_atr_mult": 1.2})),
        ("vwap_reclaim_1h", VWAPReclaimSleeve({"min_expected_r": 1.2, "vwap_dev_atr": 0.75, "volume_mult": 0.9, "tp_atr_mult": 2.0, "sl_atr_mult": 1.2})),
        ("tokyo_london_breakout_1h", SessionBreakoutSleeve({"min_expected_r": 1.5, "body_min": 0.30, "tp_atr_mult": 2.2, "sl_atr_mult": 1.2})),
        ("pullback_reclaim_1h", PullbackReclaimSleeve({"min_expected_r": 1.5, "tp_atr_mult": 2.4, "sl_atr_mult": 1.3})),
        ("universal_vwap_deviation_return_1h", UniversalStrategyTemplate({"template_type": "vwap_deviation_return", "tp_atr_mult": 2.0, "sl_atr_mult": 1.5, "regime_filter_mode": "no_filter", "trend_filter": None})),
    ]
    rows: list[dict[str, Any]] = []
    for name, sleeve in sleeves:
        print(f"Phase29.2 standalone sleeve: {name}", flush=True)
        res = run_engine(df, sleeve)
        trades = res["trades"]
        row = {"sleeve": name, "status": "EXECUTED_ENGINE"}
        row.update(metrics_with_stress(trades))
        rows.append(row)
    write_csv(REPORTS / "phase29_2_sleeve_standalone_results.csv", rows)
    return rows


def candidate_registry() -> list[dict[str, Any]]:
    families = [
        "pf12_fusion_preserving_variant",
        "dirty_pf8_pruning_research_variant",
        "second_retest_variant",
        "vwap_reclaim_variant",
        "tokyo_london_breakout_variant",
        "pullback_reclaim_variant",
        "funding_defensive_variant",
        "ny_hardening_variant",
        "weak_continuation_exit_variant",
        "multi_timeframe_confirmation_variant",
        "expected_r_dynamic_gate_variant",
        "risk_exit_improvement_variant",
    ]
    rows: list[dict[str, Any]] = []
    for i in range(1000):
        fam = families[i % len(families)]
        params = {
            "family": fam,
            "bb_width_thresh": [0.045, 0.055, 0.06, 0.07][i % 4],
            "template_type": [
                "bollinger_expansion_breakout",
                "atr_volatility_expansion",
                "funding_extreme_reversal",
                "vwap_deviation_return",
                "london_breakout_failure",
                "mtf_breakout",
            ][i % 6],
            "min_expected_r": [1.2, 1.4, 1.6, 1.8][(i // 3) % 4],
            "tp_atr_mult": [1.8, 2.0, 2.2, 2.5, 3.0][(i // 5) % 5],
            "sl_atr_mult": [1.1, 1.2, 1.4, 1.6][(i // 7) % 4],
            "funding_threshold": [0.0002, 0.0003, 0.0004, 0.0005][(i // 11) % 4],
            "ny_expected_r": [1.5, 1.7, 1.9, 2.1][(i // 13) % 4],
            "time_stop": [12, 24, 36, 48][(i // 17) % 4],
            "volume_mult": [0.8, 1.0, 1.2][(i // 19) % 3],
        }
        pjson = json.dumps(params, sort_keys=True)
        rows.append(
            {
                "candidate_id": f"P292_{i + 1:04d}",
                "family": fam,
                "params_json": pjson,
                "candidate_hash": sha16(pjson),
                "live_known_claim": "closed-candle parameters only; performance assigned only if engine executed",
            }
        )
    write_csv(REPORTS / "phase29_2_candidate_registry.csv", rows)
    return rows


def strategy_from_candidate(row: dict[str, Any]) -> Any:
    params = json.loads(row["params_json"])
    fam = params["family"]
    if fam == "pf12_fusion_preserving_variant":
        return build_p10_1_strategy(bb_width_thresh=params["bb_width_thresh"])
    if fam in {"second_retest_variant", "expected_r_dynamic_gate_variant"}:
        return SecondRetestSleeve(params)
    if fam == "vwap_reclaim_variant":
        return VWAPReclaimSleeve(params)
    if fam == "tokyo_london_breakout_variant":
        return SessionBreakoutSleeve(params)
    if fam == "pullback_reclaim_variant":
        return PullbackReclaimSleeve(params)
    if fam in {"funding_defensive_variant", "ny_hardening_variant", "weak_continuation_exit_variant", "risk_exit_improvement_variant"}:
        sleeves = [SecondRetestSleeve(params), SessionBreakoutSleeve(params), PullbackReclaimSleeve(params)]
        return GenuineRecoveryRouter(sleeves, params)
    if fam == "multi_timeframe_confirmation_variant":
        return UniversalStrategyTemplate(
            {
                "template_type": "mtf_breakout",
                "tp_atr_mult": params["tp_atr_mult"],
                "sl_atr_mult": params["sl_atr_mult"],
                "regime_filter_mode": "no_filter",
                "trend_filter": None,
            }
        )
    return UniversalStrategyTemplate(
        {
            "template_type": params["template_type"],
            "tp_atr_mult": params["tp_atr_mult"],
            "sl_atr_mult": params["sl_atr_mult"],
            "funding_threshold": params["funding_threshold"],
            "regime_filter_mode": "no_filter",
            "trend_filter": None,
        }
    )


def execute_candidates(df: pd.DataFrame, registry: list[dict[str, Any]], pf12_metrics: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None, pd.DataFrame]:
    limit = int(os.environ.get("PHASE29_2_EXECUTION_LIMIT", "100"))
    rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    best_trades = pd.DataFrame()
    for idx, row in enumerate(registry, start=1):
        if idx <= limit:
            if idx == 1 or idx % 10 == 0:
                print(f"Phase29.2 candidate {idx}/{limit}: {row['candidate_id']}", flush=True)
            try:
                strategy = strategy_from_candidate(row)
                res = run_engine(df, strategy)
                trades = res["trades"]
                m = metrics_with_stress(trades)
                score = (
                    float(m["net_pnl"])
                    + 1400.0 * float(m["profit_factor"])
                    - 650.0 * float(m["max_dd_pct"])
                    + 8.0 * int(m["trades"])
                    + 0.12 * float(m["combined_adverse"])
                )
                result = dict(row)
                result.update(m)
                result.update(
                    {
                        "status": "EXECUTED_ENGINE",
                        "score": score,
                        "beats_pf12": "YES"
                        if float(m["net_pnl"]) > float(pf12_metrics["net_pnl"])
                        and float(m["profit_factor"]) >= float(pf12_metrics["profit_factor"])
                        else "NO",
                        "trade_log_hash": df_hash(trades),
                    }
                )
                if best is None or float(result["score"]) > float(best["score"]):
                    best = result
                    best_trades = trades.copy()
            except Exception as exc:
                result = dict(row)
                result.update({"status": "ENGINE_ERROR", "error": str(exc)[:180]})
        else:
            result = dict(row)
            result.update({"status": "REGISTERED_NOT_EXECUTED_TIMEBOXED", "note": "No metrics assigned because the engine was not run for this candidate."})
            for col in METRIC_COLUMNS + ["score", "beats_pf12", "trade_log_hash"]:
                result[col] = ""
        rows.append(clean_metrics(result))
    write_csv(REPORTS / "phase29_2_candidate_results.csv", rows)
    return rows, best, best_trades


def write_recovered_router_outputs(best: dict[str, Any] | None, trades: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if best is None:
        trades = pd.DataFrame(columns=["net_pnl", "entry_time", "side"])
    trades.to_csv(REPORTS / "phase29_2_recovered_router_trade_log.csv", index=False)
    monthly = monthly_table(trades)
    write_csv(REPORTS / "phase29_2_recovered_router_monthly_table.csv", monthly)
    stress = standard_stress(trades)
    write_csv(REPORTS / "phase29_2_recovered_router_stress_table.csv", stress)
    return monthly, stress


def benchmark_matrix(
    pf12_protected: dict[str, Any],
    pf12_executable: dict[str, Any],
    dirty_metrics: dict[str, Any],
    best: dict[str, Any] | None,
    best_stress: list[dict[str, Any]] | pd.DataFrame,
) -> list[dict[str, Any]]:
    if isinstance(best_stress, pd.DataFrame):
        best_stress = best_stress.to_dict("records")

    def row(name: str, source: str, m: dict[str, Any], sleeve_note: str, data_note: str) -> dict[str, Any]:
        stress_pnls = [float(r.get("net_pnl", 0.0)) for r in best_stress] if name == "Best real Precision Fusion recovery router" else []
        return {
            "benchmark": name,
            "source": source,
            "net_pnl": m.get("net_pnl", ""),
            "trades": m.get("trades", ""),
            "winning_trades": m.get("winners", ""),
            "losing_trades": m.get("losers", ""),
            "win_rate": m.get("win_rate", ""),
            "average_win": m.get("average_winner", ""),
            "average_loss": m.get("average_loser", ""),
            "expectancy": m.get("expectancy", ""),
            "profit_factor": m.get("profit_factor", ""),
            "max_dd_pct": m.get("max_dd_pct", ""),
            "calmar_like_pnl_over_dd": float(m.get("net_pnl", 0.0)) / float(m.get("max_dd_pct", 1.0) or 1.0),
            "combined_adverse": m.get("combined_adverse", ""),
            "worst_stress_pnl": min(stress_pnls) if stress_pnls else "",
            "worst_stress_dd": max([float(r.get("max_dd_pct", 0.0)) for r in best_stress]) if stress_pnls else "",
            "positive_months": m.get("positive_months", ""),
            "negative_months": m.get("negative_months", ""),
            "zero_months": m.get("zero_months", ""),
            "best_month": "",
            "worst_month": "",
            "monthly_median_pnl": "",
            "yearly_breakdown": "see report",
            "sleeve_contribution": sleeve_note,
            "conflict_rejections": "see router/report where available",
            "data_coverage": data_note,
        }

    rows = [
        row("PF1.2 protected benchmark", "reconstruct_pf12 trade-set replay", pf12_protected, "Variant C reconstructed core plus B rescue rows", "BTCUSDT 1h"),
        row("PF1.2 rebuilt executable fusion", "build_p10_1_strategy engine run", pf12_executable, "A/C/D/F/G FusionOfFusions floor", "BTCUSDT 1h"),
        row("Dirty PF8 no-forcing baseline", "phase29_1 dirty recompute trade frame", dirty_metrics, "PF1.2 reconstructed rows plus deterministic floor additions", "BTCUSDT 1h trade frame"),
    ]
    if best:
        rows.append(row("Best real Precision Fusion recovery router", "Phase29.2 engine-executed candidate search", best, best.get("family", ""), "BTCUSDT 1h"))
    else:
        rows.append(row("Best real Precision Fusion recovery router", "none", {}, "", ""))
    write_csv(REPORTS / "phase29_2_benchmark_comparison_matrix.csv", rows)
    return rows


def no_lookahead_scan() -> list[dict[str, Any]]:
    checks = [
        ("scripts/phase29_2_precision_fusion_truth.py", "new_runner"),
        ("src/research/phase17_3_runner.py", "legacy_pf12_origin"),
        ("src/research/phase21_runner.py", "legacy_pf12_truth_lock"),
        ("src/research/phase28_runner.py", "legacy_pf8_forced"),
    ]
    pattern_specs = [
        ("is_" + "winner", "outcome label"),
        ("future_" + "pnl", "future pnl"),
        ("future_" + "mfe", "future mfe"),
        ("future_" + "mae", "future mae"),
        ("selected_" + "trade_ids", "manual ids"),
        ("diff_" + "pnl", "forced delta"),
        ("pnl_" + "81", "target assignment"),
        ("sample(n=", "trade-log sampling"),
        ("replace=True", "replacement sampling"),
        ("sort_values(by=\"net_pnl\"", "completed PnL ordering"),
        ("row[\"R\"] > 1.40", "completed trade R gate"),
    ]
    rows: list[dict[str, Any]] = []
    for rel, scope in checks:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        if scope == "new_runner":
            start = text.find("pattern_specs = [")
            end = text.find("rows: list[dict[str, Any]] = []", start)
            if start >= 0 and end > start:
                text = text[:start] + text[end:]
        for pattern, label in pattern_specs:
            count = text.count(pattern)
            if count == 0:
                cls = "CLEAN"
            elif scope == "new_runner":
                cls = "FAIL"
            elif label in {"completed PnL ordering", "completed trade R gate", "trade-log sampling", "replacement sampling", "forced delta", "target assignment"}:
                cls = "LEGACY_FAIL_EVIDENCE"
            else:
                cls = "WARNING"
            rows.append({"file": rel, "scope": scope, "pattern_label": label, "occurrences": count, "classification": cls})
    write_csv(REPORTS / "phase29_2_no_lookahead_hardcoding_scan.csv", rows)
    return rows


def write_compiler_spec(registry: list[dict[str, Any]], executed_limit: int) -> None:
    spec = {
        "name": "phase29_2_precision_fusion_compiler",
        "definition": "PF means Precision Fusion: a deterministic router over multiple sleeves, not a single report metric.",
        "max_concurrent_positions": ENGINE_SETTINGS["max_positions"],
        "conflict_priority": ["highest_live_expected_r", "lowest_risk_distance", "fixed_family_priority", "earliest_signal"],
        "duplicate_rule": "reject same candle same side duplicates unless max_positions explicitly allows more than one",
        "candidate_registry_rows": len(registry),
        "engine_execution_limit": executed_limit,
        "unexecuted_metric_policy": "blank metrics only",
    }
    write_text(REPORTS / "phase29_2_precision_fusion_compiler_config.json", json.dumps(spec, indent=2) + "\n")
    text = """# Phase 29.2 Precision Fusion Compiler Spec

PF means Precision Fusion: a reproducible router over candidate sleeves, filters, exits, and risk rules.

## Deterministic Rules

1. Sleeve configs are serialized before execution.
2. Each metric-bearing candidate must run through `MultiPositionBacktestEngine`.
3. Same-candle duplicate same-side entries are rejected unless `max_positions` explicitly allows more than one.
4. Long/short conflicts are resolved by live-known expected R, lower risk distance, fixed family priority, then earliest signal.
5. Unexecuted candidates remain registered-only and receive blank metrics.
6. Report rows, dirty trade diagnostics, and PF1.2 reconstructed trade sets are not allowed to become accepted executable benchmarks.

## Saved Config

`reports/phase29_2_precision_fusion_compiler_config.json` stores the compiler policy used for this phase.
"""
    write_text(REPORTS / "phase29_2_precision_fusion_compiler_spec.md", text)


def write_live_audit(final_status: str) -> None:
    text = f"""# Phase 29.2 Live Automation Readiness Audit

## PF1.2 Rebuilt Executable Fusion

- Entry rules: closed-candle for the executable floor fusion.
- Exact protected PF1.2 rules: not proven as executable from saved fusion config.
- Exit rules: deterministic backtest TP/SL/time handling through the engine.
- Exchange lifecycle: no Binance shadow executor or exchange ledger proof exists.
- Status: BACKTEST_ONLY / NOT_REAL_CAPITAL_READY.

## Best Recovered PF8 Router

- Entry rules: only engine-executed candidate rows may carry metrics.
- Exit rules: engine TP/SL/time-stop style logic only.
- Tick/step/min-notional: modeled by backtest assumptions, not exchange-verified.
- Stress: standard scenarios are generated in `phase29_2_recovered_router_stress_table.csv`.
- Status: BACKTEST_ONLY / NOT_REAL_CAPITAL_READY.

## Final Live Status

`{final_status}` is not real-capital ready. REAL_CAPITAL_READY is forbidden here because no exchange-level shadow proof exists.
"""
    write_text(REPORTS / "phase29_2_live_automation_readiness_audit.md", text)


def write_final_status(final_verdict: str, pf12_status: str, best: dict[str, Any] | None, pf12_metrics: dict[str, Any]) -> None:
    best_pnl = float(best.get("net_pnl", 0.0)) if best else 0.0
    best_pf = float(best.get("profit_factor", 0.0)) if best else 0.0
    beats = best_pnl > float(pf12_metrics["net_pnl"]) and best_pf >= float(pf12_metrics["profit_factor"]) if best else False
    text = f"""# Phase 29.2 Final Status Correction

PF means Precision Fusion, not a single report number.

## Corrected Status

- PF1.2 protected trade-set metrics: retained as reconstructed research evidence.
- PF1.2 executable fusion status: `{pf12_status}`.
- Old PF7/PF8/PF8.1 claimed benchmark status: invalid forced/synthetic historical artifacts.
- Best recovered router beats PF1.2: `{beats}`.
- Final verdict: `{final_verdict}`.

## Boundary

PF1.2 cannot be called an exactly proven executable benchmark until a saved rule/config/router regenerates the exact 325 protected trades and metrics from candle data without completed-trade PnL sorting, completed-trade R filtering, or trade-log reconstruction.
"""
    write_text(REPORTS / "phase29_2_final_status_correction.md", text)


def write_report(
    final_verdict: str,
    pf12_status: str,
    pf12_rebuild: dict[str, Any],
    dirty_metrics: dict[str, Any],
    best: dict[str, Any] | None,
    registry_count: int,
    executed_count: int,
    mtf_rows: list[dict[str, Any]],
) -> None:
    protected = pf12_rebuild["protected"]
    executable = pf12_rebuild["executable"]
    best_text = "No engine-executed recovered candidate was selected." if best is None else (
        f"{best['candidate_id']} / {best['family']} / PnL {float(best['net_pnl']):.2f} / "
        f"trades {int(best['trades'])} / PF {float(best['profit_factor']):.2f} / DD {float(best['max_dd_pct']):.2f}%"
    )
    btc_15 = next((r for r in mtf_rows if r["asset"] == "BTCUSDT" and r["timeframe"] == "15m"), {})
    btc_5 = next((r for r in mtf_rows if r["asset"] == "BTCUSDT" and r["timeframe"] == "5m"), {})
    text = f"""# Phase 29.2 Precision Fusion Truth Reconstruction Report

## Executive Verdict

**FINAL VERDICT: {final_verdict}**

PF means Precision Fusion: a router/fusion of strategy sleeves, filters, exits, and risk rules. Phase 29.2 found that PF1.2 has an exact protected reconstructed trade set, but the exact PF1.2 protected benchmark is not proven as a saved executable Precision Fusion router.

## 1. Is PF1.2 Real Executable Precision Fusion Or Only A Reconstructed Trade Set?

Current status: **{pf12_status}**.

The executable floor fusion is `build_p10_1_strategy()`, but it does not reproduce the protected PF1.2 metrics. The protected PF1.2 metrics come from `reconstruct_pf12()`, which replays Variant C plus B rescue rows from completed trade logs.

## 2. PF1.2 Protected Metrics Vs Executable Floor

| Metric | Protected PF1.2 reconstructed | Executable floor fusion |
|---|---:|---:|
| Net PnL | {float(protected['net_pnl']):.2f} | {float(executable['net_pnl']):.2f} |
| Trades | {int(protected['trades'])} | {int(executable['trades'])} |
| Profit Factor | {float(protected['profit_factor']):.2f} | {float(executable['profit_factor']):.2f} |
| Max DD % | {float(protected['max_dd_pct']):.2f} | {float(executable['max_dd_pct']):.2f} |
| Months | {int(protected['positive_months'])}/{int(protected['negative_months'])}/{int(protected['zero_months'])} | {int(executable['positive_months'])}/{int(executable['negative_months'])}/{int(executable['zero_months'])} |
| Combined adverse | {float(protected['combined_adverse']):.2f} | {float(executable['combined_adverse']):.2f} |

## 3. Why The Core Path Differs

The executable floor path evaluates real candle signals. The protected PF1.2 path transforms completed floor trades: it ranks completed trades by net PnL, creates Variant B and C trade frames, adjusts entry prices, and appends B-unique rows filtered by the completed trade `R` column. That explains why the executable floor can show materially weaker metrics while the protected reconstructed trade set shows the locked PF1.2 numbers.

## 4. Dirty PF8

Dirty PF8 no-forcing baseline:

| Metric | Value |
|---|---:|
| Net PnL | {float(dirty_metrics['net_pnl']):.2f} |
| Trades | {int(dirty_metrics['trades'])} |
| Profit Factor | {float(dirty_metrics['profit_factor']):.2f} |
| Max DD % | {float(dirty_metrics['max_dd_pct']):.2f} |
| Combined adverse | {float(dirty_metrics['combined_adverse']):.2f} |

Dirty PF8 is not production quality. It is a diagnostic trade frame with useful PnL/activity clues and timestamp/lineage contamination that prevents benchmark promotion.

## 5. Recovery Search

- Registered candidates: {registry_count}
- Engine-executed candidates: {executed_count}
- Best recovered router: {best_text}

The best recovered router does not override PF1.2 unless it beats PF1.2 through engine-computed trades. Phase 29.2 did not prove that.

## 6. Multi-Timeframe Repair

- BTC 15m availability: {btc_15.get('exists', '')}, use status: {btc_15.get('phase29_2_use', '')}
- BTC 5m availability: {btc_5.get('exists', '')}, use status: {btc_5.get('phase29_2_use', '')}

Because BTC 5m is missing locally and the exact PF1.2 executable router is not proven, Phase 29.2 does not claim a completed multi-timeframe PF8.1 repair.

## 7. Final Answers

1. PF1.2 is currently an exact reconstructed trade set, not an exactly proven executable Precision Fusion.
2. The lineage is Variant C reconstructed core plus B rescue rows; see `phase29_2_pf12_fusion_lineage_map.csv`.
3. The core executable path differs because it uses live candle rules, while protected PF1.2 uses completed trade-log reconstruction.
4. The exact protected PF1.2 cannot currently be reproduced from saved fusion rules alone.
5. Dirty PF8 is PF1.2 reconstructed rows plus deterministic added floor-trade material from the no-forcing recompute.
6. Dirty PF8 has useful high-activity diagnostics but toxic and timestamp-shifted rows; see the dirty cluster report.
7. Dirty PF8 was not improved to PF8.1 quality without forcing in this phase.
8. The best real recovered router is recorded in the candidate and recovered-router files.
9. It does not beat PF1.2 unless `beats_pf12` says YES in `phase29_2_candidate_results.csv`.
10. The exact gap is saved in `phase29_2_pf12_trade_diff_audit.csv`.
11. Phase 29.3 should rebuild PF1.2 from first-principles live-known rules, starting with Variant C and B rescue signals as real strategies rather than completed-trade transformations.

## Required Proof Files

All required Phase 29.2 files are listed and hashed in `phase29_2_audit_manifest.json`.
"""
    write_text(REPORTS / "phase29_2_precision_fusion_truth_reconstruction_report.md", text)


def write_manifest(final_verdict: str, executed_count: int) -> None:
    files: dict[str, Any] = {}
    for name in REQUIRED_FILES:
        if name == "phase29_2_audit_manifest.json":
            continue
        path = REPORTS / name
        files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    manifest = {
        "phase": "29.2",
        "final_verdict": final_verdict,
        "repo_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "executed_candidate_count": executed_count,
        "manifest_hash_note": "Manifest excludes self hash to avoid recursive mutation.",
        "files": files,
    }
    write_text(REPORTS / "phase29_2_audit_manifest.json", json.dumps(manifest, indent=2) + "\n")
    if OUTPUTS.exists():
        for name in REQUIRED_FILES:
            src = REPORTS / name
            if src.exists():
                dst = OUTPUTS / name
                dst.write_bytes(src.read_bytes())


def choose_verdict(pf12_status: str, scan_rows: list[dict[str, Any]], best: dict[str, Any] | None, pf12_metrics: dict[str, Any]) -> str:
    new_fail = any(r["scope"] == "new_runner" and r["classification"] == "FAIL" and int(r["occurrences"]) > 0 for r in scan_rows)
    if new_fail:
        return "AUDIT_FAIL_FORCED_METRICS_REMAIN"
    if pf12_status == "PF12_EXECUTABLE_FUSION_EXACTLY_PROVEN":
        if best and best.get("beats_pf12") == "YES":
            return "PF12_EXECUTABLE_FUSION_EXACTLY_PROVEN_AND_REAL_PF8_RECOVERED"
        return "PF12_EXECUTABLE_FUSION_EXACTLY_PROVEN_BUT_PF8_RECOVERY_RESEARCH_ONLY"
    if pf12_status == "PF12_EXECUTABLE_FUSION_APPROXIMATELY_REBUILT":
        return "PF12_EXECUTABLE_FUSION_APPROXIMATELY_REBUILT_PF8_RESEARCH_ONLY"
    return "PF12_TRADESET_RECONSTRUCTED_BUT_EXECUTABLE_FUSION_NOT_PROVEN"


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    df = load_btc_1h()
    floor, pf12, _ = build_pf12_truth(df)
    pf12_rebuild, pf12_status = write_pf12_rebuild(df, floor, pf12)
    write_csv(REPORTS / "phase29_2_pf12_fusion_lineage_map.csv", pf12_lineage_map())

    dirty_path = REPORTS / "phase29_1_dirty_pf8_recompute_trade_log.csv"
    if dirty_path.exists():
        dirty = pd.read_csv(dirty_path)
    else:
        dirty = pf12.copy()
    dirty_metrics = metrics_with_stress(dirty)
    dirty_rows = enrich_dirty_trades(dirty, df)
    write_dirty_cluster_report(dirty_rows)

    mtf_rows = multitimeframe_audit()
    sleeve_standalone(df)

    registry = candidate_registry()
    executed_limit = int(os.environ.get("PHASE29_2_EXECUTION_LIMIT", "100"))
    write_compiler_spec(registry, executed_limit)
    results, best, best_trades = execute_candidates(df, registry, pf12_rebuild["protected"])
    best_monthly, best_stress = write_recovered_router_outputs(best, best_trades)

    benchmark_matrix(pf12_rebuild["protected"], pf12_rebuild["executable"], dirty_metrics, best, best_stress)
    scan_rows = no_lookahead_scan()
    final_verdict = choose_verdict(pf12_status, scan_rows, best, pf12_rebuild["protected"])
    write_live_audit(final_verdict)
    write_final_status(final_verdict, pf12_status, best, pf12_rebuild["protected"])
    executed_count = len([r for r in results if r["status"] == "EXECUTED_ENGINE"])
    write_report(final_verdict, pf12_status, pf12_rebuild, dirty_metrics, best, len(registry), executed_count, mtf_rows)
    write_manifest(final_verdict, executed_count)
    print(json.dumps({"final_verdict": final_verdict, "executed_candidate_count": executed_count}, indent=2))


if __name__ == "__main__":
    main()
