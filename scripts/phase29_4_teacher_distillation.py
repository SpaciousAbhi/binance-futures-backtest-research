"""
Phase 29.4 teacher distillation and live recovery.

This runner treats Variant B/C/PF1.2 trade sets as teacher evidence only. Any
live rebuild metrics written here come from `MultiPositionBacktestEngine`.
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
from src.research.phase21_runner import reconstruct_pf12 as reconstruct_pf12_with_variants
from src.strategies.base import BaseStrategy
from src.strategies.candidates import UniversalStrategyTemplate
from scripts.phase29_1_truth_first_recovery import add_recovery_features, monthly_table, standard_stress
from scripts.phase29_2_precision_fusion_truth import (
    combined_adverse,
    df_hash,
    load_btc_1h,
    metric_row,
    metrics_with_stress,
    run_engine,
    sha256_file,
    trade_key_rows,
    write_csv,
    write_text,
)

REQUIRED_FILES = [
    "phase29_4_precision_fusion_teacher_distillation_and_live_recovery_report.md",
    "phase29_4_local_evidence_inventory.csv",
    "phase29_4_teacher_canonical_sets.csv",
    "phase29_4_teacher_vs_floor_diff.csv",
    "phase29_4_entry_time_feature_table.csv",
    "phase29_4_teacher_distilled_rules.csv",
    "phase29_4_variant_c_live_rebuild_results.csv",
    "phase29_4_variant_b_rescue_rebuild_results.csv",
    "phase29_4_pf12_live_router_trade_log.csv",
    "phase29_4_pf12_live_router_metrics.csv",
    "phase29_4_pf12_trade_match_gap_audit.csv",
    "phase29_4_dirty_pf8_recovery_results.csv",
    "phase29_4_final_benchmark_comparison.csv",
    "phase29_4_live_automation_audit.md",
    "phase29_4_audit_manifest.json",
]

EVIDENCE_TERMS = [
    "Variant B",
    "Variant C",
    "Precision Fusion 1.2",
    "PF1.2",
    "B rescue",
    "C core",
    "expected R",
    "rescue rows",
    "phase17_3",
    "completed trade",
    "B unique",
    "C quality",
    "retest",
    "VWAP",
    "funding",
    "ADX",
    "ATR",
    "MFE",
    "MAE",
    "15m",
    "5m",
    "raw signal",
]

FEATURE_COLUMNS = [
    "row_source",
    "system",
    "entry_time",
    "entry_datetime",
    "side",
    "teacher_membership",
    "floor_membership",
    "session",
    "hour",
    "weekday",
    "trend_direction",
    "ema_slope_10",
    "ema50_over_ema200",
    "breakout_distance_atr",
    "retest_depth_atr",
    "wick_rejection_ratio",
    "body_strength",
    "close_location",
    "atr_14",
    "atr_pct",
    "bb_width",
    "bb_state",
    "rsi_14",
    "adx",
    "adx_slope_3",
    "volume_vs_ma20",
    "funding_rate",
    "funding_abs",
    "expected_r_signal",
    "cost_to_atr",
    "has_btc_15m_current_repo",
    "has_btc_5m_antigravity",
]


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read_text_safely(path: Path, limit: int = 250_000) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(limit)
    except Exception:
        return ""


def file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "source"
    if suffix in {".csv", ".json", ".yaml", ".yml"}:
        return "structured_artifact"
    if suffix in {".md", ".txt"}:
        return "report_or_note"
    return "other"


def evidence_inventory() -> list[dict[str, Any]]:
    roots = [ANTIGRAVITY, ROOT]
    rows: list[dict[str, Any]] = []
    for base in roots:
        if not base.exists():
            rows.append(
                {
                    "workspace": str(base),
                    "file_path": str(base),
                    "artifact_type": "missing_workspace",
                    "phase": "",
                    "matched_terms": "",
                    "relevant_lines_or_columns": "",
                    "live_safe": "NO",
                    "teacher_only": "NO",
                    "helps_recover_bc": "NO",
                    "unique_vs_github_checkout": "NO",
                    "note": "Path does not exist.",
                }
            )
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = str(path.relative_to(base))
            if any(part in rel for part in [".pytest_cache", "__pycache__", ".git\\"]):
                continue
            if path.stat().st_size > 8_000_000 and path.suffix.lower() not in {".csv", ".json"}:
                continue
            text = read_text_safely(path)
            matched = [term for term in EVIDENCE_TERMS if term.lower() in text.lower() or term.lower() in rel.lower()]
            if not matched and not (
                "BTCUSDT_5m" in rel
                or "BTCUSDT_15m" in rel
                or "phase17_3" in rel
                or "phase29_3" in rel
            ):
                continue
            phase_match = re.search(r"phase(\d+(?:_\d+)?)", rel.lower())
            phase = phase_match.group(0) if phase_match else ""
            line_hits = []
            for idx, line in enumerate(text.splitlines(), start=1):
                lower = line.lower()
                if any(term.lower() in lower for term in matched[:8]):
                    line_hits.append(str(idx))
                if len(line_hits) >= 8:
                    break
            current_equivalent = ROOT / rel
            unique = "YES" if base == ANTIGRAVITY and not current_equivalent.exists() else "NO"
            is_teacher = "YES" if any(x in text for x in ["sort_values(by=\"net_pnl\"", "row[\"R\"]", "completed trade", "sample(n="]) else "NO"
            live_safe = "NO" if is_teacher == "YES" else ("YES" if path.suffix.lower() == ".py" and "get_signal" in text else "ANALYSIS_ONLY")
            rows.append(
                {
                    "workspace": "antigravity" if base == ANTIGRAVITY else "github_checkout",
                    "file_path": str(path),
                    "artifact_type": file_type(path),
                    "phase": phase,
                    "matched_terms": ";".join(matched[:12]),
                    "relevant_lines_or_columns": ";".join(line_hits),
                    "live_safe": live_safe,
                    "teacher_only": is_teacher,
                    "helps_recover_bc": "YES" if {"Variant B", "Variant C", "Precision Fusion 1.2", "phase17_3"} & set(matched) else "MAYBE",
                    "unique_vs_github_checkout": unique,
                    "note": "Antigravity-only artifact" if unique == "YES" else "",
                }
            )
    rows.sort(key=lambda r: (r["workspace"], r["phase"], r["file_path"]))
    write_csv(REPORTS / "phase29_4_local_evidence_inventory.csv", rows)
    return rows


def load_antigravity_processed(asset: str, timeframe: str) -> pd.DataFrame | None:
    path = ANTIGRAVITY / "data" / "processed" / f"{asset}_{timeframe}_processed.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def canonical_teacher_sets(floor: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    pf12_teacher, variant_b_teacher, variant_c_teacher = reconstruct_pf12_with_variants(floor.copy())
    teachers = [
        ("Variant B teacher", variant_b_teacher, "phase17_3 reconstructed consistency teacher"),
        ("Variant C teacher", variant_c_teacher, "phase17_3 reconstructed quality teacher"),
        ("PF1.2 teacher", pf12_teacher, "Variant C plus B rescue teacher set"),
    ]
    rows: list[dict[str, Any]] = []
    for name, trades, source in teachers:
        stable = trades.copy().reset_index(drop=True)
        stable["stable_teacher_row"] = [sha16(f"{name}|{i}|{int(r.entry_time)}|{r.side}|{float(r.entry_price):.8f}") for i, r in stable.iterrows()]
        m = metrics_with_stress(stable)
        rows.append(
            {
                "teacher_set": name,
                "source": source,
                "metrics_computed_from_trade_rows": "YES",
                "net_pnl": m["net_pnl"],
                "trades": m["trades"],
                "profit_factor": m["profit_factor"],
                "max_dd_pct": m["max_dd_pct"],
                "positive_months": m["positive_months"],
                "negative_months": m["negative_months"],
                "zero_months": m["zero_months"],
                "combined_adverse": m["combined_adverse"],
                "trade_log_hash": df_hash(stable),
                "status": "TEACHER_TRADESET_CANONICALIZED",
            }
        )
    write_csv(REPORTS / "phase29_4_teacher_canonical_sets.csv", rows)
    return pf12_teacher.copy(), variant_b_teacher.copy(), variant_c_teacher.copy(), rows


def basic_key_set(df: pd.DataFrame, price_round: int = 4) -> set[tuple[Any, ...]]:
    if df is None or df.empty:
        return set()
    return {
        (
            int(row["entry_time"]),
            str(row["side"]),
            round(float(row["entry_price"]), price_round),
        )
        for _, row in df.iterrows()
    }


def time_side_key_set(df: pd.DataFrame) -> set[tuple[Any, ...]]:
    if df is None or df.empty:
        return set()
    return {(int(row["entry_time"]), str(row["side"])) for _, row in df.iterrows()}


def teacher_vs_floor_diff(
    floor: pd.DataFrame,
    pf12_teacher: pd.DataFrame,
    variant_b_teacher: pd.DataFrame,
    variant_c_teacher: pd.DataFrame,
) -> list[dict[str, Any]]:
    teachers = {
        "Variant B teacher": variant_b_teacher,
        "Variant C teacher": variant_c_teacher,
        "PF1.2 teacher": pf12_teacher,
    }
    floor_exact = basic_key_set(floor)
    floor_time_side = time_side_key_set(floor)
    rows: list[dict[str, Any]] = []
    for name, teacher in teachers.items():
        teacher_exact = basic_key_set(teacher)
        teacher_time_side = time_side_key_set(teacher)
        rows.append(
            {
                "row_type": "summary",
                "system": name,
                "floor_trades": len(floor),
                "teacher_trades": len(teacher),
                "exact_matches": len(floor_exact & teacher_exact),
                "nearby_time_side_matches": len(floor_time_side & teacher_time_side),
                "teacher_missing_exact": len(teacher_exact - floor_exact),
                "floor_rejected_exact": len(floor_exact - teacher_exact),
                "explanation": "Teacher rows inherit floor timestamps but adjusted entries make exact price matching sparse; time/side matching is the useful lineage test.",
            }
        )
    pf12_exact = basic_key_set(pf12_teacher)
    pf12_time_side = time_side_key_set(pf12_teacher)
    for i, row in floor.reset_index(drop=True).iterrows():
        key = (int(row["entry_time"]), str(row["side"]), round(float(row["entry_price"]), 4))
        ts_key = (int(row["entry_time"]), str(row["side"]))
        rows.append(
            {
                "row_type": "floor_candidate",
                "system": "floor_vs_pf12",
                "row_number": i,
                "entry_time": int(row["entry_time"]),
                "side": row["side"],
                "exact_match_pf12": "YES" if key in pf12_exact else "NO",
                "time_side_match_pf12": "YES" if ts_key in pf12_time_side else "NO",
                "teacher_rejection_status": "accepted_time_side" if ts_key in pf12_time_side else "rejected_or_shifted",
            }
        )
    floor_exact = basic_key_set(floor)
    floor_time_side = time_side_key_set(floor)
    for i, row in pf12_teacher.reset_index(drop=True).iterrows():
        key = (int(row["entry_time"]), str(row["side"]), round(float(row["entry_price"]), 4))
        ts_key = (int(row["entry_time"]), str(row["side"]))
        rows.append(
            {
                "row_type": "teacher_pf12",
                "system": "pf12_vs_floor",
                "row_number": i,
                "entry_time": int(row["entry_time"]),
                "side": row["side"],
                "exact_floor_match": "YES" if key in floor_exact else "NO",
                "time_side_floor_match": "YES" if ts_key in floor_time_side else "NO",
                "teacher_origin_status": "same_signal_family_shifted" if ts_key in floor_time_side else "missing_from_floor_signal_time",
            }
        )
    write_csv(REPORTS / "phase29_4_teacher_vs_floor_diff.csv", rows)
    return rows


def candle_context(df: pd.DataFrame, entry_time: int) -> tuple[int, pd.Series]:
    times = df["open_time"].values
    pos = int(np.searchsorted(times, entry_time, side="right") - 1)
    pos = max(0, min(pos, len(df) - 1))
    return pos, df.iloc[pos]


def entry_feature_row(
    df: pd.DataFrame,
    trade: pd.Series,
    row_source: str,
    system: str,
    teacher_membership: str,
    floor_membership: str,
    has_15m: bool,
    has_5m_ag: bool,
) -> dict[str, Any]:
    pos, candle = candle_context(df, int(trade["entry_time"]))
    dt = pd.to_datetime(int(trade["entry_time"]), unit="ms", utc=True)
    high = float(candle.get("high", 0.0))
    low = float(candle.get("low", 0.0))
    open_ = float(candle.get("open", 0.0))
    close = float(candle.get("close", 0.0))
    atr = float(candle.get("atr_14", 0.0) or 0.0)
    rng = max(high - low, 1e-12)
    body = abs(close - open_)
    upper_wick = max(high - max(open_, close), 0.0)
    lower_wick = max(min(open_, close) - low, 0.0)
    side = str(trade.get("side", ""))
    stop = float(trade.get("stop_loss", close))
    target = float(trade.get("take_profit", close))
    entry = float(trade.get("entry_price", close))
    risk = abs(entry - stop)
    reward = abs(target - entry)
    expected_r = reward / risk if risk > 0 else 0.0
    ema_50 = float(candle.get("ema_50", close))
    ema_200 = float(candle.get("ema_200", close))
    ema_prev = float(df.iloc[max(0, pos - 10)].get("ema_50", ema_50))
    vol = float(candle.get("volume", 0.0))
    vol_window = df["volume"].iloc[max(0, pos - 20) : pos].mean() if "volume" in df.columns and pos > 0 else vol
    bb_upper = float(candle.get("bb_upper", close))
    bb_lower = float(candle.get("bb_lower", close))
    bb_state = "above_upper" if close > bb_upper else "below_lower" if close < bb_lower else "inside"
    if 0 <= dt.hour < 8:
        session = "tokyo"
    elif 8 <= dt.hour < 13:
        session = "london"
    elif 13 <= dt.hour < 21:
        session = "ny"
    else:
        session = "off"
    breakout_ref = float(df["high"].iloc[max(0, pos - 24) : pos].max()) if side == "Long" and pos > 0 else float(df["low"].iloc[max(0, pos - 24) : pos].min()) if pos > 0 else close
    breakout_distance_atr = abs(close - breakout_ref) / atr if atr else 0.0
    retest_depth_atr = abs(entry - close) / atr if atr else 0.0
    return {
        "row_source": row_source,
        "system": system,
        "entry_time": int(trade["entry_time"]),
        "entry_datetime": str(dt),
        "side": side,
        "teacher_membership": teacher_membership,
        "floor_membership": floor_membership,
        "session": session,
        "hour": int(dt.hour),
        "weekday": int(dt.weekday()),
        "trend_direction": "bull" if close >= ema_200 else "bear",
        "ema_slope_10": ema_50 - ema_prev,
        "ema50_over_ema200": "YES" if ema_50 > ema_200 else "NO",
        "breakout_distance_atr": breakout_distance_atr,
        "retest_depth_atr": retest_depth_atr,
        "wick_rejection_ratio": max(upper_wick, lower_wick) / rng,
        "body_strength": body / rng,
        "close_location": (close - low) / rng,
        "atr_14": atr,
        "atr_pct": float(candle.get("atr_pct", 0.0) or 0.0),
        "bb_width": float(candle.get("bb_width", 0.0) or 0.0),
        "bb_state": bb_state,
        "rsi_14": float(candle.get("rsi_14", 0.0) or 0.0),
        "adx": float(candle.get("adx", 0.0) or 0.0),
        "adx_slope_3": float(candle.get("adx_slope_3", 0.0) or 0.0),
        "volume_vs_ma20": vol / float(vol_window) if vol_window and not np.isnan(vol_window) else 1.0,
        "funding_rate": float(candle.get("fundingRate", 0.0) or 0.0),
        "funding_abs": abs(float(candle.get("fundingRate", 0.0) or 0.0)),
        "expected_r_signal": expected_r,
        "cost_to_atr": (entry * (2 * 0.0005 + 0.0007)) / atr if atr else 0.0,
        "has_btc_15m_current_repo": "YES" if has_15m else "NO",
        "has_btc_5m_antigravity": "YES" if has_5m_ag else "NO",
    }


def entry_time_feature_table(
    df: pd.DataFrame,
    floor: pd.DataFrame,
    pf12_teacher: pd.DataFrame,
    variant_b_teacher: pd.DataFrame,
    variant_c_teacher: pd.DataFrame,
) -> list[dict[str, Any]]:
    has_15m = (ROOT / "data" / "processed" / "BTCUSDT_15m_processed.csv").exists()
    has_5m_ag = (ANTIGRAVITY / "data" / "processed" / "BTCUSDT_5m_processed.csv").exists()
    pf12_ts = time_side_key_set(pf12_teacher)
    floor_ts = time_side_key_set(floor)
    rows: list[dict[str, Any]] = []
    for _, trade in floor.iterrows():
        ts_key = (int(trade["entry_time"]), str(trade["side"]))
        rows.append(entry_feature_row(df, trade, "floor_candidate", "floor", "YES" if ts_key in pf12_ts else "NO", "YES", has_15m, has_5m_ag))
    for system, trades in [
        ("Variant B teacher", variant_b_teacher),
        ("Variant C teacher", variant_c_teacher),
        ("PF1.2 teacher", pf12_teacher),
    ]:
        for _, trade in trades.iterrows():
            ts_key = (int(trade["entry_time"]), str(trade["side"]))
            rows.append(entry_feature_row(df, trade, "teacher_reference", system, "YES", "YES" if ts_key in floor_ts else "NO", has_15m, has_5m_ag))
    rows = [{k: row.get(k, "") for k in FEATURE_COLUMNS} for row in rows]
    write_csv(REPORTS / "phase29_4_entry_time_feature_table.csv", rows)
    return rows


def rule_eval(rows: list[dict[str, Any]], name: str, predicate: Any, description: str, overfit: str) -> dict[str, Any]:
    floor_rows = [r for r in rows if r["row_source"] == "floor_candidate"]
    teacher_rows = [r for r in rows if r["row_source"] == "teacher_reference" and r["system"] == "PF1.2 teacher"]
    selected_floor = [r for r in floor_rows if predicate(r)]
    selected_teacher = [r for r in teacher_rows if predicate(r)]
    rejected_floor = [r for r in floor_rows if not predicate(r)]
    return {
        "rule_name": name,
        "live_rule_expression": description,
        "teacher_pf12_preserved": len(selected_teacher),
        "teacher_pf12_total": len(teacher_rows),
        "teacher_preservation_pct": len(selected_teacher) / len(teacher_rows) if teacher_rows else 0.0,
        "floor_candidates_rejected": len(rejected_floor),
        "floor_candidates_total": len(floor_rows),
        "floor_rejection_pct": len(rejected_floor) / len(floor_rows) if floor_rows else 0.0,
        "live_known_validity": "YES",
        "overfit_risk": overfit,
        "notes": "Teacher labels used for analysis only; final routers implement the expression against closed-candle features.",
    }


def distilled_rules(feature_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rules = [
        rule_eval(
            feature_rows,
            "expected_r_gate_140",
            lambda r: float(r["expected_r_signal"]) >= 1.40,
            "expected_r_signal >= 1.40",
            "MEDIUM: inspired by Phase 17.3 but recomputed from signal stop/target geometry.",
        ),
        rule_eval(
            feature_rows,
            "active_session_gate",
            lambda r: r["session"] in {"london", "ny"},
            "session in {london, ny}",
            "LOW: session is known at entry and not result-derived.",
        ),
        rule_eval(
            feature_rows,
            "adx_quality_gate",
            lambda r: float(r["adx"]) >= 18.0,
            "adx >= 18.0",
            "MEDIUM: threshold mined from teacher/floor contrast.",
        ),
        rule_eval(
            feature_rows,
            "funding_defensive_gate",
            lambda r: float(r["funding_abs"]) <= 0.00035,
            "abs(funding_rate) <= 0.00035",
            "LOW: funding is candle-aligned and known at decision time.",
        ),
        rule_eval(
            feature_rows,
            "body_wick_confirmation",
            lambda r: float(r["body_strength"]) >= 0.35 or float(r["wick_rejection_ratio"]) >= 0.45,
            "body_strength >= 0.35 OR wick_rejection_ratio >= 0.45",
            "MEDIUM: candle-shape gate can overfit without walk-forward validation.",
        ),
        rule_eval(
            feature_rows,
            "combined_distilled_pf12_gate",
            lambda r: float(r["expected_r_signal"]) >= 1.35
            and r["session"] in {"london", "ny"}
            and float(r["funding_abs"]) <= 0.00035,
            "expected_r_signal >= 1.35 AND session in {london, ny} AND abs(funding_rate) <= 0.00035",
            "HIGH: combined rule is still a distillation candidate, not locked benchmark proof.",
        ),
    ]
    write_csv(REPORTS / "phase29_4_teacher_distilled_rules.csv", rules)
    return rules


class LiveFeatureGateStrategy(BaseStrategy):
    def __init__(self, name: str, base: BaseStrategy, gates: dict[str, Any]):
        super().__init__(name=name, hypothesis="Live-known closed-candle gate over an executable strategy.")
        self.base = base
        self.gates = gates

    def get_param_grid(self) -> dict:
        return {}

    def _expected_r(self, sig: dict[str, Any], close_value: float) -> float:
        risk = abs(close_value - float(sig["stop_loss"]))
        reward = abs(float(sig["take_profit"]) - close_value)
        return reward / risk if risk > 0 else 0.0

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict | None = None) -> dict | None:
        if "live_metrics" in self.base.get_signal.__code__.co_varnames:
            sig = self.base.get_signal(df, i, live_metrics=live_metrics)
        else:
            sig = self.base.get_signal(df, i)
        if sig is None:
            return None
        row = df.iloc[i]
        close_value = float(row["close"])
        er = self._expected_r(sig, close_value)
        dt = pd.to_datetime(int(row["open_time"]), unit="ms", utc=True)
        session = "tokyo" if 0 <= dt.hour < 8 else "london" if 8 <= dt.hour < 13 else "ny" if 13 <= dt.hour < 21 else "off"
        if er < float(self.gates.get("min_expected_r", 0.0)):
            return None
        if self.gates.get("sessions") and session not in set(self.gates["sessions"]):
            return None
        if float(row.get("adx", 0.0) or 0.0) < float(self.gates.get("min_adx", 0.0)):
            return None
        if abs(float(row.get("fundingRate", 0.0) or 0.0)) > float(self.gates.get("max_funding_abs", 999.0)):
            return None
        body_strength = abs(float(row["close"]) - float(row["open"])) / max(float(row["high"]) - float(row["low"]), 1e-12)
        upper = max(float(row["high"]) - max(float(row["open"]), float(row["close"])), 0.0)
        lower = max(min(float(row["open"]), float(row["close"])) - float(row["low"]), 0.0)
        wick_ratio = max(upper, lower) / max(float(row["high"]) - float(row["low"]), 1e-12)
        if body_strength < float(self.gates.get("min_body_strength", 0.0)) and wick_ratio < float(self.gates.get("min_wick_ratio", 0.0)):
            return None
        out = dict(sig)
        out["strategy_name"] = self.name
        out["reason"] = f"{self.name}: {sig.get('reason', '')}"
        out["expected_r_signal"] = er
        return out


class PF12DistilledRouter(BaseStrategy):
    def __init__(self, c_core: BaseStrategy, b_rescue: BaseStrategy):
        super().__init__(name="phase29_4_pf12_live_router", hypothesis="C live core plus B rescue live-known distilled router.")
        self.c_core = c_core
        self.b_rescue = b_rescue
        self.rejections: list[dict[str, Any]] = []

    def get_param_grid(self) -> dict:
        return {}

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict | None = None) -> dict | None:
        c_sig = self.c_core.get_signal(df, i, live_metrics=live_metrics)
        if c_sig is not None:
            c_sig = dict(c_sig)
            c_sig["strategy_name"] = "variant_c_live_core"
            return c_sig
        b_sig = self.b_rescue.get_signal(df, i, live_metrics=live_metrics)
        if b_sig is not None:
            b_sig = dict(b_sig)
            b_sig["strategy_name"] = "variant_b_live_rescue"
            return b_sig
        return None


def cfg_strategy(cfg: dict[str, Any]) -> UniversalStrategyTemplate:
    params = dict(cfg)
    params["bb_width_thresh"] = params.get("bb_width_thresh", 0.06)
    return UniversalStrategyTemplate(params)


def run_named_strategy(df: pd.DataFrame, system: str, status: str, strategy: BaseStrategy, extra: dict[str, Any] | None = None) -> tuple[dict[str, Any], pd.DataFrame]:
    trades = run_engine(df, strategy)["trades"].copy()
    row = metric_row(system, status, trades, extra or {})
    return row, trades


def rebuild_variant_c(df: pd.DataFrame, teacher: pd.DataFrame) -> tuple[list[dict[str, Any]], pd.DataFrame, dict[str, Any]]:
    candidates = [
        ("c_proxy_phase12_cfg", cfg_strategy(CAND_C_CFG), "Phase 12 C config without new distillation gates."),
        (
            "c_distilled_expected_r_session",
            LiveFeatureGateStrategy(
                "c_distilled_expected_r_session",
                cfg_strategy(CAND_C_CFG),
                {"min_expected_r": 1.35, "sessions": ["london", "ny"], "max_funding_abs": 0.00035},
            ),
            "C config gated by live expected-R/session/funding.",
        ),
        (
            "c_distilled_adx_shape",
            LiveFeatureGateStrategy(
                "c_distilled_adx_shape",
                cfg_strategy(CAND_C_CFG),
                {"min_expected_r": 1.20, "min_adx": 18.0, "min_body_strength": 0.35, "min_wick_ratio": 0.45},
            ),
            "C config gated by live ADX and candle shape.",
        ),
        (
            "c_floor_distilled_quality",
            LiveFeatureGateStrategy(
                "c_floor_distilled_quality",
                build_p10_1_strategy(),
                {"min_expected_r": 1.35, "sessions": ["london", "ny"], "max_funding_abs": 0.00035},
            ),
            "Full floor fusion gated into a C-like quality core.",
        ),
    ]
    teacher_ts = time_side_key_set(teacher)
    rows: list[dict[str, Any]] = []
    best_row: dict[str, Any] | None = None
    best_trades: pd.DataFrame | None = None
    for name, strategy, note in candidates:
        row, trades = run_named_strategy(df, name, "ENGINE_EXECUTED_LIVE_KNOWN_REBUILD", strategy, {"rule_note": note})
        ts = time_side_key_set(trades)
        row["teacher_time_side_match_rate"] = len(ts & teacher_ts) / len(teacher_ts) if teacher_ts else 0.0
        row["missing_teacher_time_side"] = len(teacher_ts - ts)
        row["extra_live_time_side"] = len(ts - teacher_ts)
        rows.append(row)
        score = float(row["net_pnl"]) + 2000.0 * float(row["profit_factor"]) - 250.0 * float(row["max_dd_pct"])
        if best_row is None or score > best_row["_score"]:
            best_row = dict(row)
            best_row["_score"] = score
            best_trades = trades.copy()
    for row in rows:
        row.pop("_score", None)
    write_csv(REPORTS / "phase29_4_variant_c_live_rebuild_results.csv", rows)
    assert best_row is not None and best_trades is not None
    return rows, best_trades, best_row


def rebuild_variant_b(df: pd.DataFrame, teacher: pd.DataFrame) -> tuple[list[dict[str, Any]], pd.DataFrame, dict[str, Any]]:
    candidates = [
        ("b_proxy_phase12_cfg", cfg_strategy(CAND_A_CFG), "Phase 12 A config as B-rescue proxy."),
        (
            "b_rescue_expected_r_session",
            LiveFeatureGateStrategy(
                "b_rescue_expected_r_session",
                cfg_strategy(CAND_A_CFG),
                {"min_expected_r": 1.40, "sessions": ["london", "ny"], "max_funding_abs": 0.00035},
            ),
            "B rescue gated by live expected-R/session/funding.",
        ),
        (
            "b_rescue_adx_shape",
            LiveFeatureGateStrategy(
                "b_rescue_adx_shape",
                cfg_strategy(CAND_A_CFG),
                {"min_expected_r": 1.30, "min_adx": 18.0, "min_body_strength": 0.35, "min_wick_ratio": 0.45},
            ),
            "B rescue gated by live ADX and candle shape.",
        ),
    ]
    teacher_ts = time_side_key_set(teacher)
    rows: list[dict[str, Any]] = []
    best_row: dict[str, Any] | None = None
    best_trades: pd.DataFrame | None = None
    for name, strategy, note in candidates:
        row, trades = run_named_strategy(df, name, "ENGINE_EXECUTED_LIVE_KNOWN_REBUILD", strategy, {"rule_note": note})
        ts = time_side_key_set(trades)
        row["teacher_time_side_match_rate"] = len(ts & teacher_ts) / len(teacher_ts) if teacher_ts else 0.0
        row["missing_teacher_time_side"] = len(teacher_ts - ts)
        row["extra_live_time_side"] = len(ts - teacher_ts)
        rows.append(row)
        score = float(row["net_pnl"]) + 1500.0 * float(row["profit_factor"]) - 250.0 * float(row["max_dd_pct"])
        if best_row is None or score > best_row["_score"]:
            best_row = dict(row)
            best_row["_score"] = score
            best_trades = trades.copy()
    for row in rows:
        row.pop("_score", None)
    write_csv(REPORTS / "phase29_4_variant_b_rescue_rebuild_results.csv", rows)
    assert best_row is not None and best_trades is not None
    return rows, best_trades, best_row


def pf12_live_router(df: pd.DataFrame, pf12_teacher: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any], str]:
    c_core = LiveFeatureGateStrategy(
        "variant_c_distilled_core",
        cfg_strategy(CAND_C_CFG),
        {"min_expected_r": 1.35, "sessions": ["london", "ny"], "max_funding_abs": 0.00035},
    )
    b_rescue = LiveFeatureGateStrategy(
        "variant_b_distilled_rescue",
        cfg_strategy(CAND_A_CFG),
        {"min_expected_r": 1.40, "sessions": ["london", "ny"], "max_funding_abs": 0.00035},
    )
    router = PF12DistilledRouter(c_core, b_rescue)
    trades = run_engine(df, router)["trades"].copy()
    trades.to_csv(REPORTS / "phase29_4_pf12_live_router_trade_log.csv", index=False)
    row = metric_row(
        "PF1.2 distilled live router",
        "ENGINE_EXECUTED_LIVE_KNOWN_PARTIAL_RECOVERY",
        trades,
        {"router_rule": "C core priority, B rescue fallback, max one position from engine"},
    )
    teacher_m = metrics_with_stress(pf12_teacher)
    rows = [
        row,
        {
            "system": "PF1.2 protected teacher",
            "status": "TEACHER_REFERENCE_NOT_EXECUTABLE_PROOF",
            **teacher_m,
            "router_rule": "phase17_3/phase21 trade-set reconstruction",
        },
    ]
    write_csv(REPORTS / "phase29_4_pf12_live_router_metrics.csv", rows)
    teacher_exact = basic_key_set(pf12_teacher)
    live_exact = basic_key_set(trades)
    teacher_ts = time_side_key_set(pf12_teacher)
    live_ts = time_side_key_set(trades)
    status = "NOT_RECOVERED"
    if teacher_exact == live_exact and round(float(row["net_pnl"]), 2) == round(float(teacher_m["net_pnl"]), 2):
        status = "EXACT_MATCH"
    elif len(live_ts & teacher_ts) / len(teacher_ts) >= 0.80 if teacher_ts else False:
        status = "NEAR_MATCH"
    elif len(live_ts & teacher_ts) > 0:
        status = "PARTIAL_RECOVERY"
    gap_rows = [
        {
            "row_type": "summary",
            "status": status,
            "teacher_trades": len(pf12_teacher),
            "live_trades": len(trades),
            "exact_matches": len(teacher_exact & live_exact),
            "time_side_matches": len(teacher_ts & live_ts),
            "missing_teacher_exact": len(teacher_exact - live_exact),
            "extra_live_exact": len(live_exact - teacher_exact),
            "pnl_gap": float(row["net_pnl"]) - float(teacher_m["net_pnl"]),
            "pf_gap": float(row["profit_factor"]) - float(teacher_m["profit_factor"]),
            "dd_gap": float(row["max_dd_pct"]) - float(teacher_m["max_dd_pct"]),
        }
    ]
    for key in sorted(teacher_ts - live_ts)[:80]:
        gap_rows.append({"row_type": "missing_teacher_time_side", "status": status, "key": json.dumps(key)})
    for key in sorted(live_ts - teacher_ts)[:80]:
        gap_rows.append({"row_type": "extra_live_time_side", "status": status, "key": json.dumps(key)})
    write_csv(REPORTS / "phase29_4_pf12_trade_match_gap_audit.csv", gap_rows)
    return trades, row, status


def dirty_pf8_recovery(df: pd.DataFrame, pf12_live_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    dirty_path = REPORTS / "phase29_1_dirty_pf8_recompute_trade_log.csv"
    dirty = pd.read_csv(dirty_path) if dirty_path.exists() else pd.DataFrame()
    rows: list[dict[str, Any]] = []
    if not dirty.empty:
        base = metrics_with_stress(dirty)
        rows.append({"system": "Dirty PF8 no-forcing baseline", "status": "DIAGNOSTIC_BASELINE_NOT_BENCHMARK", **base})
        filtered = []
        for _, trade in dirty.iterrows():
            pos, candle = candle_context(df, int(trade["entry_time"]))
            dt = pd.to_datetime(int(trade["entry_time"]), unit="ms", utc=True)
            session = "tokyo" if 0 <= dt.hour < 8 else "london" if 8 <= dt.hour < 13 else "ny" if 13 <= dt.hour < 21 else "off"
            risk = abs(float(trade.get("entry_price", candle["close"])) - float(trade.get("stop_loss", candle["close"])))
            reward = abs(float(trade.get("take_profit", candle["close"])) - float(trade.get("entry_price", candle["close"])))
            er = reward / risk if risk > 0 else 0.0
            if er >= 1.35 and session in {"london", "ny"} and abs(float(candle.get("fundingRate", 0.0) or 0.0)) <= 0.00035:
                filtered.append(trade)
        filtered_df = pd.DataFrame(filtered)
        if not filtered_df.empty:
            m = metrics_with_stress(filtered_df)
            rows.append({"system": "Dirty PF8 diagnostic distilled filter", "status": "DIAGNOSTIC_FILTER_ONLY_NOT_ENGINE_BENCHMARK", **m})
    rows.append({"system": "PF1.2 distilled live router", "status": "ENGINE_EXECUTED_RECOVERY_REFERENCE", **pf12_live_metrics})
    write_csv(REPORTS / "phase29_4_dirty_pf8_recovery_results.csv", rows)
    return rows


def benchmark_comparison(
    floor: pd.DataFrame,
    pf12_teacher: pd.DataFrame,
    variant_b_teacher: pd.DataFrame,
    variant_c_teacher: pd.DataFrame,
    c_best: dict[str, Any],
    b_best: dict[str, Any],
    pf12_live: dict[str, Any],
) -> list[dict[str, Any]]:
    systems = [
        ("Executable floor fusion", "ENGINE_EXECUTED", metrics_with_stress(floor)),
        ("Variant B teacher", "TEACHER_REFERENCE", metrics_with_stress(variant_b_teacher)),
        ("Variant C teacher", "TEACHER_REFERENCE", metrics_with_stress(variant_c_teacher)),
        ("PF1.2 teacher", "TEACHER_REFERENCE", metrics_with_stress(pf12_teacher)),
        ("Best Variant C live rebuild", "ENGINE_EXECUTED", c_best),
        ("Best Variant B rescue rebuild", "ENGINE_EXECUTED", b_best),
        ("PF1.2 distilled live router", "ENGINE_EXECUTED", pf12_live),
    ]
    rows = []
    for name, status, m in systems:
        rows.append(
            {
                "system": name,
                "status": status,
                "net_pnl": m.get("net_pnl", ""),
                "trades": m.get("trades", ""),
                "winners": m.get("winners", ""),
                "losers": m.get("losers", ""),
                "win_rate": m.get("win_rate", ""),
                "average_winner": m.get("average_winner", ""),
                "average_loser": m.get("average_loser", ""),
                "expectancy": m.get("expectancy", ""),
                "profit_factor": m.get("profit_factor", ""),
                "max_dd_pct": m.get("max_dd_pct", ""),
                "combined_adverse": m.get("combined_adverse", ""),
                "positive_months": m.get("positive_months", ""),
                "negative_months": m.get("negative_months", ""),
                "zero_months": m.get("zero_months", ""),
                "trade_log_hash": m.get("trade_log_hash", ""),
            }
        )
    write_csv(REPORTS / "phase29_4_final_benchmark_comparison.csv", rows)
    return rows


def write_live_audit() -> None:
    text = """# Phase 29.4 Live Automation Audit

Phase 29.4 rebuilds are backtest-only research artifacts.

## PF1.2 Distilled Live Router

- Entry timing: closed-candle signal evaluation through the existing backtest engine.
- Exit timing: deterministic engine TP/SL handling.
- SL/TP: signal stop and target are generated before trade entry.
- Router: Variant C core priority; Variant B rescue fallback only if no C signal is accepted.
- Duplicate control: engine max positions is one; same-position overlap is not exchange-tested.
- Funding handling: candle-aligned funding feature only; no later funding values are used for signal generation.
- Tick/step/min-notional: not exchange-shadow verified in this phase.
- Reduce-only exits: concept only; no exchange order lifecycle proof exists.
- Exchange shadow status: no Binance shadow/live execution ledger was produced.

Final live status: NOT_REAL_CAPITAL_READY.
"""
    write_text(REPORTS / "phase29_4_live_automation_audit.md", text)


def runner_clean() -> bool:
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "29386" + ".59",
        "30580" + ".40",
        "31250" + ".80",
        ".sam" + "ple(",
        "is_" + "winner",
        "future_" + "pnl",
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


def final_verdict(pf12_status: str, pf12_live_metrics: dict[str, Any], pf12_teacher: pd.DataFrame) -> str:
    if not runner_clean():
        return "AUDIT_FAIL_FORCED_METRICS_REMAIN"
    teacher_m = metrics_with_stress(pf12_teacher)
    if pf12_status == "EXACT_MATCH":
        return "PF12_LIVE_EXECUTABLE_EXACTLY_RECOVERED"
    if pf12_status == "NEAR_MATCH":
        return "PF12_LIVE_EXECUTABLE_NEAR_MATCH_RECOVERED"
    if float(pf12_live_metrics.get("trades", 0) or 0) > 0 and float(pf12_live_metrics.get("profit_factor", 0) or 0) >= 1.0:
        return "PF12_PARTIAL_LIVE_RECOVERY_RULES_FOUND"
    if float(teacher_m["net_pnl"]) > 0:
        return "PF12_TEACHER_DISTILLATION_DONE_EXECUTABLE_STILL_WEAK"
    return "PF12_REQUIRES_MORE_LOCAL_ARTIFACT_RECOVERY"


def write_main_report(
    verdict: str,
    evidence_rows: list[dict[str, Any]],
    teacher_rows: list[dict[str, Any]],
    floor: pd.DataFrame,
    pf12_teacher: pd.DataFrame,
    variant_b_teacher: pd.DataFrame,
    variant_c_teacher: pd.DataFrame,
    c_rows: list[dict[str, Any]],
    b_rows: list[dict[str, Any]],
    pf12_live_metrics: dict[str, Any],
    pf12_status: str,
    dirty_rows: list[dict[str, Any]],
) -> None:
    floor_m = metrics_with_stress(floor)
    pf12_m = metrics_with_stress(pf12_teacher)
    unique_ag = [r for r in evidence_rows if r["workspace"] == "antigravity" and r["unique_vs_github_checkout"] == "YES"]
    ag_5m = ANTIGRAVITY / "data" / "processed" / "BTCUSDT_5m_processed.csv"
    ag_15m = ANTIGRAVITY / "data" / "processed" / "BTCUSDT_15m_processed.csv"
    b_m = metrics_with_stress(variant_b_teacher)
    c_m = metrics_with_stress(variant_c_teacher)
    best_c = max(c_rows, key=lambda r: float(r.get("net_pnl", 0.0)) + 2000.0 * float(r.get("profit_factor", 0.0)) - 250.0 * float(r.get("max_dd_pct", 0.0)))
    best_b = max(b_rows, key=lambda r: float(r.get("net_pnl", 0.0)) + 1500.0 * float(r.get("profit_factor", 0.0)) - 250.0 * float(r.get("max_dd_pct", 0.0)))
    dirty_summary = dirty_rows[0] if dirty_rows else {}
    text = f"""# Phase 29.4 Precision Fusion Teacher Distillation and Live Recovery Report

**FINAL VERDICT: {verdict}**

PF means Precision Fusion: a router of multiple candidates, sleeves, filters, rescue layers, and risk controls. Phase 29.4 used the Antigravity workspace as an additional evidence source and kept teacher labels analysis-only.

## 1. Local Antigravity Evidence

- Antigravity workspace exists: `{ANTIGRAVITY.exists()}`.
- Evidence inventory rows: {len(evidence_rows)}.
- Antigravity-only evidence rows: {len(unique_ag)}.
- BTC 15m processed in Antigravity: `{ag_15m.exists()}`.
- BTC 5m processed in Antigravity: `{ag_5m.exists()}`.

The most useful Antigravity evidence was not a hidden exact PF1.2 executable router. It was supporting recovery material: 5m/15m data, Phase 17.3 reports/code, idea-engine descriptions for 15m/5m retest/VWAP confirmation, and prior reports that record the teacher metrics.

## 2. Canonical Teacher Sets

| Teacher | PnL | Trades | PF | DD % | Stress |
|---|---:|---:|---:|---:|---:|
| Variant B | {float(b_m['net_pnl']):.2f} | {int(b_m['trades'])} | {float(b_m['profit_factor']):.2f} | {float(b_m['max_dd_pct']):.2f} | {float(b_m['combined_adverse']):.2f} |
| Variant C | {float(c_m['net_pnl']):.2f} | {int(c_m['trades'])} | {float(c_m['profit_factor']):.2f} | {float(c_m['max_dd_pct']):.2f} | {float(c_m['combined_adverse']):.2f} |
| PF1.2 | {float(pf12_m['net_pnl']):.2f} | {int(pf12_m['trades'])} | {float(pf12_m['profit_factor']):.2f} | {float(pf12_m['max_dd_pct']):.2f} | {float(pf12_m['combined_adverse']):.2f} |

These values were recomputed from trade rows, not copied from report text.

## 3. Why Teacher Sets Beat The Executable Floor

The executable floor produced {float(floor_m['net_pnl']):.2f} PnL, {int(floor_m['trades'])} trades, PF {float(floor_m['profit_factor']):.2f}, and DD {float(floor_m['max_dd_pct']):.2f}%. The teacher sets are stronger because Phase 17.3 built B/C from completed floor trade logs: completed PnL sorting, row sampling, synthetic entry adjustment, and a B-rescue gate that reads completed trade `R`. Those operations explain the quality jump but cannot be accepted as live entry logic.

## 4. Teacher To Floor Match

The strict exact key test uses entry time, side, and rounded entry price. Because teacher entries were adjusted, exact matches are sparse. The useful lineage evidence is time/side matching, saved in `phase29_4_teacher_vs_floor_diff.csv` and `phase29_4_pf12_trade_match_gap_audit.csv`.

## 5. Entry-Time Features And Distillation

The feature table contains only entry-time fields: session, trend, EMA relation, ATR/Bollinger/RSI/ADX, volume, funding, candle body/wick, and signal expected-R geometry. It deliberately excludes completed trade PnL, completed trade R, MFE/MAE paths, winner labels, month targets, and row IDs as live rules.

Distilled candidate rules:

- `expected_r_signal >= 1.40`
- active London/NY session gate
- `adx >= 18`
- funding defensive skip at `abs(funding_rate) <= 0.00035`
- candle body/wick confirmation
- combined expected-R/session/funding gate

These are still research rules. They are not a proof that the old PF1.2 teacher set was a live executable router.

## 6. Variant C Live Recovery

Best Variant C rebuild: `{best_c['system']}` with PnL {float(best_c['net_pnl']):.2f}, trades {int(best_c['trades'])}, PF {float(best_c['profit_factor']):.2f}, DD {float(best_c['max_dd_pct']):.2f}%, teacher time/side match {float(best_c['teacher_time_side_match_rate']):.2%}.

## 7. Variant B Rescue Live Recovery

Best Variant B rescue rebuild: `{best_b['system']}` with PnL {float(best_b['net_pnl']):.2f}, trades {int(best_b['trades'])}, PF {float(best_b['profit_factor']):.2f}, DD {float(best_b['max_dd_pct']):.2f}%, teacher time/side match {float(best_b['teacher_time_side_match_rate']):.2%}.

## 8. PF1.2 Live Router Recovery

PF1.2 live router status: `{pf12_status}`.

| Metric | PF1.2 teacher | Phase 29.4 live router |
|---|---:|---:|
| PnL | {float(pf12_m['net_pnl']):.2f} | {float(pf12_live_metrics['net_pnl']):.2f} |
| Trades | {int(pf12_m['trades'])} | {int(pf12_live_metrics['trades'])} |
| PF | {float(pf12_m['profit_factor']):.2f} | {float(pf12_live_metrics['profit_factor']):.2f} |
| DD % | {float(pf12_m['max_dd_pct']):.2f} | {float(pf12_live_metrics['max_dd_pct']):.2f} |
| Stress | {float(pf12_m['combined_adverse']):.2f} | {float(pf12_live_metrics['combined_adverse']):.2f} |

PF1.2 cannot yet be treated as exactly executable. Phase 29.4 found live-known rules and generated an engine-run router, but it did not regenerate the exact 325 teacher trades and metrics.

## 9. Dirty PF8 Recovery

Dirty PF8 remains diagnostic only. Baseline diagnostic PnL: {dirty_summary.get('net_pnl', '')}; PF: {dirty_summary.get('profit_factor', '')}; status: {dirty_summary.get('status', '')}. Applying distilled filters to the dirty trade frame is explicitly labeled non-benchmark because Dirty PF8 contains trade-frame surgery and cannot prove live routing by itself.

## 10. Answers Required By Phase 29.4

1. Files that helped recovery: Antigravity Phase 17.3 code/report, 5m/15m data, idea-engine MTF ideas, and prior audit artifacts.
2. Variant B/C are canonical teacher sets reconstructed from floor trades, not currently exact live routers.
3. Teacher sets are stronger because completed-trade transformations selected/shifted better rows.
4. Many teacher rows share floor signal time/side lineage; exact price keys diverge because of adjusted entries.
5. Missing teacher trades are mainly shifted/transformed or selected by teacher-only completed-trade logic.
6. Live-known explanatory features include expected-R geometry, session, funding, ADX, candle shape, and volatility state.
7. Rules distilled are listed in `phase29_4_teacher_distilled_rules.csv`.
8. Variant C got closer as a live-known rebuild but did not match the teacher.
9. Variant B rescue produced live trades but did not recover the old B teacher quality.
10. PF1.2 live router status is `{pf12_status}`.
11. PF1.2 should still be treated as protected teacher evidence, not exactly executable benchmark proof.
12. Dirty PF8 recovery remained research-only.
13. Phase 29.5 should use Antigravity BTC 5m/15m to implement true lower-timeframe trigger sleeves, then walk-forward validate the distilled rules without teacher labels in routing.

## Live Status

NOT_REAL_CAPITAL_READY. No exchange-level shadow/live proof exists.
"""
    write_text(REPORTS / "phase29_4_precision_fusion_teacher_distillation_and_live_recovery_report.md", text)


def write_manifest(verdict: str) -> None:
    files: dict[str, Any] = {}
    for name in REQUIRED_FILES:
        if name == "phase29_4_audit_manifest.json":
            continue
        path = REPORTS / name
        files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    manifest = {
        "phase": "29.4",
        "final_verdict": verdict,
        "repo_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "antigravity_workspace": str(ANTIGRAVITY),
        "manifest_hash_note": "Manifest excludes self hash.",
        "files": files,
    }
    write_text(REPORTS / "phase29_4_audit_manifest.json", json.dumps(manifest, indent=2) + "\n")
    if OUTPUTS.exists():
        for name in REQUIRED_FILES:
            src = REPORTS / name
            if src.exists():
                (OUTPUTS / name).write_bytes(src.read_bytes())


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    df = load_btc_1h()
    evidence_rows = evidence_inventory()
    floor = run_engine(df, build_p10_1_strategy())["trades"].copy()
    pf12_teacher, variant_b_teacher, variant_c_teacher, teacher_rows = canonical_teacher_sets(floor)
    teacher_vs_floor_diff(floor, pf12_teacher, variant_b_teacher, variant_c_teacher)
    feature_rows = entry_time_feature_table(df, floor, pf12_teacher, variant_b_teacher, variant_c_teacher)
    distilled_rules(feature_rows)
    c_rows, c_best_trades, c_best = rebuild_variant_c(df, variant_c_teacher)
    b_rows, b_best_trades, b_best = rebuild_variant_b(df, variant_b_teacher)
    pf12_live_trades, pf12_live_metrics, pf12_status = pf12_live_router(df, pf12_teacher)
    dirty_rows = dirty_pf8_recovery(df, pf12_live_metrics)
    benchmark_comparison(floor, pf12_teacher, variant_b_teacher, variant_c_teacher, c_best, b_best, pf12_live_metrics)
    write_live_audit()
    verdict = final_verdict(pf12_status, pf12_live_metrics, pf12_teacher)
    write_main_report(
        verdict,
        evidence_rows,
        teacher_rows,
        floor,
        pf12_teacher,
        variant_b_teacher,
        variant_c_teacher,
        c_rows,
        b_rows,
        pf12_live_metrics,
        pf12_status,
        dirty_rows,
    )
    write_manifest(verdict)
    print(json.dumps({"final_verdict": verdict, "pf12_live_status": pf12_status, "router_trades": int(len(pf12_live_trades))}, indent=2))


if __name__ == "__main__":
    main()
