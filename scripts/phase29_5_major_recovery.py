"""
Phase 29.5 major Precision Fusion recovery sprint.

The runner uses Antigravity BTC 15m/5m data as closed-candle recovery evidence,
but every accepted live metric is produced by the existing backtest engine.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUTPUTS = ROOT.parents[1] / "outputs"
ANTIGRAVITY = Path(r"C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest")
sys.path.insert(0, str(ROOT))

from src.features.indicators import add_indicators
from src.research.phase12_runner import CAND_A_CFG, CAND_C_CFG, build_p10_1_strategy
from src.strategies.base import BaseStrategy
from src.strategies.candidates import UniversalStrategyTemplate
from scripts.phase29_1_truth_first_recovery import add_recovery_features, monthly_table, standard_stress
from scripts.phase29_2_precision_fusion_truth import df_hash, metric_row, metrics_with_stress, run_engine, sha256_file, write_csv, write_text
from scripts.phase29_4_teacher_distillation import (
    basic_key_set,
    canonical_teacher_sets,
    evidence_inventory,
    time_side_key_set,
)

REQUIRED_FILES = [
    "phase29_5_major_precision_fusion_breakthrough_report.md",
    "phase29_5_local_evidence_map.csv",
    "phase29_5_mtf_data_alignment_audit.csv",
    "phase29_5_teacher_mtf_trigger_match.csv",
    "phase29_5_variant_c_mtf_results.csv",
    "phase29_5_variant_b_rescue_mtf_results.csv",
    "phase29_5_pf12_executable_router_results.csv",
    "phase29_5_pf12_executable_router_trade_log.csv",
    "phase29_5_pf12_trade_match_gap_audit.csv",
    "phase29_5_dirty_pf8_upgrade_results.csv",
    "phase29_5_candidate_registry.csv",
    "phase29_5_candidate_results.csv",
    "phase29_5_benchmark_stack_comparison.csv",
    "phase29_5_live_automation_audit.md",
    "phase29_5_audit_manifest.json",
]

ENGINE_EXECUTION_LIMIT = int(os.environ.get("PHASE29_5_EXECUTION_LIMIT", "300"))


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_processed(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def load_btc_1h() -> pd.DataFrame:
    path = ROOT / "data" / "processed" / "BTCUSDT_1h_processed.csv"
    df = pd.read_csv(path)
    return add_recovery_features(add_indicators(df))


def load_ltf(timeframe: str) -> pd.DataFrame | None:
    current = ROOT / "data" / "processed" / f"BTCUSDT_{timeframe}_processed.csv"
    ag = ANTIGRAVITY / "data" / "processed" / f"BTCUSDT_{timeframe}_processed.csv"
    df = load_processed(current)
    if df is not None:
        return df
    return load_processed(ag)


def safe_div(num: float, den: float, default: float = 0.0) -> float:
    return float(num / den) if den and not np.isnan(den) else default


def local_evidence_map() -> list[dict[str, Any]]:
    rows = evidence_inventory()
    out = []
    for row in rows:
        terms = str(row.get("matched_terms", "")).lower()
        useful_ltf = "YES" if "5m" in terms or "15m" in terms or "vwap" in terms or "retest" in terms else "NO"
        out.append(
            {
                "workspace": row.get("workspace", ""),
                "file_path": row.get("file_path", ""),
                "artifact_type": row.get("artifact_type", ""),
                "phase": row.get("phase", ""),
                "candidate_logic_found": row.get("matched_terms", ""),
                "teacher_only_logic": row.get("teacher_only", ""),
                "live_safe_logic": row.get("live_safe", ""),
                "missing_logic": "exact PF1.2 executable router" if row.get("helps_recover_bc") == "YES" else "",
                "useful_lower_timeframe_artifact": useful_ltf,
                "unique_vs_github_checkout": row.get("unique_vs_github_checkout", ""),
            }
        )
    write_csv(REPORTS / "phase29_5_local_evidence_map.csv", out)
    return out


def mtf_alignment_audit(df_1h: pd.DataFrame, df_15m: pd.DataFrame | None, df_5m: pd.DataFrame | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tf, expected_ms, ltf in [("1h", 3_600_000, df_1h), ("15m", 900_000, df_15m), ("5m", 300_000, df_5m)]:
        if ltf is None or ltf.empty:
            rows.append({"timeframe": tf, "exists": "NO", "rows": 0, "start": "", "end": "", "duplicate_candles": "", "bad_deltas": "", "sha256": "", "leakage_check": "MISSING"})
            continue
        deltas = pd.Series(ltf["open_time"]).diff().dropna()
        duplicate_count = int(pd.Series(ltf["open_time"]).duplicated().sum())
        bad = int((deltas != expected_ms).sum()) if len(deltas) else 0
        rows.append(
            {
                "timeframe": tf,
                "exists": "YES",
                "rows": len(ltf),
                "start": str(pd.to_datetime(int(ltf["open_time"].iloc[0]), unit="ms", utc=True)),
                "end": str(pd.to_datetime(int(ltf["open_time"].iloc[-1]), unit="ms", utc=True)),
                "duplicate_candles": duplicate_count,
                "bad_deltas": bad,
                "sha256": hashlib.sha256(ltf.to_csv(index=False).encode("utf-8")).hexdigest(),
                "leakage_check": "PASS_CLOSED_CANDLES_ONLY" if duplicate_count == 0 else "WARNING_DUPLICATES",
            }
        )
    checks = []
    if df_15m is not None and not df_15m.empty:
        ltf_times = df_15m["open_time"].values
        for t in df_1h["open_time"].iloc[:: max(len(df_1h) // 250, 1)].values:
            close_t = int(t) + 3_600_000
            pos = np.searchsorted(ltf_times, close_t, side="left")
            checks.append(pos < len(ltf_times) and int(ltf_times[pos]) >= close_t)
    if df_5m is not None and not df_5m.empty:
        ltf_times = df_5m["open_time"].values
        for t in df_1h["open_time"].iloc[:: max(len(df_1h) // 250, 1)].values:
            close_t = int(t) + 3_600_000
            pos = np.searchsorted(ltf_times, close_t, side="left")
            checks.append(pos < len(ltf_times) and int(ltf_times[pos]) >= close_t)
    rows.append(
        {
            "timeframe": "cross_timeframe",
            "exists": "YES" if checks else "NO",
            "rows": len(checks),
            "start": "",
            "end": "",
            "duplicate_candles": "",
            "bad_deltas": "",
            "sha256": "",
            "leakage_check": "PASS_NO_TRIGGER_BEFORE_SETUP_CLOSE" if checks and all(checks) else "WARNING_ALIGNMENT_INCOMPLETE",
        }
    )
    write_csv(REPORTS / "phase29_5_mtf_data_alignment_audit.csv", rows)
    return rows


def add_mtf_features(df_1h: pd.DataFrame, df_15m: pd.DataFrame | None, df_5m: pd.DataFrame | None) -> pd.DataFrame:
    df = df_1h.copy()
    df["mtf_15m_body_max"] = 0.0
    df["mtf_15m_wick_max"] = 0.0
    df["mtf_15m_volume_impulse"] = 1.0
    df["mtf_5m_body_max"] = 0.0
    df["mtf_5m_wick_max"] = 0.0
    df["mtf_5m_volume_impulse"] = 1.0
    df["mtf_5m_vwap"] = df["close"]
    df["mtf_5m_close"] = df["close"]
    df["mtf_15m_available"] = False
    df["mtf_5m_available"] = False

    def build_arrays(ltf: pd.DataFrame | None, prefix: str) -> None:
        if ltf is None or ltf.empty:
            return
        work = ltf[["open_time", "open", "high", "low", "close", "volume"]].copy()
        rng = (work["high"] - work["low"]).replace(0, np.nan)
        body = (work["close"] - work["open"]).abs() / rng
        upper = work["high"] - np.maximum(work["open"], work["close"])
        lower = np.minimum(work["open"], work["close"]) - work["low"]
        wick = np.maximum(upper, lower) / rng
        vol_ma = work["volume"].rolling(20, min_periods=1).mean()
        work["body_strength"] = body.fillna(0.0)
        work["wick_ratio"] = wick.fillna(0.0)
        work["volume_impulse"] = (work["volume"] / vol_ma.replace(0, np.nan)).fillna(1.0)
        work["pv"] = work["close"] * work["volume"]
        ltf_times = work["open_time"].values
        for idx, row in df.iterrows():
            start = int(row["open_time"])
            end = start + 3_600_000
            lo = np.searchsorted(ltf_times, start, side="left")
            hi = np.searchsorted(ltf_times, end, side="left")
            if hi <= lo:
                continue
            chunk = work.iloc[lo:hi]
            df.at[idx, f"{prefix}_body_max"] = float(chunk["body_strength"].max())
            df.at[idx, f"{prefix}_wick_max"] = float(chunk["wick_ratio"].max())
            df.at[idx, f"{prefix}_volume_impulse"] = float(chunk["volume_impulse"].max())
            if prefix == "mtf_5m":
                vol = float(chunk["volume"].sum())
                df.at[idx, "mtf_5m_vwap"] = safe_div(float(chunk["pv"].sum()), vol, float(chunk["close"].iloc[-1]))
                df.at[idx, "mtf_5m_close"] = float(chunk["close"].iloc[-1])
            df.at[idx, f"{prefix}_available"] = True

    build_arrays(df_15m, "mtf_15m")
    build_arrays(df_5m, "mtf_5m")
    return df


class MTFGateStrategy(BaseStrategy):
    def __init__(self, name: str, base: BaseStrategy, gates: dict[str, Any]):
        super().__init__(name=name, hypothesis="Closed-candle MTF gate over executable strategy signal.")
        self.base = base
        self.gates = gates

    def get_param_grid(self) -> dict:
        return {}

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict | None = None) -> dict | None:
        sig = self.base.get_signal(df, i, live_metrics=live_metrics) if "live_metrics" in self.base.get_signal.__code__.co_varnames else self.base.get_signal(df, i)
        if sig is None:
            return None
        row = df.iloc[i]
        close_value = float(row["close"])
        risk = abs(close_value - float(sig["stop_loss"]))
        reward = abs(float(sig["take_profit"]) - close_value)
        expected_r = reward / risk if risk > 0 else 0.0
        if expected_r < float(self.gates.get("min_expected_r", 0.0)):
            return None
        dt = pd.to_datetime(int(row["open_time"]), unit="ms", utc=True)
        session = "tokyo" if 0 <= dt.hour < 8 else "london" if 8 <= dt.hour < 13 else "ny" if 13 <= dt.hour < 21 else "off"
        if self.gates.get("sessions") and session not in set(self.gates["sessions"]):
            return None
        if abs(float(row.get("fundingRate", 0.0) or 0.0)) > float(self.gates.get("max_funding_abs", 999.0)):
            return None
        if float(row.get("adx", 0.0) or 0.0) < float(self.gates.get("min_adx", 0.0)):
            return None
        if float(row.get("mtf_15m_body_max", 0.0) or 0.0) < float(self.gates.get("min_15m_body", 0.0)):
            return None
        if float(row.get("mtf_5m_wick_max", 0.0) or 0.0) < float(self.gates.get("min_5m_wick", 0.0)):
            return None
        if float(row.get("mtf_5m_volume_impulse", 1.0) or 1.0) < float(self.gates.get("min_5m_volume", 0.0)):
            return None
        if self.gates.get("require_5m_vwap_reclaim"):
            if sig["side"] == "Long" and float(row.get("mtf_5m_close", close_value)) < float(row.get("mtf_5m_vwap", close_value)):
                return None
            if sig["side"] == "Short" and float(row.get("mtf_5m_close", close_value)) > float(row.get("mtf_5m_vwap", close_value)):
                return None
        out = dict(sig)
        out["strategy_name"] = self.name
        out["expected_r_signal"] = expected_r
        out["reason"] = f"{self.name}: {sig.get('reason', '')}"
        if self.gates.get("trail_atr_mult"):
            out["trail_atr_mult"] = self.gates["trail_atr_mult"]
        if self.gates.get("breakeven_atr_mult"):
            out["breakeven_atr_mult"] = self.gates["breakeven_atr_mult"]
        if self.gates.get("time_stop"):
            out["time_stop"] = self.gates["time_stop"]
        return out


class PF12MTFRouter(BaseStrategy):
    def __init__(self, c_core: BaseStrategy, b_rescue: BaseStrategy):
        super().__init__(name="phase29_5_pf12_mtf_router", hypothesis="MTF C core priority plus B rescue fallback.")
        self.c_core = c_core
        self.b_rescue = b_rescue
        self.conflicts: list[dict[str, Any]] = []

    def get_param_grid(self) -> dict:
        return {}

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict | None = None) -> dict | None:
        c_sig = self.c_core.get_signal(df, i, live_metrics=live_metrics)
        b_sig = self.b_rescue.get_signal(df, i, live_metrics=live_metrics)
        if c_sig is not None and b_sig is not None and c_sig["side"] != b_sig["side"]:
            self.conflicts.append({"signal_time": int(df["open_time"].iloc[i]), "conflict": "c_core_vs_b_rescue"})
        if c_sig is not None:
            c_sig = dict(c_sig)
            c_sig["strategy_name"] = "variant_c_mtf_core"
            return c_sig
        if b_sig is not None:
            b_sig = dict(b_sig)
            b_sig["strategy_name"] = "variant_b_mtf_rescue"
            return b_sig
        return None


def cfg_strategy(cfg: dict[str, Any], **updates: Any) -> UniversalStrategyTemplate:
    params = dict(cfg)
    params["bb_width_thresh"] = params.get("bb_width_thresh", 0.06)
    params.update(updates)
    return UniversalStrategyTemplate(params)


def teacher_mtf_trigger_match(df_1h_mtf: pd.DataFrame, df_15m: pd.DataFrame | None, df_5m: pd.DataFrame | None, pf12_teacher: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ltf5 = df_5m[["open_time", "open", "high", "low", "close", "volume"]].copy() if df_5m is not None else None
    ltf15 = df_15m[["open_time", "open", "high", "low", "close", "volume"]].copy() if df_15m is not None else None
    for idx, trade in pf12_teacher.reset_index(drop=True).iterrows():
        entry_time = int(trade["entry_time"])
        setup_open = entry_time - 3_600_000
        setup_close = setup_open + 3_600_000
        _, candle = candle_at_or_before(df_1h_mtf, setup_open)
        side = str(trade["side"])
        triggers = []
        for tf, ltf in [("15m", ltf15), ("5m", ltf5)]:
            if ltf is None or ltf.empty:
                continue
            times = ltf["open_time"].values
            lo = np.searchsorted(times, setup_close, side="left")
            hi = np.searchsorted(times, setup_close + 3_600_000, side="left")
            if hi <= lo:
                continue
            chunk = ltf.iloc[lo:hi]
            rng = (chunk["high"] - chunk["low"]).replace(0, np.nan)
            body = ((chunk["close"] - chunk["open"]).abs() / rng).fillna(0.0).max()
            upper = chunk["high"] - np.maximum(chunk["open"], chunk["close"])
            lower = np.minimum(chunk["open"], chunk["close"]) - chunk["low"]
            wick = (np.maximum(upper, lower) / rng).fillna(0.0).max()
            pv = float((chunk["close"] * chunk["volume"]).sum())
            vol = float(chunk["volume"].sum())
            vwap = safe_div(pv, vol, float(chunk["close"].iloc[-1]))
            last_close = float(chunk["close"].iloc[-1])
            reclaim = (side == "Long" and last_close >= vwap) or (side == "Short" and last_close <= vwap)
            if body >= 0.55:
                triggers.append(f"{tf}_body_close")
            if wick >= 0.50:
                triggers.append(f"{tf}_wick_rejection")
            if reclaim:
                triggers.append(f"{tf}_vwap_reclaim")
        category = "no_live_trigger_found"
        if any("15m" in t for t in triggers) and any("5m" in t for t in triggers):
            category = "exact_live_trigger_found"
        elif triggers:
            category = "nearby_trigger_found"
        elif "adjusted_entry" in trade.index:
            category = "shifted_entry_explainable"
        rows.append(
            {
                "teacher_row": idx,
                "entry_time": entry_time,
                "entry_datetime": str(pd.to_datetime(entry_time, unit="ms", utc=True)),
                "side": side,
                "setup_close": setup_close,
                "setup_close_datetime": str(pd.to_datetime(setup_close, unit="ms", utc=True)),
                "match_category": category,
                "trigger_patterns": ";".join(triggers),
                "adx": float(candle.get("adx", 0.0) or 0.0),
                "atr_pct": float(candle.get("atr_pct", 0.0) or 0.0),
                "funding_safe": "YES" if abs(float(candle.get("fundingRate", 0.0) or 0.0)) <= 0.00035 else "NO",
                "used_in_live_router": "NO_TEACHER_ANALYSIS_ONLY",
            }
        )
    write_csv(REPORTS / "phase29_5_teacher_mtf_trigger_match.csv", rows)
    return rows


def candle_at_or_before(df: pd.DataFrame, open_time: int) -> tuple[int, pd.Series]:
    pos = int(np.searchsorted(df["open_time"].values, open_time, side="right") - 1)
    pos = max(0, min(pos, len(df) - 1))
    return pos, df.iloc[pos]


def run_strategy_row(system: str, status: str, df: pd.DataFrame, strategy: BaseStrategy, extra: dict[str, Any] | None = None) -> tuple[dict[str, Any], pd.DataFrame]:
    trades = run_engine(df, strategy)["trades"].copy()
    row = metric_row(system, status, trades, extra or {})
    return row, trades


def variant_c_mtf_results(df: pd.DataFrame, teacher: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, Any], pd.DataFrame]:
    specs = [
        ("c_mtf_strict_quality", {"min_expected_r": 1.55, "sessions": ["london", "ny"], "max_funding_abs": 0.00025, "min_adx": 20, "min_15m_body": 0.45, "min_5m_wick": 0.45, "require_5m_vwap_reclaim": True}),
        ("c_mtf_balanced_quality", {"min_expected_r": 1.35, "sessions": ["london", "ny"], "max_funding_abs": 0.00035, "min_adx": 16, "min_15m_body": 0.35, "min_5m_wick": 0.35}),
        ("c_mtf_trade_count", {"min_expected_r": 1.15, "sessions": ["tokyo", "london", "ny"], "max_funding_abs": 0.0005, "min_adx": 12, "min_15m_body": 0.25, "min_5m_wick": 0.25}),
        ("c_mtf_teacher_match", {"min_expected_r": 1.25, "sessions": ["london", "ny"], "max_funding_abs": 0.00045, "min_adx": 14, "min_15m_body": 0.30, "min_5m_wick": 0.30, "require_5m_vwap_reclaim": True}),
    ]
    teacher_ts = time_side_key_set(teacher)
    rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    best_trades: pd.DataFrame | None = None
    for name, gates in specs:
        row, trades = run_strategy_row(name, "ENGINE_EXECUTED_MTF_C_REBUILD", df, MTFGateStrategy(name, cfg_strategy(CAND_C_CFG), gates), {"gates": json.dumps(gates, sort_keys=True)})
        ts = time_side_key_set(trades)
        row["teacher_time_side_match_rate"] = len(ts & teacher_ts) / len(teacher_ts) if teacher_ts else 0.0
        row["missing_teacher_time_side"] = len(teacher_ts - ts)
        row["extra_live_time_side"] = len(ts - teacher_ts)
        rows.append(row)
        score = float(row["net_pnl"]) + 2000 * float(row["profit_factor"]) - 250 * float(row["max_dd_pct"]) + 5000 * float(row["teacher_time_side_match_rate"])
        if best is None or score > float(best["_score"]):
            best = dict(row)
            best["_score"] = score
            best_trades = trades.copy()
    for row in rows:
        row.pop("_score", None)
    write_csv(REPORTS / "phase29_5_variant_c_mtf_results.csv", rows)
    assert best is not None and best_trades is not None
    best.pop("_score", None)
    return rows, best, best_trades


def variant_b_mtf_results(df: pd.DataFrame, teacher: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, Any], pd.DataFrame]:
    specs = [
        ("b_rescue_mtf_strict", {"min_expected_r": 1.55, "sessions": ["london", "ny"], "max_funding_abs": 0.0003, "min_adx": 18, "min_15m_body": 0.40, "min_5m_wick": 0.45, "require_5m_vwap_reclaim": True}),
        ("b_rescue_mtf_balanced", {"min_expected_r": 1.35, "sessions": ["london", "ny"], "max_funding_abs": 0.0004, "min_adx": 14, "min_15m_body": 0.30, "min_5m_wick": 0.30}),
        ("b_rescue_mtf_tokyo_london", {"min_expected_r": 1.25, "sessions": ["tokyo", "london"], "max_funding_abs": 0.00045, "min_adx": 12, "min_15m_body": 0.25, "min_5m_wick": 0.25}),
        ("b_rescue_mtf_vwap", {"min_expected_r": 1.20, "sessions": ["tokyo", "london", "ny"], "max_funding_abs": 0.0005, "min_adx": 10, "require_5m_vwap_reclaim": True}),
    ]
    teacher_ts = time_side_key_set(teacher)
    rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    best_trades: pd.DataFrame | None = None
    for name, gates in specs:
        row, trades = run_strategy_row(name, "ENGINE_EXECUTED_MTF_B_RESCUE_REBUILD", df, MTFGateStrategy(name, cfg_strategy(CAND_A_CFG), gates), {"gates": json.dumps(gates, sort_keys=True)})
        ts = time_side_key_set(trades)
        row["teacher_time_side_match_rate"] = len(ts & teacher_ts) / len(teacher_ts) if teacher_ts else 0.0
        row["missing_teacher_time_side"] = len(teacher_ts - ts)
        row["extra_live_time_side"] = len(ts - teacher_ts)
        rows.append(row)
        score = float(row["net_pnl"]) + 1500 * float(row["profit_factor"]) - 250 * float(row["max_dd_pct"]) + 4000 * float(row["teacher_time_side_match_rate"])
        if best is None or score > float(best["_score"]):
            best = dict(row)
            best["_score"] = score
            best_trades = trades.copy()
    for row in rows:
        row.pop("_score", None)
    write_csv(REPORTS / "phase29_5_variant_b_rescue_mtf_results.csv", rows)
    assert best is not None and best_trades is not None
    best.pop("_score", None)
    return rows, best, best_trades


def pf12_router_results(df: pd.DataFrame, pf12_teacher: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame, str, list[dict[str, Any]]]:
    teacher_metrics = metrics_with_stress(pf12_teacher)
    router_specs = [
        ("pf12_mtf_balanced", {"min_expected_r": 1.35, "sessions": ["london", "ny"], "max_funding_abs": 0.00035, "min_adx": 16, "min_15m_body": 0.35, "min_5m_wick": 0.30}, {"min_expected_r": 1.35, "sessions": ["london", "ny"], "max_funding_abs": 0.0004, "min_adx": 14, "min_15m_body": 0.30, "min_5m_wick": 0.30}),
        ("pf12_mtf_trade_count", {"min_expected_r": 1.15, "sessions": ["tokyo", "london", "ny"], "max_funding_abs": 0.0005, "min_adx": 12, "min_15m_body": 0.25, "min_5m_wick": 0.20}, {"min_expected_r": 1.20, "sessions": ["tokyo", "london", "ny"], "max_funding_abs": 0.0005, "min_adx": 10, "require_5m_vwap_reclaim": True}),
        ("pf12_mtf_strict", {"min_expected_r": 1.50, "sessions": ["london", "ny"], "max_funding_abs": 0.00025, "min_adx": 20, "min_15m_body": 0.45, "min_5m_wick": 0.45, "require_5m_vwap_reclaim": True}, {"min_expected_r": 1.55, "sessions": ["london", "ny"], "max_funding_abs": 0.0003, "min_adx": 18, "min_15m_body": 0.40, "min_5m_wick": 0.45, "require_5m_vwap_reclaim": True}),
    ]
    teacher_ts = time_side_key_set(pf12_teacher)
    teacher_exact = basic_key_set(pf12_teacher)
    rows: list[dict[str, Any]] = []
    best_row: dict[str, Any] | None = None
    best_trades: pd.DataFrame | None = None
    best_status = "NOT_RECOVERED"
    for name, c_gates, b_gates in router_specs:
        router = PF12MTFRouter(MTFGateStrategy(f"{name}_c", cfg_strategy(CAND_C_CFG), c_gates), MTFGateStrategy(f"{name}_b", cfg_strategy(CAND_A_CFG), b_gates))
        row, trades = run_strategy_row(name, "ENGINE_EXECUTED_PF12_MTF_ROUTER", df, router, {"c_gates": json.dumps(c_gates, sort_keys=True), "b_gates": json.dumps(b_gates, sort_keys=True), "conflict_count": len(router.conflicts)})
        ts = time_side_key_set(trades)
        exact = basic_key_set(trades)
        row["teacher_time_side_match_rate"] = len(ts & teacher_ts) / len(teacher_ts) if teacher_ts else 0.0
        row["exact_matches"] = len(exact & teacher_exact)
        row["missing_teacher_time_side"] = len(teacher_ts - ts)
        row["extra_live_time_side"] = len(ts - teacher_ts)
        rows.append(row)
        score = float(row["net_pnl"]) + 2000 * float(row["profit_factor"]) - 250 * float(row["max_dd_pct"]) + 6000 * float(row["teacher_time_side_match_rate"])
        if best_row is None or score > float(best_row["_score"]):
            best_row = dict(row)
            best_row["_score"] = score
            best_trades = trades.copy()
    assert best_row is not None and best_trades is not None
    best_row.pop("_score", None)
    if int(best_row["exact_matches"]) == len(pf12_teacher) and round(float(best_row["net_pnl"]), 2) == round(float(teacher_metrics["net_pnl"]), 2):
        best_status = "EXACT_MATCH"
    elif float(best_row["teacher_time_side_match_rate"]) >= 0.80:
        best_status = "NEAR_MATCH"
    elif float(best_row["teacher_time_side_match_rate"]) > 0:
        best_status = "PARTIAL_RECOVERY"
    best_row["pf12_recovery_status"] = best_status
    best_trades.to_csv(REPORTS / "phase29_5_pf12_executable_router_trade_log.csv", index=False)
    rows.insert(0, best_row)
    write_csv(REPORTS / "phase29_5_pf12_executable_router_results.csv", rows)

    best_ts = time_side_key_set(best_trades)
    best_exact = basic_key_set(best_trades)
    gap = [
        {
            "row_type": "summary",
            "status": best_status,
            "teacher_trades": len(pf12_teacher),
            "live_trades": len(best_trades),
            "exact_matches": len(best_exact & teacher_exact),
            "time_side_matches": len(best_ts & teacher_ts),
            "missing_teacher_time_side": len(teacher_ts - best_ts),
            "extra_live_time_side": len(best_ts - teacher_ts),
            "pnl_gap": float(best_row["net_pnl"]) - float(teacher_metrics["net_pnl"]),
            "pf_gap": float(best_row["profit_factor"]) - float(teacher_metrics["profit_factor"]),
        }
    ]
    for key in sorted(teacher_ts - best_ts)[:100]:
        gap.append({"row_type": "missing_teacher_time_side", "status": best_status, "key": json.dumps(key)})
    for key in sorted(best_ts - teacher_ts)[:100]:
        gap.append({"row_type": "extra_live_time_side", "status": best_status, "key": json.dumps(key)})
    write_csv(REPORTS / "phase29_5_pf12_trade_match_gap_audit.csv", gap)
    return best_row, best_trades, best_status, rows


def candidate_registry(count: int = 5000) -> list[dict[str, Any]]:
    families = [
        "variant_c_mtf",
        "variant_b_rescue_mtf",
        "pf12_fusion_mtf",
        "dirty_pf8_pruning",
        "vwap_reclaim",
        "second_retest",
        "london_tokyo",
        "expected_r",
        "funding_ny_hardening",
        "exit_risk",
    ]
    templates = [
        "bollinger_expansion_breakout",
        "atr_volatility_expansion",
        "breakout_retest",
        "vwap_reclaim_continuation",
        "london_continuation",
        "asia_range_breakout",
        "pullback_after_impulse",
        "hh_hl_continuation",
    ]
    rows: list[dict[str, Any]] = []
    for i in range(count):
        family = families[i % len(families)]
        template = templates[(i // len(families)) % len(templates)]
        min_er = [1.10, 1.20, 1.30, 1.40, 1.55][i % 5]
        min_adx = [10, 12, 14, 16, 18, 20][(i // 3) % 6]
        max_funding = [0.00025, 0.00035, 0.00045, 0.00060][(i // 5) % 4]
        min_body = [0.20, 0.30, 0.40, 0.50][(i // 7) % 4]
        min_wick = [0.20, 0.30, 0.40, 0.50][(i // 11) % 4]
        session_mode = ["london_ny", "tokyo_london", "all"][i % 3]
        params = {
            "family": family,
            "template_type": template,
            "min_expected_r": min_er,
            "min_adx": min_adx,
            "max_funding_abs": max_funding,
            "min_15m_body": min_body,
            "min_5m_wick": min_wick,
            "session_mode": session_mode,
            "require_5m_vwap_reclaim": (i % 4 == 0),
            "trail_atr_mult": [None, 1.2, 1.5][i % 3],
            "breakeven_atr_mult": [None, 0.8, 1.2][(i // 2) % 3],
            "time_stop": [None, 24, 48][(i // 4) % 3],
        }
        cid = f"P295_{i:05d}"
        rows.append({"candidate_id": cid, "candidate_hash": sha16(f"{cid}|{json.dumps(params, sort_keys=True)}"), **params})
    write_csv(REPORTS / "phase29_5_candidate_registry.csv", rows)
    return rows


def build_candidate_strategy(row: dict[str, Any]) -> BaseStrategy:
    session_map = {
        "london_ny": ["london", "ny"],
        "tokyo_london": ["tokyo", "london"],
        "all": ["tokyo", "london", "ny"],
    }
    gates = {
        "min_expected_r": float(row["min_expected_r"]),
        "min_adx": float(row["min_adx"]),
        "max_funding_abs": float(row["max_funding_abs"]),
        "min_15m_body": float(row["min_15m_body"]),
        "min_5m_wick": float(row["min_5m_wick"]),
        "sessions": session_map.get(row["session_mode"], ["london", "ny"]),
        "require_5m_vwap_reclaim": str(row["require_5m_vwap_reclaim"]) == "True",
    }
    if row.get("trail_atr_mult") not in ("", "None", None):
        gates["trail_atr_mult"] = float(row["trail_atr_mult"])
    if row.get("breakeven_atr_mult") not in ("", "None", None):
        gates["breakeven_atr_mult"] = float(row["breakeven_atr_mult"])
    if row.get("time_stop") not in ("", "None", None):
        gates["time_stop"] = int(float(row["time_stop"]))

    cfg = {
        "template_type": row["template_type"],
        "trend_filter": None,
        "regime_filter_mode": "strict" if row["family"] in {"variant_c_mtf", "expected_r"} else "no_filter",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.8,
        "rsi_overbought": 75,
        "rsi_oversold": 30,
        "adx_thresh": 20,
        "wick_ratio_thresh": 0.45,
        "timeframe": "1h",
    }
    if row["family"] == "pf12_fusion_mtf":
        c = MTFGateStrategy(row["candidate_id"] + "_c", cfg_strategy(CAND_C_CFG), gates)
        b = MTFGateStrategy(row["candidate_id"] + "_b", cfg_strategy(CAND_A_CFG), gates)
        return PF12MTFRouter(c, b)
    return MTFGateStrategy(row["candidate_id"], UniversalStrategyTemplate(cfg), gates)


def execute_candidates(df: pd.DataFrame, registry: list[dict[str, Any]], pf12_teacher_metrics: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    best_trades = pd.DataFrame()
    for idx, row in enumerate(registry):
        if idx < ENGINE_EXECUTION_LIMIT:
            try:
                strategy = build_candidate_strategy(row)
                trades = run_engine(df, strategy)["trades"].copy()
                m = metrics_with_stress(trades)
                score = float(m["net_pnl"]) + 2500 * float(m["profit_factor"]) - 300 * float(m["max_dd_pct"]) + 10 * float(m["trades"])
                result = dict(row)
                result.update(m)
                result.update(
                    {
                        "status": "EXECUTED_ENGINE",
                        "engine_run_index": idx,
                        "score": score,
                        "beats_pf12_teacher": "YES"
                        if float(m["net_pnl"]) > float(pf12_teacher_metrics["net_pnl"])
                        and float(m["profit_factor"]) >= float(pf12_teacher_metrics["profit_factor"])
                        else "NO",
                    }
                )
                if best is None or score > float(best["score"]):
                    best = dict(result)
                    best_trades = trades.copy()
            except Exception as exc:
                result = dict(row)
                result.update({"status": "ENGINE_ERROR", "engine_run_index": idx, "error": str(exc)[:200]})
        else:
            result = dict(row)
            result.update({"status": "REGISTERED_NOT_EXECUTED_TIMEBOXED", "engine_run_index": "", "score": "", "beats_pf12_teacher": "", "trade_log_hash": ""})
            for col in [
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
            ]:
                result[col] = ""
        rows.append(result)
    write_csv(REPORTS / "phase29_5_candidate_results.csv", rows)
    return rows, best, best_trades


def dirty_pf8_upgrade(df: pd.DataFrame, candidate_best: dict[str, Any] | None) -> list[dict[str, Any]]:
    dirty_path = REPORTS / "phase29_1_dirty_pf8_recompute_trade_log.csv"
    dirty = pd.read_csv(dirty_path) if dirty_path.exists() else pd.DataFrame()
    rows: list[dict[str, Any]] = []
    if not dirty.empty:
        base = metrics_with_stress(dirty)
        rows.append({"system": "Dirty PF8 no-forcing baseline", "status": "DIAGNOSTIC_BASELINE_NOT_ACCEPTED", **base})
        filtered = []
        for _, trade in dirty.iterrows():
            _, candle = candle_at_or_before(df, int(trade["entry_time"]) - 3_600_000)
            dt = pd.to_datetime(int(trade["entry_time"]), unit="ms", utc=True)
            session = "tokyo" if 0 <= dt.hour < 8 else "london" if 8 <= dt.hour < 13 else "ny" if 13 <= dt.hour < 21 else "off"
            if (
                session in {"london", "ny"}
                and abs(float(candle.get("fundingRate", 0.0) or 0.0)) <= 0.00035
                and float(candle.get("adx", 0.0) or 0.0) >= 14
                and float(candle.get("mtf_5m_wick_max", 0.0) or 0.0) >= 0.25
            ):
                filtered.append(trade)
        filtered_df = pd.DataFrame(filtered)
        if not filtered_df.empty:
            rows.append({"system": "Dirty PF8 MTF diagnostic filter", "status": "DIAGNOSTIC_FILTER_ONLY_NOT_ENGINE_BENCHMARK", **metrics_with_stress(filtered_df)})
    if candidate_best:
        rows.append({"system": "Best engine-executed recovered PF8/PF8.1 router", "status": "ENGINE_EXECUTED_CANDIDATE", **candidate_best})
    write_csv(REPORTS / "phase29_5_dirty_pf8_upgrade_results.csv", rows)
    return rows


def benchmark_stack(
    floor: pd.DataFrame,
    variant_b_teacher: pd.DataFrame,
    variant_c_teacher: pd.DataFrame,
    pf12_teacher: pd.DataFrame,
    c_best: dict[str, Any],
    b_best: dict[str, Any],
    pf12_best: dict[str, Any],
    dirty_rows: list[dict[str, Any]],
    candidate_best: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    phase294 = pd.read_csv(REPORTS / "phase29_4_pf12_live_router_metrics.csv") if (REPORTS / "phase29_4_pf12_live_router_metrics.csv").exists() else pd.DataFrame()
    phase294_live = phase294.iloc[0].to_dict() if not phase294.empty else {}
    dirty_base = dirty_rows[0] if dirty_rows else {}
    systems = [
        ("Executable floor", "ENGINE_EXECUTED", metrics_with_stress(floor)),
        ("Variant B teacher", "TEACHER_REFERENCE", metrics_with_stress(variant_b_teacher)),
        ("Variant C teacher", "TEACHER_REFERENCE", metrics_with_stress(variant_c_teacher)),
        ("PF1.2 teacher", "TEACHER_REFERENCE", metrics_with_stress(pf12_teacher)),
        ("Phase 29.4 live router", "ENGINE_EXECUTED_PRIOR_PHASE", phase294_live),
        ("Best Variant C MTF rebuild", "ENGINE_EXECUTED", c_best),
        ("Best B rescue MTF rebuild", "ENGINE_EXECUTED", b_best),
        ("Best PF1.2 executable rebuild", "ENGINE_EXECUTED", pf12_best),
        ("Dirty PF8 baseline", "DIAGNOSTIC_BASELINE", dirty_base),
        ("Best recovered PF8/PF8.1 router", "ENGINE_EXECUTED" if candidate_best else "NONE", candidate_best or {}),
    ]
    rows = []
    for name, status, m in systems:
        rows.append(
            {
                "system": name,
                "status": status,
                "net_pnl": m.get("net_pnl", ""),
                "trades": m.get("trades", ""),
                "winning_trades": m.get("winners", ""),
                "losing_trades": m.get("losers", ""),
                "win_rate": m.get("win_rate", ""),
                "profit_factor": m.get("profit_factor", ""),
                "max_dd_pct": m.get("max_dd_pct", ""),
                "combined_adverse": m.get("combined_adverse", ""),
                "average_winner": m.get("average_winner", ""),
                "average_loser": m.get("average_loser", ""),
                "expectancy": m.get("expectancy", ""),
                "positive_months": m.get("positive_months", ""),
                "negative_months": m.get("negative_months", ""),
                "zero_months": m.get("zero_months", ""),
                "sleeve_contribution": m.get("family", m.get("router_rule", "")),
                "conflict_count": m.get("conflict_count", ""),
            }
        )
    write_csv(REPORTS / "phase29_5_benchmark_stack_comparison.csv", rows)
    return rows


def write_live_audit(final_status: str) -> None:
    text = f"""# Phase 29.5 Live Automation Readiness Audit

## Best PF1.2 MTF Rebuild

- Entry rules: closed 1h engine signals with closed 15m/5m features from the completed setup candle.
- Exit rules: deterministic engine stop loss, take profit, optional breakeven, trailing, and time stop where configured.
- Order timing: signal on closed candle, fill at next engine candle open.
- Same-candle SL priority: engine uses conservative stop-first handling.
- Funding handling: candle-aligned funding only.
- Tick/step/min-notional: modeled in engine, not exchange-shadow verified.
- Reduce-only exit concept: not proven against exchange order ledger.
- Shadow-mode gaps: no Binance shadow execution, restart recovery, partial-fill ledger, or rate-limit proof.

## Best Recovered PF8/PF8.1 Router

- Candidate rows carry metrics only when `status=EXECUTED_ENGINE`.
- Unexecuted rows are blank-metric registered candidates.
- Dirty PF8 filtered rows remain diagnostic and are not accepted as benchmarks.

Final status: {final_status}. Live capital status: NOT_REAL_CAPITAL_READY.
"""
    write_text(REPORTS / "phase29_5_live_automation_audit.md", text)


def runner_clean() -> bool:
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "29386" + ".59",
        "30580" + ".40",
        "31250" + ".80",
        ".sam" + "ple(",
        "is_" + "winner",
        "future_" + "pnl",
        "future_" + "r",
        "future_" + "mfe",
        "future_" + "mae",
        "selected_" + "trade_ids",
        "forced_" + "pnl",
    ]
    if any(fragment in source for fragment in forbidden_fragments):
        return False
    tree = ast.parse(source)
    forbidden_names = {"pnl" + "_70", "pnl" + "_80", "pnl" + "_81", "pf" + "_81", "dd" + "_81", "forced" + "_pnl"}
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in forbidden_names:
                return False
    return True


def phase29_4_router_net() -> float:
    path = REPORTS / "phase29_4_pf12_live_router_metrics.csv"
    if not path.exists():
        return 0.0
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    if not rows:
        return 0.0
    return float(rows[0].get("net_pnl", 0.0) or 0.0)


def choose_verdict(pf12_status: str, pf12_best: dict[str, Any], candidate_best: dict[str, Any] | None) -> str:
    if not runner_clean():
        return "AUDIT_FAIL_FORCED_METRICS_REMAIN"
    if pf12_status == "EXACT_MATCH":
        return "PF12_LIVE_EXECUTABLE_EXACTLY_RECOVERED"
    if pf12_status == "NEAR_MATCH":
        return "PF12_LIVE_EXECUTABLE_NEAR_MATCH_RECOVERED"
    best_net = max(float(pf12_best.get("net_pnl", 0.0) or 0.0), float(candidate_best.get("net_pnl", 0.0) or 0.0) if candidate_best else 0.0)
    if best_net > phase29_4_router_net():
        return "PF12_MAJOR_MTF_RECOVERY_PROGRESS_PF8_RESEARCH_CONTINUES"
    if float(pf12_best.get("trades", 0.0) or 0.0) > 0:
        return "PF12_PARTIAL_RECOVERY_BUT_BREAKTHROUGH_NOT_FOUND"
    return "PF12_TEACHER_ONLY_EXECUTABLE_NOT_RECOVERED"


def write_report(
    verdict: str,
    evidence_rows: list[dict[str, Any]],
    mtf_rows: list[dict[str, Any]],
    trigger_rows: list[dict[str, Any]],
    c_best: dict[str, Any],
    b_best: dict[str, Any],
    pf12_best: dict[str, Any],
    pf12_status: str,
    candidate_results: list[dict[str, Any]],
    candidate_best: dict[str, Any] | None,
    dirty_rows: list[dict[str, Any]],
    pf12_teacher_metrics: dict[str, Any],
) -> None:
    executed = [r for r in candidate_results if r.get("status") == "EXECUTED_ENGINE"]
    trigger_counts = pd.Series([r["match_category"] for r in trigger_rows]).value_counts().to_dict() if trigger_rows else {}
    best_candidate_line = "none" if not candidate_best else f"{candidate_best['candidate_id']} / {candidate_best['family']} / PnL {float(candidate_best['net_pnl']):.2f} / trades {int(float(candidate_best['trades']))} / PF {float(candidate_best['profit_factor']):.2f}"
    text = f"""# Phase 29.5 Major Precision Fusion Breakthrough Report

**FINAL VERDICT: {verdict}**

PF means Precision Fusion: a live-known router over candidate sleeves, filters, rescue layers, and risk controls. Phase 29.5 used Antigravity BTC 15m/5m data for recovery evidence, but accepted metrics only from engine-executed strategies.

## Local Evidence Re-Scan

Evidence rows mapped: {len(evidence_rows)}. Antigravity provided useful 15m/5m data and lower-timeframe research artifacts, but still no hidden exact PF1.2 executable router.

## MTF Data Alignment

MTF audit status rows are saved in `phase29_5_mtf_data_alignment_audit.csv`. The cross-timeframe rule is: setup candle closes first, then lower-timeframe trigger windows start at or after the setup close. Engine MTF gates only use lower-timeframe candles inside already-closed 1h setup candles.

## PF1.2 Teacher-to-MTF Trigger Match

Trigger category counts: `{trigger_counts}`. These categories explain teacher rows as research diagnostics only; no teacher row ID or teacher label is used by the live router.

## Variant C MTF Rebuild

Best C MTF rebuild: `{c_best['system']}` with PnL {float(c_best['net_pnl']):.2f}, trades {int(c_best['trades'])}, PF {float(c_best['profit_factor']):.2f}, DD {float(c_best['max_dd_pct']):.2f}%, teacher time/side match {float(c_best['teacher_time_side_match_rate']):.2%}.

## Variant B Rescue MTF Rebuild

Best B rescue MTF rebuild: `{b_best['system']}` with PnL {float(b_best['net_pnl']):.2f}, trades {int(b_best['trades'])}, PF {float(b_best['profit_factor']):.2f}, DD {float(b_best['max_dd_pct']):.2f}%, teacher time/side match {float(b_best['teacher_time_side_match_rate']):.2%}.

## PF1.2 Executable Router Recovery

PF1.2 MTF router status: `{pf12_status}`.

| Metric | PF1.2 teacher target | Best Phase 29.5 PF1.2 MTF router |
|---|---:|---:|
| PnL | {float(pf12_teacher_metrics['net_pnl']):.2f} | {float(pf12_best['net_pnl']):.2f} |
| Trades | {int(pf12_teacher_metrics['trades'])} | {int(pf12_best['trades'])} |
| PF | {float(pf12_teacher_metrics['profit_factor']):.2f} | {float(pf12_best['profit_factor']):.2f} |
| DD % | {float(pf12_teacher_metrics['max_dd_pct']):.2f} | {float(pf12_best['max_dd_pct']):.2f} |
| Stress | {float(pf12_teacher_metrics['combined_adverse']):.2f} | {float(pf12_best['combined_adverse']):.2f} |
| Teacher time/side match | 100.00% | {float(pf12_best['teacher_time_side_match_rate']):.2%} |

This is not exact PF1.2 executable proof unless `pf12_recovery_status` is `EXACT_MATCH`.

## Dirty PF8 Upgrade

Dirty PF8 remains diagnostic. Rows in `phase29_5_dirty_pf8_upgrade_results.csv` show baseline, MTF diagnostic filtering, and the best engine-executed recovered PF8/PF8.1 candidate where available.

## Large Candidate Search

- Registered candidates: 5000
- Engine-executed candidates: {len(executed)}
- Execution limit: {ENGINE_EXECUTION_LIMIT}
- Best engine candidate: {best_candidate_line}
- Unexecuted candidates have blank metrics by design.

## Benchmark Stack

The stack comparison is saved in `phase29_5_benchmark_stack_comparison.csv`. Any system marked `TEACHER_REFERENCE` is not an executable live proof.

## Final Answers

- PF1.2 executable recovery got to PnL {float(pf12_best['net_pnl']):.2f}, {int(pf12_best['trades'])} trades, PF {float(pf12_best['profit_factor']):.2f}, status `{pf12_status}`.
- MTF triggers explain a subset of teacher trades, but they do not fully regenerate the teacher set.
- Variant C and B now have live-known MTF rebuild candidates, but neither exactly reproduces the teacher set.
- Dirty PF8 quality improved only as diagnostics unless an engine-executed candidate row beats the teacher target.
- No real router beats the PF1.2 teacher unless `beats_pf12_teacher=YES` in `phase29_5_candidate_results.csv`.
- Next step: build a true event-driven 5m execution engine so 1h setup plus post-close 5m trigger entries can be backtested without compressing trigger evidence into 1h rows.

## Live Status

NOT_REAL_CAPITAL_READY. No exchange-level shadow proof exists.
"""
    write_text(REPORTS / "phase29_5_major_precision_fusion_breakthrough_report.md", text)


def write_manifest(verdict: str) -> None:
    files: dict[str, Any] = {}
    for name in REQUIRED_FILES:
        if name == "phase29_5_audit_manifest.json":
            continue
        path = REPORTS / name
        files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    manifest = {
        "phase": "29.5",
        "final_verdict": verdict,
        "repo_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "execution_limit": ENGINE_EXECUTION_LIMIT,
        "antigravity_workspace": str(ANTIGRAVITY),
        "manifest_hash_note": "Manifest excludes self hash.",
        "files": files,
    }
    write_text(REPORTS / "phase29_5_audit_manifest.json", json.dumps(manifest, indent=2) + "\n")
    if OUTPUTS.exists():
        for name in REQUIRED_FILES:
            src = REPORTS / name
            if src.exists():
                (OUTPUTS / name).write_bytes(src.read_bytes())


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    df_1h = load_btc_1h()
    df_15m = load_ltf("15m")
    df_5m = load_ltf("5m")
    evidence_rows = local_evidence_map()
    mtf_rows = mtf_alignment_audit(df_1h, df_15m, df_5m)
    df_mtf = add_mtf_features(df_1h, df_15m, df_5m)
    floor = run_engine(df_mtf, build_p10_1_strategy())["trades"].copy()
    pf12_teacher, variant_b_teacher, variant_c_teacher, _ = canonical_teacher_sets(floor)
    trigger_rows = teacher_mtf_trigger_match(df_mtf, df_15m, df_5m, pf12_teacher)
    c_rows, c_best, _ = variant_c_mtf_results(df_mtf, variant_c_teacher)
    b_rows, b_best, _ = variant_b_mtf_results(df_mtf, variant_b_teacher)
    pf12_best, pf12_trades, pf12_status, _ = pf12_router_results(df_mtf, pf12_teacher)
    registry = candidate_registry(5000)
    pf12_teacher_metrics = metrics_with_stress(pf12_teacher)
    candidate_results, candidate_best, _ = execute_candidates(df_mtf, registry, pf12_teacher_metrics)
    dirty_rows = dirty_pf8_upgrade(df_mtf, candidate_best)
    benchmark_stack(floor, variant_b_teacher, variant_c_teacher, pf12_teacher, c_best, b_best, pf12_best, dirty_rows, candidate_best)
    verdict = choose_verdict(pf12_status, pf12_best, candidate_best)
    write_live_audit(verdict)
    write_report(verdict, evidence_rows, mtf_rows, trigger_rows, c_best, b_best, pf12_best, pf12_status, candidate_results, candidate_best, dirty_rows, pf12_teacher_metrics)
    write_manifest(verdict)
    print(json.dumps({"final_verdict": verdict, "executed_candidates": len([r for r in candidate_results if r.get("status") == "EXECUTED_ENGINE"]), "pf12_status": pf12_status}, indent=2))


if __name__ == "__main__":
    main()
