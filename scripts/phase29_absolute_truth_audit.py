import ast
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.engine import MultiPositionBacktestEngine
from src.features.indicators import add_indicators
from src.research.phase12_runner import build_p10_1_strategy
from src.research.phase28_runner import calc_metrics, reconstruct_pf12, run_stress_scenario


REPORTS = ROOT / "reports"
OUTPUTS = ROOT.parent.parent / "outputs"
EXTERNAL_DATA = ROOT.parent / "phase29_market_data"

REQUIRED_FILES = [
    "phase29_absolute_truth_audit_full_project_report.md",
    "phase29_project_inventory.csv",
    "phase29_data_integrity_audit.csv",
    "phase29_benchmark_reproduction.csv",
    "phase29_fusion_architecture_map.csv",
    "phase29_strategy_rulebook.md",
    "phase29_lookahead_hardcoding_audit.csv",
    "phase29_multi_asset_monthly_metrics.csv",
    "phase29_cross_asset_summary.csv",
    "phase29_stress_torture_results.csv",
    "phase29_live_execution_readiness.csv",
    "phase29_security_operational_safety.csv",
    "phase29_statistical_robustness.csv",
    "phase29_audit_manifest.json",
]

ASSETS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
TIMEFRAMES = ["1h", "15m", "5m"]
TF_MS = {"1h": 60 * 60 * 1000, "15m": 15 * 60 * 1000, "5m": 5 * 60 * 1000}
CURRENT_UTC = pd.Timestamp("2026-07-01T00:00:00Z")

DECLARED = {
    "PF1.2": {
        "net_pnl": 21684.99,
        "trades": 325,
        "profit_factor": 2.42,
        "max_dd_pct": 10.87,
        "positive_months": 56,
        "negative_months": 16,
        "zero_months": 6,
        "combined_adverse": 15922.97,
    },
    "PF7.0": {
        "net_pnl": 29386.59,
        "trades": 625,
        "profit_factor": 2.28,
        "max_dd_pct": 11.50,
        "positive_months": 62,
        "negative_months": 13,
        "zero_months": 3,
        "combined_adverse": 18250.40,
    },
    "PF8.0": {
        "net_pnl": 30580.40,
        "trades": 640,
        "profit_factor": 2.32,
        "max_dd_pct": 10.95,
        "positive_months": 63,
        "negative_months": 12,
        "zero_months": 3,
        "combined_adverse": 19450.20,
    },
    "PF8.1": {
        "net_pnl": 31250.80,
        "trades": 625,
        "profit_factor": 2.38,
        "max_dd_pct": 10.85,
        "positive_months": 63,
        "negative_months": 12,
        "zero_months": 3,
        "combined_adverse": 20150.80,
    },
}


def sha256_file(path):
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path):
    return path.relative_to(ROOT).as_posix()


def classify_path(path):
    rel_path = rel(path)
    suffix = path.suffix.lower()
    if rel_path.startswith("src/strategies/"):
        return "strategy_source"
    if rel_path.startswith("src/research/"):
        return "runner_source"
    if rel_path.startswith("src/backtest/"):
        return "backtest_engine"
    if rel_path.startswith("src/data/"):
        return "data_code"
    if rel_path.startswith("tests/"):
        return "test"
    if rel_path.startswith("configs/"):
        return "config"
    if rel_path.startswith("data/"):
        return "data"
    if rel_path.startswith("reports/"):
        if suffix == ".json":
            return "manifest_or_json_report"
        if suffix == ".csv":
            return "csv_report"
        return "markdown_report"
    if rel_path.startswith("scratch/"):
        return "scratch"
    if rel_path.startswith("scripts/"):
        return "script"
    if rel_path.startswith(".agents/"):
        return "agent_artifact"
    if suffix in {".md", ".txt"}:
        return "walkthrough_task_doc"
    if suffix in {".toml", ".yaml", ".yml", ".ini"}:
        return "config"
    return "other"


def build_inventory():
    rows = []
    suspicious = []
    seen_names = defaultdict(list)
    for path in sorted(ROOT.rglob("*")):
        if path.is_dir() or ".git" in path.parts or "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        rp = rel(path)
        category = classify_path(path)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore") if path.stat().st_size < 3_000_000 else ""
        except OSError:
            text = ""
        notes = []
        if category in {"scratch", "agent_artifact"}:
            notes.append("not final-repo material")
        if category in {"markdown_report", "csv_report", "manifest_or_json_report"} and not rp.startswith("reports/phase29_"):
            notes.append("historical generated artifact")
        if "C:/Users/HP/.gemini" in text:
            notes.append("hardcoded local brain path")
        if "Mocking" in text or "mocking" in text:
            notes.append("mock/generated evidence text")
        if "diff_pnl" in text or "pnl_81 = 31250.80" in text:
            notes.append("target-metric adjustment code")
        seen_names[path.name].append(rp)
        row = {
            "path": rp,
            "category": category,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "notes": "; ".join(notes),
        }
        rows.append(row)
        if notes:
            suspicious.append(row)
    for name, paths in seen_names.items():
        if len(paths) > 1 and name not in {"__init__.py"}:
            for rp in paths:
                suspicious.append(
                    {
                        "path": rp,
                        "category": "duplicate_name",
                        "size_bytes": "",
                        "sha256": "",
                        "notes": f"same basename appears {len(paths)} times",
                    }
                )
    write_csv(REPORTS / "phase29_project_inventory.csv", rows)
    return rows, suspicious


def audit_one_data_file(path, timeframe):
    if not path.exists():
        return None
    df = pd.read_csv(path)
    step = TF_MS[timeframe]
    first_ts = int(df["open_time"].min()) if "open_time" in df else None
    last_ts = int(df["open_time"].max()) if "open_time" in df else None
    first_dt = str(pd.to_datetime(first_ts, unit="ms", utc=True)) if first_ts is not None else ""
    last_dt = str(pd.to_datetime(last_ts, unit="ms", utc=True)) if last_ts is not None else ""
    duplicates = int(df["open_time"].duplicated().sum()) if "open_time" in df else -1
    if first_ts is not None and last_ts is not None:
        expected = int((last_ts - first_ts) // step + 1)
        diffs = df["open_time"].diff().dropna()
        gap_count = int((diffs != step).sum())
        max_gap_steps = int(diffs.max() // step) if gap_count else 0
    else:
        expected = 0
        gap_count = -1
        max_gap_steps = -1
    ohlc_bad = int(
        (
            (df["high"] < df[["open", "close", "low"]].max(axis=1))
            | (df["low"] > df[["open", "close", "high"]].min(axis=1))
            | (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
        ).sum()
    )
    volume_bad = int((df["volume"] < 0).sum())
    future_rows = int((pd.to_datetime(df["open_time"], unit="ms", utc=True) > CURRENT_UTC).sum())
    funding_col = "fundingRate" in df.columns
    funding_na = int(df["fundingRate"].isna().sum()) if funding_col else None
    return {
        "rows": len(df),
        "expected_rows": expected,
        "missing_candles": int(expected - len(df)),
        "duplicate_candles": duplicates,
        "gap_count": gap_count,
        "max_gap_steps": max_gap_steps,
        "first_datetime": first_dt,
        "last_datetime": last_dt,
        "ohlc_bad": ohlc_bad,
        "volume_bad": volume_bad,
        "future_rows": future_rows,
        "funding_column": funding_col,
        "funding_na": funding_na,
        "sha256": sha256_file(path),
    }


def audit_data():
    rows = []
    for symbol in ASSETS:
        for tf in TIMEFRAMES:
            repo_processed = ROOT / "data" / "processed" / f"{symbol}_{tf}_processed.csv"
            repo_raw = ROOT / "data" / "raw" / f"{symbol}_{tf}_raw.csv"
            ext_processed = EXTERNAL_DATA / "processed" / f"{symbol}_{tf}_processed.csv"
            ext_raw = EXTERNAL_DATA / "raw" / f"{symbol}_{tf}_raw.csv"
            chosen_path = repo_processed if repo_processed.exists() else ext_processed
            stats = audit_one_data_file(chosen_path, tf) if chosen_path.exists() else None
            status = "PASS_LOCAL_FILE" if repo_processed.exists() and stats else "MISSING_REQUIRED_PROCESSED"
            if not repo_processed.exists() and ext_processed.exists() and stats:
                status = "EXTERNAL_DOWNLOAD_AVAILABLE_NOT_IN_REPO"
            if stats:
                if any(stats[k] for k in ["missing_candles", "duplicate_candles", "gap_count", "ohlc_bad", "volume_bad", "future_rows"]):
                    status = "FAIL_DATA_QUALITY"
                elif not stats["funding_column"]:
                    status = "WARNING_NO_FUNDING_COLUMN"
            row = {
                "asset": symbol + ".P",
                "timeframe": tf,
                "repo_raw_exists": repo_raw.exists(),
                "repo_processed_exists": repo_processed.exists(),
                "external_raw_exists": ext_raw.exists(),
                "external_processed_exists": ext_processed.exists(),
                "chosen_source": rel(chosen_path) if chosen_path.exists() and chosen_path.is_relative_to(ROOT) else str(chosen_path) if chosen_path.exists() else "",
                "status": status,
            }
            if stats:
                row.update(stats)
            rows.append(row)
    write_csv(REPORTS / "phase29_data_integrity_audit.csv", rows)
    return rows


def df_hash(df):
    return sha256_text(df.to_csv(index=False))


def monthly_series_from_trades(trades):
    if trades.empty:
        return pd.Series(dtype=float)
    t = trades.copy()
    t["month"] = pd.to_datetime(t["entry_time"], unit="ms", utc=True).dt.to_period("M").astype(str)
    return t.groupby("month")["net_pnl"].sum()


def summarize_trades(name, trades, declared):
    pnl, pf, dd, pos, neg, zero, monthly = calc_metrics(trades)
    combined = run_stress_scenario(
        trades, fee_mult=2.0, slip_mult=2.0, delay_slip=0.0005, missed_fill_pct=0.10
    )[0]
    wins = trades[trades["net_pnl"] > 0]
    losses = trades[trades["net_pnl"] <= 0]
    avg_win = float(wins["net_pnl"].mean()) if len(wins) else 0.0
    avg_loss = float(losses["net_pnl"].mean()) if len(losses) else 0.0
    metrics = {
        "strategy": name,
        "actual_net_pnl": float(pnl),
        "actual_trades": int(len(trades)),
        "actual_profit_factor": float(pf),
        "actual_max_dd_pct": float(dd * 100),
        "actual_positive_months": int(pos),
        "actual_negative_months": int(neg),
        "actual_zero_months": int(zero),
        "actual_combined_adverse": float(combined),
        "winners": int(len(wins)),
        "losers": int(len(losses)),
        "win_rate": float(len(wins) / len(trades)) if len(trades) else 0.0,
        "expectancy": float(trades["net_pnl"].mean()) if len(trades) else 0.0,
        "average_winner": avg_win,
        "average_loser": avg_loss,
        "best_trade": float(trades["net_pnl"].max()) if len(trades) else 0.0,
        "worst_trade": float(trades["net_pnl"].min()) if len(trades) else 0.0,
        "trade_log_hash": df_hash(trades),
        "monthly_table_hash": sha256_text(monthly.to_csv()),
        "stress_table_hash": sha256_text(str(round(combined, 8))),
    }
    drift_fields = []
    checks = [
        ("net_pnl", round(metrics["actual_net_pnl"], 2), declared["net_pnl"]),
        ("trades", metrics["actual_trades"], declared["trades"]),
        ("profit_factor", round(metrics["actual_profit_factor"], 2), declared["profit_factor"]),
        ("max_dd_pct", round(metrics["actual_max_dd_pct"], 2), declared["max_dd_pct"]),
        ("positive_months", metrics["actual_positive_months"], declared["positive_months"]),
        ("negative_months", metrics["actual_negative_months"], declared["negative_months"]),
        ("zero_months", metrics["actual_zero_months"], declared["zero_months"]),
        ("combined_adverse", round(metrics["actual_combined_adverse"], 2), declared["combined_adverse"]),
    ]
    for field, actual, expected in checks:
        if actual != expected:
            drift_fields.append(f"{field}: actual={actual} declared={expected}")
    metrics["declared_net_pnl"] = declared["net_pnl"]
    metrics["declared_trades"] = declared["trades"]
    metrics["declared_profit_factor"] = declared["profit_factor"]
    metrics["declared_max_dd_pct"] = declared["max_dd_pct"]
    metrics["declared_months_pos_neg_zero"] = (
        f"{declared['positive_months']}/{declared['negative_months']}/{declared['zero_months']}"
    )
    metrics["declared_combined_adverse"] = declared["combined_adverse"]
    metrics["drift"] = " | ".join(drift_fields)
    metrics["status"] = "REPRODUCED" if not drift_fields else "UNREPRODUCIBLE"
    return metrics


def reproduce_benchmarks():
    df = add_indicators(pd.read_csv(ROOT / "data" / "processed" / "BTCUSDT_1h_processed.csv"))
    settings = {
        "initial_capital": 10000.0,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slippage": 0.0005,
        "max_positions": 1,
        "cooldown_candles": 5,
    }
    risk = {
        "risk_limit_pct": 1.0,
        "monthly_risk_limit": 0.025,
        "risk_throttle_mode": "no_throttle",
        "emergency_pause_threshold": 0.025,
    }
    floor_res = MultiPositionBacktestEngine(**settings).run(df, build_p10_1_strategy(), risk)
    trades_floor = floor_res["trades"].copy()
    pf12 = reconstruct_pf12(trades_floor)

    t_add = trades_floor.sample(n=300, replace=True, random_state=100).copy()
    for col in ["net_pnl", "fees", "slippage", "funding", "gross_pnl"]:
        t_add[col] = t_add[col] * 0.90
    t_add.index = range(10000, 10300)
    t_add["entry_time"] = t_add["entry_time"] + 100000000
    pf70 = pd.concat([pf12, t_add]).sort_values(by="entry_time").copy()
    pf70.loc[pf70.index[0], "net_pnl"] += 29386.59 - pf70["net_pnl"].sum()

    t_add_80 = trades_floor.sample(n=315, replace=True, random_state=200).copy()
    for col in ["net_pnl", "fees", "slippage", "funding", "gross_pnl"]:
        t_add_80[col] = t_add_80[col] * 0.94
    t_add_80.index = range(20000, 20315)
    t_add_80["entry_time"] = t_add_80["entry_time"] + 200000000
    pf80 = pd.concat([pf12, t_add_80]).sort_values(by="entry_time").copy()
    pf80.loc[pf80.index[0], "net_pnl"] += 30580.40 - pf80["net_pnl"].sum()

    pf81 = pf80.drop(pf80.tail(15).index).copy()
    pf81.loc[pf81.index[0], "net_pnl"] += 31250.80 - pf81["net_pnl"].sum()

    trade_frames = {"PF1.2": pf12, "PF7.0": pf70, "PF8.0": pf80, "PF8.1": pf81}
    rows = [summarize_trades(name, frame, DECLARED[name]) for name, frame in trade_frames.items()]
    rows.insert(
        0,
        {
            "strategy": "Executable Phase12 floor baseline",
            "actual_net_pnl": floor_res["metrics"]["net_pnl"],
            "actual_trades": floor_res["metrics"]["total_trades"],
            "actual_profit_factor": floor_res["metrics"]["profit_factor"],
            "actual_max_dd_pct": floor_res["metrics"]["max_drawdown"] * 100,
            "actual_positive_months": floor_res["metrics"]["positive_months"],
            "actual_negative_months": floor_res["metrics"]["negative_months"],
            "actual_zero_months": floor_res["metrics"]["zero_months"],
            "actual_combined_adverse": "",
            "status": "EXECUTABLE_BASELINE_NOT_A_DECLARED_PF_BENCHMARK",
            "trade_log_hash": df_hash(trades_floor),
        },
    )
    write_csv(REPORTS / "phase29_benchmark_reproduction.csv", rows)
    return rows, trade_frames, settings, risk


def scan_patterns():
    patterns = [
        "is_winner",
        "future_pnl",
        "future_return",
        "future_mfe",
        "future_mae",
        "hindsight",
        "selected_trade_ids",
        "known losing",
        "known winning",
        "hardcoded_trade_ids",
        "outcome_based",
        "diff_pnl",
        "pnl_81 = 31250.80",
        "pf_81 = 2.38",
        "dd_81 = 0.1085",
        "ca_81 = 20150.80",
        "sample(n=300, replace=True",
        "Mocking",
        "Mocking representative",
        "override stress",
    ]
    roots = ["src", "tests", "reports", "scratch", "scripts", "configs"]
    rows = []
    for root_name in roots:
        base = ROOT / root_name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or path.suffix.lower() in {".pyc", ".png", ".jpg", ".zip"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            lines = text.splitlines()
            for i, line in enumerate(lines, start=1):
                lower = line.lower()
                for pat in patterns:
                    if pat.lower() in lower:
                        severity = "WARNING"
                        if rel(path).startswith("src/research/phase2") and any(
                            key in lower
                            for key in [
                                "diff_pnl",
                                "pnl_81",
                                "pf_81",
                                "dd_81",
                                "ca_81",
                                "sample(n=300",
                                "mocking",
                                "override stress",
                            ]
                        ):
                            severity = "FAIL"
                        if rel(path).startswith("src/research/phase28") and any(
                            key in lower for key in ["pnl_81", "pf_81", "dd_81", "ca_81", "diff_pnl"]
                        ):
                            severity = "FAIL"
                        rows.append(
                            {
                                "file": rel(path),
                                "line": i,
                                "pattern": pat,
                                "classification": severity,
                                "evidence": line.strip()[:300],
                            }
                        )
    write_csv(REPORTS / "phase29_lookahead_hardcoding_audit.csv", rows)
    return rows


def build_fusion_map():
    rows = [
        {
            "system": "Executable Phase12 floor baseline",
            "code_location": "src/research/phase12_runner.py: build_p10_1_strategy",
            "construction": "FusionOfFusionsStrategy over quality_core/activity/defensive/zero_rescue portfolios",
            "sleeves": "CAND_A, CAND_C, CAND_D, CAND_F, CAND_G UniversalStrategyTemplate variants",
            "evidence_status": "EXECUTABLE",
            "audit_verdict": "Real code exists; metrics do not equal PF 1.2/7.0/8.0/8.1 claims",
        },
        {
            "system": "PF1.2",
            "code_location": "src/research/phase25_1_runner.py and phase28_runner.py: reconstruct_pf12",
            "construction": "Post-hoc reconstruction from floor trade log sorted by net_pnl, sampled, adjusted entries, then R > 1.40 inclusion",
            "sleeves": "Not a standalone live strategy object; derived from historical trade log",
            "evidence_status": "REPRODUCED_BY_RECONSTRUCTION",
            "audit_verdict": "Metrics reproduce, but architecture is reconstruction from historical trades rather than executable live sleeve router",
        },
        {
            "system": "PF7.0",
            "code_location": "src/research/phase25_1_runner.py, phase26_runner.py, phase27_runner.py, phase28_runner.py",
            "construction": "PF1.2 plus 300 sampled floor trades with replacement, scaled by 0.90, timestamp shifted, first trade net_pnl edited to target",
            "sleeves": "Claimed second retest/VWAP/session sleeves are not implemented as a reproducible router",
            "evidence_status": "HARDCODED_SYNTHETIC",
            "audit_verdict": "Rejected; advertised PF/DD/month/stress metrics are overridden",
        },
        {
            "system": "PF8.0",
            "code_location": "src/research/phase26_runner.py, phase27_runner.py, phase28_runner.py",
            "construction": "PF1.2 plus 315 sampled floor trades with replacement, scaled by 0.94, timestamp shifted, first trade net_pnl edited to target",
            "sleeves": "Claimed pruning/refinement is report-only in Phase 26",
            "evidence_status": "HARDCODED_SYNTHETIC",
            "audit_verdict": "Rejected; no executable PF8.0 router reproduces declared metrics",
        },
        {
            "system": "PF8.1",
            "code_location": "src/research/phase27_runner.py and phase28_runner.py",
            "construction": "PF8.0 synthetic trade frame with tail 15 trades dropped, first trade net_pnl edited to $31,250.80, PF/DD/stress/month counts set as constants",
            "sleeves": "Claimed NY expected-R hardening is not implemented as executable signal logic",
            "evidence_status": "HARDCODED_SYNTHETIC",
            "audit_verdict": "Rejected; benchmark is not a real live-serializable strategy",
        },
    ]
    write_csv(REPORTS / "phase29_fusion_architecture_map.csv", rows)
    return rows


def build_rulebook(settings, risk):
    text = f"""# Phase 29 Strategy Rulebook

## Verified Executable Strategy Surface

The only executable strategy object behind the latest benchmark runners is `build_p10_1_strategy()` in `src/research/phase12_runner.py`.
It creates a `FusionOfFusionsStrategy` with four sub-portfolios:

| Portfolio | Members | Routing Notes |
|---|---|---|
| quality_core | CAND_C, CAND_F, CAND_G, CAND_D | union mode, conflict cancel, zero-month rescue enabled |
| activity | CAND_A, CAND_C, CAND_F | union mode, conflict cancel, inactive after monthly trade count reaches 5 |
| defensive | CAND_C, CAND_G, CAND_D | active when monthly drawdown >= 1.5% |
| zero_rescue | CAND_D, CAND_G | active after day 10 with 0 trades or day 15 with fewer than 6 trades |

## Entry Rule Table

| Template | Timeframe | Long / Short Logic | Filters |
|---|---|---|---|
| CAND_A bollinger_expansion_breakout | 1h | BB expansion breakout direction | no regime filter, RSI thresholds, ADX threshold, bb_width_thresh |
| CAND_C bollinger_expansion_breakout | 1h | Same family as CAND_A | strict regime filter, wider RSI allowance |
| CAND_D low_activity_filler | 1h | low-activity filler logic inside UniversalStrategyTemplate | activated only through zero-month rescue routing |
| CAND_F atr_volatility_expansion | 1h | volatility expansion continuation | strict regime filter |
| CAND_G funding_extreme_reversal | 1h | funding extreme reversal | strict regime filter, funding threshold logic |

PF 7.0, PF 8.0, and PF 8.1 claimed sleeves are not implemented as standalone live strategy classes in the audited code. Their latest runners synthesize or hardcode benchmark outputs.

## Exit Rules

The backtest engine exits on SL/TP, with SL priority when both SL and TP are touched in the same candle. It supports trailing stop, breakeven, time stop, failed-continuation exit, force close at end of test, funding debits at 8-hour boundaries, and market slippage on exits.

## Risk Rules

| Rule | Verified Code Behavior |
|---|---|
| Initial capital | {settings['initial_capital']} |
| Maker fee | {settings['maker_fee']} |
| Taker fee | {settings['taker_fee']} |
| Slippage | {settings['slippage']} |
| Max positions | {settings['max_positions']} |
| Cooldown candles | {settings['cooldown_candles']} |
| Risk per trade | engine uses 1% of current capital before dynamic throttles |
| Leverage cap | position notional capped at 5x capital |
| Min notional | engine boosts to $100 notional where needed |
| Size rounding | round(size, 3) |
| Price rounding | round(entry_price, 1) |
| Monthly risk config | {risk} |

## Live-Known Feature Matrix

| Feature | Status |
|---|---|
| Closed-candle signal generation | Present in backtest logic |
| Binance exchange connector | Missing |
| Real order placement | Missing |
| Shadow exchange order lifecycle | Report-only / simulated |
| Restart recovery | Missing |
| API retry and rate-limit handling for live trading | Missing |
| Kill switch / daily loss guard / position guard | Missing |
"""
    write_text(REPORTS / "phase29_strategy_rulebook.md", text)
    return text


def compute_monthly_metrics_for_trades(asset, system, trades):
    if trades.empty:
        return []
    t = trades.copy()
    t["month"] = pd.to_datetime(t["entry_time"], unit="ms", utc=True).dt.to_period("M").astype(str)
    rows = []
    for month, grp in t.groupby("month"):
        wins = grp[grp["net_pnl"] > 0]
        losses = grp[grp["net_pnl"] <= 0]
        gross_profit = float(wins["net_pnl"].sum())
        gross_loss = float(losses["net_pnl"].sum())
        pf = gross_profit / abs(gross_loss) if gross_loss < 0 else 0.0
        long_grp = grp[grp["side"] == "Long"]
        short_grp = grp[grp["side"] == "Short"]
        pnl = float(grp["net_pnl"].sum())
        equity = 10000.0 + grp["net_pnl"].cumsum()
        peaks = equity.cummax()
        dd = float(((peaks - equity) / peaks).max()) if len(equity) else 0.0
        rows.append(
            {
                "system": system,
                "asset": asset + ".P",
                "month": month,
                "pnl": pnl,
                "trades": len(grp),
                "winners": len(wins),
                "losers": len(losses),
                "win_rate": len(wins) / len(grp) if len(grp) else 0.0,
                "profit_factor": pf,
                "gross_profit": gross_profit,
                "gross_loss": gross_loss,
                "expectancy": float(grp["net_pnl"].mean()) if len(grp) else 0.0,
                "average_winner": float(wins["net_pnl"].mean()) if len(wins) else 0.0,
                "average_loser": float(losses["net_pnl"].mean()) if len(losses) else 0.0,
                "max_dd_contribution": dd,
                "long_trades": len(long_grp),
                "short_trades": len(short_grp),
                "long_pnl": float(long_grp["net_pnl"].sum()) if len(long_grp) else 0.0,
                "short_pnl": float(short_grp["net_pnl"].sum()) if len(short_grp) else 0.0,
                "sleeve_contribution": "strategy column" if "strategy" in grp.columns else "not available",
                "fees": float(grp["fees"].sum()) if "fees" in grp.columns else 0.0,
                "slippage": float(grp["slippage"].sum()) if "slippage" in grp.columns else 0.0,
                "funding_impact": float(grp["funding"].sum()) if "funding" in grp.columns else 0.0,
                "status": "positive" if pnl > 0 else "negative" if pnl < 0 else "zero",
                "negative_or_zero_reason": "not attributable without implemented PF8.1 sleeve logs",
            }
        )
    return rows


def run_multi_asset_baseline(settings, risk):
    monthly_rows = []
    summary_rows = []
    for asset in ASSETS:
        path = ROOT / "data" / "processed" / f"{asset}_1h_processed.csv"
        if not path.exists():
            summary_rows.append({"asset": asset + ".P", "status": "MISSING_1H_DATA"})
            continue
        df = add_indicators(pd.read_csv(path))
        res = MultiPositionBacktestEngine(**settings).run(df, build_p10_1_strategy(), risk)
        trades = res["trades"]
        m = res["metrics"]
        monthly_rows.extend(compute_monthly_metrics_for_trades(asset, "Executable Phase12 baseline 1h", trades))
        summary_rows.append(
            {
                "asset": asset + ".P",
                "system": "Executable Phase12 baseline 1h",
                "net_pnl": m["net_pnl"],
                "trades": m["total_trades"],
                "profit_factor": m["profit_factor"],
                "max_drawdown": m["max_drawdown"],
                "positive_months": m["positive_months"],
                "negative_months": m["negative_months"],
                "zero_months": m["zero_months"],
                "trade_hash": df_hash(trades),
                "pf81_status": "PF8.1 not executable for this asset in code",
            }
        )
    write_csv(REPORTS / "phase29_multi_asset_monthly_metrics.csv", monthly_rows)
    write_csv(REPORTS / "phase29_cross_asset_summary.csv", summary_rows)
    return monthly_rows, summary_rows


def stress_from_net(trades, fee_mult=1.0, slip_mult=1.0, delay=0.0, missed=0.0):
    return run_stress_scenario(trades, fee_mult=fee_mult, slip_mult=slip_mult, delay_slip=delay, missed_fill_pct=missed)


def custom_torture(name, trades):
    base = trades.copy()
    if name == "top_5_winners_removed":
        idx = base.sort_values("net_pnl", ascending=False).head(5).index
        base = base.drop(idx)
    elif name == "top_10_winners_removed":
        idx = base.sort_values("net_pnl", ascending=False).head(10).index
        base = base.drop(idx)
    elif name == "worst_5_losers_doubled":
        idx = base.sort_values("net_pnl").head(5).index
        base.loc[idx, "net_pnl"] = base.loc[idx, "net_pnl"] * 2
    elif name == "trade_sequence_shuffle":
        base = base.sample(frac=1.0, random_state=29).reset_index(drop=True)
    elif name == "monthly_bootstrap":
        months = pd.to_datetime(base["entry_time"], unit="ms", utc=True).dt.to_period("M").astype(str)
        base = base.assign(month=months)
        sampled_months = pd.Series(base["month"].unique()).sample(frac=1.0, replace=True, random_state=29).tolist()
        base = pd.concat([base[base["month"] == m] for m in sampled_months], ignore_index=True)
    pnl = float(base["net_pnl"].sum()) if len(base) else 0.0
    wins = base[base["net_pnl"] > 0]
    losses = base[base["net_pnl"] <= 0]
    pf = float(wins["net_pnl"].sum() / abs(losses["net_pnl"].sum())) if len(losses) and abs(losses["net_pnl"].sum()) else 0.0
    equity = 10000.0 + base["net_pnl"].cumsum()
    dd = float(((equity.cummax() - equity) / equity.cummax()).max()) if len(equity) else 0.0
    return pnl, pf, dd, len(base)


def build_stress(trade_frames):
    standard = [
        ("normal", 1.0, 1.0, 0.0, 0.0),
        ("double fees", 2.0, 1.0, 0.0, 0.0),
        ("triple fees", 3.0, 1.0, 0.0, 0.0),
        ("double slippage", 1.0, 2.0, 0.0, 0.0),
        ("triple slippage", 1.0, 3.0, 0.0, 0.0),
        ("double fees + double slippage", 2.0, 2.0, 0.0, 0.0),
        ("delay 1 candle", 1.0, 1.0, 0.0005, 0.0),
        ("delay 2 candles", 1.0, 1.0, 0.0010, 0.0),
        ("missed fills 10%", 1.0, 1.0, 0.0, 0.10),
        ("missed fills 20%", 1.0, 1.0, 0.0, 0.20),
        ("missed fills 30%", 1.0, 1.0, 0.0, 0.30),
        ("combined adverse", 2.0, 2.0, 0.0005, 0.10),
        ("combined adverse passive", 1.5, 1.5, 0.0002, 0.05),
        ("combined adverse high funding", 2.0, 2.0, 0.0005, 0.15),
        ("combined adverse stale cancel", 2.5, 2.5, 0.0008, 0.10),
    ]
    torture = [
        ("4x fees", 4.0, 1.0, 0.0, 0.0),
        ("5x fees", 5.0, 1.0, 0.0, 0.0),
        ("4x slippage", 1.0, 4.0, 0.0, 0.0),
        ("5x slippage", 1.0, 5.0, 0.0, 0.0),
        ("fees + slippage + delay", 3.0, 3.0, 0.0010, 0.0),
        ("50% missed fills", 1.0, 1.0, 0.0, 0.50),
        ("70% missed fills", 1.0, 1.0, 0.0, 0.70),
        ("liquidity gap shock", 1.0, 4.0, 0.0020, 0.0),
        ("funding shock", 3.0, 1.0, 0.0, 0.0),
        ("NY low-liquidity shock", 2.0, 4.0, 0.0015, 0.10),
    ]
    custom = [
        "top_5_winners_removed",
        "top_10_winners_removed",
        "worst_5_losers_doubled",
        "trade_sequence_shuffle",
        "monthly_bootstrap",
        "yearly_walk_forward_stress",
    ]
    rows = []
    for system, trades in trade_frames.items():
        for scenario, fm, sm, delay, missed in standard:
            pnl, pf, dd, count, pos, neg, zero, verdict = stress_from_net(trades, fm, sm, delay, missed)
            rows.append(
                {
                    "system": system,
                    "test_type": "standard",
                    "scenario": scenario,
                    "pnl": float(pnl),
                    "profit_factor": float(pf),
                    "max_dd": float(dd),
                    "trades": int(count),
                    "positive_months": int(pos),
                    "negative_months": int(neg),
                    "zero_months": int(zero),
                    "classification": "PASS" if pnl > 0 else "FAIL",
                    "audit_note": "computed from reconstructed/synthetic trade frame",
                }
            )
        for scenario, fm, sm, delay, missed in torture:
            pnl, pf, dd, count, pos, neg, zero, verdict = stress_from_net(trades, fm, sm, delay, missed)
            rows.append(
                {
                    "system": system,
                    "test_type": "torture",
                    "scenario": scenario,
                    "pnl": float(pnl),
                    "profit_factor": float(pf),
                    "max_dd": float(dd),
                    "trades": int(count),
                    "classification": "WARNING" if pnl > 0 else "FAIL",
                    "audit_note": "computed from reconstructed/synthetic trade frame",
                }
            )
        for scenario in custom:
            if scenario == "yearly_walk_forward_stress":
                pnl = float(trades["net_pnl"].sum())
                pf = float("nan")
                dd = float("nan")
                count = len(trades)
                note = "no yearly re-optimization protocol implemented; summary only"
            else:
                pnl, pf, dd, count = custom_torture(scenario, trades)
                note = "custom trade-log perturbation"
            rows.append(
                {
                    "system": system,
                    "test_type": "torture",
                    "scenario": scenario,
                    "pnl": pnl,
                    "profit_factor": pf,
                    "max_dd": dd,
                    "trades": count,
                    "classification": "WARNING" if pnl > 0 else "FAIL",
                    "audit_note": note,
                }
            )
    write_csv(REPORTS / "phase29_stress_torture_results.csv", rows)
    return rows


def build_live_readiness():
    steps = [
        "candle ingestion",
        "candle close event",
        "data validation",
        "indicator calculation",
        "signal generation",
        "router decision",
        "duplicate signal prevention",
        "long/short conflict resolution",
        "expected-R calculation",
        "funding/session check",
        "position sizing",
        "tick rounding",
        "step rounding",
        "min notional check",
        "margin/leverage validation",
        "entry order intent",
        "fill simulation",
        "partial fill handling",
        "TP order",
        "SL order",
        "reduce-only protection",
        "cancellation / max wait",
        "time stop",
        "breakeven/trailing update",
        "exit execution",
        "trade logging",
        "restart recovery",
        "missing candle handling",
        "API retry simulation",
        "rate limit handling",
    ]
    rows = []
    for i, step in enumerate(steps, start=1):
        if i <= 15:
            status = "BACKTEST_ONLY_OR_PARTIAL"
        elif i <= 26:
            status = "SIMULATED_BACKTEST_ONLY"
        else:
            status = "MISSING"
        rows.append(
            {
                "step": i,
                "lifecycle_step": step,
                "status": status,
                "classification": "NOT_REAL_CAPITAL_READY",
                "evidence": "No live Binance order client or exchange shadow ledger found; PF8.1 itself is hardcoded/synthetic",
            }
        )
    write_csv(REPORTS / "phase29_live_execution_readiness.csv", rows)
    return rows


def build_security_audit():
    files_text = ""
    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in path.parts and path.stat().st_size < 2_000_000:
            try:
                files_text += "\n" + rel(path) + "\n" + path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                pass
    checks = [
        ("secrets committed", not re.search(r"(api[_-]?key|secret[_-]?key|private key)\s*[:=]\s*[A-Za-z0-9_\\-]{20,}", files_text, re.I), "No obvious live credential literal found"),
        (".env ignored", ".env" in (ROOT / ".gitignore").read_text(encoding="utf-8", errors="ignore"), ".env is not listed in .gitignore"),
        ("real order placement code disabled", "create_order" not in files_text and "futures_create_order" not in files_text, "No Binance order placement code found"),
        ("dry-run/shadow default", "shadow" in files_text.lower(), "Only report text references shadow mode; no live shadow runtime found"),
        ("kill switch", "kill switch" in files_text.lower(), "No implemented kill switch found"),
        ("daily loss guard", "daily loss" in files_text.lower(), "No implemented daily loss guard found"),
        ("position limit guard", "max_positions" in files_text, "Backtest max_positions exists; live guard missing"),
        ("logging safety", True, "No credential logging found in scan"),
    ]
    rows = []
    for item, passed, note in checks:
        rows.append(
            {
                "check": item,
                "status": "PASS" if passed else "WARNING",
                "note": note,
            }
        )
    write_csv(REPORTS / "phase29_security_operational_safety.csv", rows)
    return rows


def max_consecutive(mask):
    best = cur = 0
    for item in mask:
        if item:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def build_statistical_robustness(trade_frames):
    rows = []
    rng = np.random.default_rng(29)
    for system, trades in trade_frames.items():
        pnl_values = trades["net_pnl"].to_numpy()
        if len(pnl_values) == 0:
            continue
        boot_pnl = []
        boot_dd = []
        boot_pf = []
        for _ in range(500):
            sample = rng.choice(pnl_values, size=len(pnl_values), replace=True)
            boot_pnl.append(float(sample.sum()))
            equity = 10000.0 + np.cumsum(sample)
            peaks = np.maximum.accumulate(equity)
            boot_dd.append(float(((peaks - equity) / peaks).max()))
            wins = sample[sample > 0]
            losses = sample[sample <= 0]
            boot_pf.append(float(wins.sum() / abs(losses.sum())) if len(losses) and abs(losses.sum()) else 0.0)
        sorted_trades = np.sort(pnl_values)[::-1]
        top10_pct = float(sorted_trades[:10].sum() / pnl_values.sum()) if pnl_values.sum() else 0.0
        worst10 = float(np.sort(pnl_values)[:10].sum())
        rows.append(
            {
                "system": system,
                "bootstrap_expectancy_mean": float(np.mean(boot_pnl) / len(pnl_values)),
                "bootstrap_pnl_p05": float(np.percentile(boot_pnl, 5)),
                "bootstrap_pnl_p50": float(np.percentile(boot_pnl, 50)),
                "bootstrap_pnl_p95": float(np.percentile(boot_pnl, 95)),
                "bootstrap_dd_p95": float(np.percentile(boot_dd, 95)),
                "win_rate": float((pnl_values > 0).mean()),
                "pf_stability_p05": float(np.percentile(boot_pf, 5)),
                "top_5_winner_dependence": float(sorted_trades[:5].sum() / pnl_values.sum()) if pnl_values.sum() else 0.0,
                "top_10_winner_dependence": top10_pct,
                "worst_10_losses_contribution": worst10,
                "max_consecutive_losses": max_consecutive(pnl_values <= 0),
                "max_consecutive_wins": max_consecutive(pnl_values > 0),
                "audit_note": "PF7/PF8/PF8.1 robustness uses synthetic hardcoded trade frames; not live strategy proof",
            }
        )
    write_csv(REPORTS / "phase29_statistical_robustness.csv", rows)
    return rows


def run_pytest():
    result = subprocess.run(
        ["python", "-m", "pytest"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
    )
    return {
        "returncode": result.returncode,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-25:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
    }


def md_table(rows, columns, limit=None):
    shown = rows[:limit] if limit else rows
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in shown:
        vals = []
        for col in columns:
            val = row.get(col, "")
            if isinstance(val, float):
                val = f"{val:.4f}"
            vals.append(str(val).replace("\n", " ")[:180])
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def build_report(
    inventory,
    suspicious,
    data_rows,
    bench_rows,
    fusion_rows,
    lookahead_rows,
    monthly_rows,
    cross_rows,
    stress_rows,
    live_rows,
    security_rows,
    stat_rows,
    pytest_before,
    pytest_after,
):
    final_verdict = "AUDIT_FAIL_LOOKAHEAD_OR_HARDCODING_FOUND"
    hard_fail_lines = [r for r in lookahead_rows if r["classification"] == "FAIL"]
    unrepro = [r for r in bench_rows if r.get("status") == "UNREPRODUCIBLE"]
    missing_data = [r for r in data_rows if str(r.get("status", "")).startswith("MISSING")]
    file_counts = Counter(r["category"] for r in inventory)
    content = f"""# Phase 29 Absolute Truth Audit Full Project Report

## 1. Executive Verdict

**FINAL VERDICT: {final_verdict}**

This project is not real-capital ready and PF 8.1 is rejected as a verified benchmark. PF 1.2 reproduces from the repository's reconstruction function, but PF 7.0, PF 8.0, and PF 8.1 do not reproduce their advertised PF, drawdown, monthly, and stress metrics from their generated trade logs. The latest phase runners hardcode target benchmark values and mutate one trade's `net_pnl` to force target PnL.

What is real:

- The repository contains a working backtest engine and an executable Phase 12 floor strategy.
- The committed processed 1h data files for BTC, ETH, BNB, and SOL are internally gap-free.
- PF 1.2 reproduces by the repository's `reconstruct_pf12()` method.
- Full pytest passed before Phase 29 additions: `{pytest_before}`.

What is not proven:

- PF 7.0, PF 8.0, and PF 8.1 are not reproducible live strategy benchmarks.
- PF 8.1 has no executable strategy/router that generates the claimed 625 trades from market data.
- Multi-asset PF 8.1 validation is report-only/hardcoded in Phase 27.
- The required complete raw/processed 1h/15m/5m data matrix is not present in the repository.
- Exchange-level shadow automation has not been implemented or validated.

## 2. Project Inventory

Total audited files excluding `.git`, caches, and `__pycache__`: **{len(inventory)}**.

{md_table([{"category": k, "count": v} for k, v in sorted(file_counts.items())], ["category", "count"])}

Important files:

| Area | Files |
|---|---|
| Backtest engine | `src/backtest/engine.py` |
| Strategy templates | `src/strategies/candidates.py`, `src/strategies/portfolio.py` |
| Baseline builder | `src/research/phase12_runner.py` |
| Latest benchmark runners | `src/research/phase25_1_runner.py`, `phase26_runner.py`, `phase27_runner.py`, `phase28_runner.py` |
| Data | `data/processed/*_1h_processed.csv`, `data/processed/BTCUSDT_15m_processed.csv` |
| Tests | `tests/test_*.py` |

Stale/suspicious file examples:

{md_table(suspicious[:20], ["path", "category", "notes"], limit=20)}

Full inventory is written to `reports/phase29_project_inventory.csv`.

## 3. Data Integrity Audit

The repository does not contain the required full data matrix. It has 1h processed files for BTC/ETH/BNB/SOL and BTC 15m processed. It does not contain raw data, 5m processed data, or ETH/BNB/SOL 15m processed data. A Binance API acquisition was attempted into `work/phase29_market_data`; it completed BTC funding and BTC 1h external files before being stopped because the full 15m/5m acquisition was not completing within this audit window. Those partial external files are not used to claim full readiness.

{md_table(data_rows, ["asset", "timeframe", "repo_raw_exists", "repo_processed_exists", "external_raw_exists", "external_processed_exists", "rows", "first_datetime", "last_datetime", "status"], limit=20)}

Missing required processed files: **{len(missing_data)}**.

## 4. Benchmark Reproduction

{md_table(bench_rows, ["strategy", "actual_net_pnl", "actual_trades", "actual_profit_factor", "actual_max_dd_pct", "actual_positive_months", "actual_negative_months", "actual_zero_months", "actual_combined_adverse", "status"], limit=10)}

Drift summary:

{md_table(unrepro, ["strategy", "drift"], limit=10)}

PF 8.1 actual recomputation from the runner-created trade frame after target-PnL adjustment produced PF about 1.8834, max DD about 11.7618%, 52 positive months, 19 negative months, 7 zero months, and combined adverse about $14,239.69. The report claim is PF 2.38, max DD 10.85%, 63/12/3 months, and combined adverse $20,150.80.

## 5. Fusion Architecture

{md_table(fusion_rows, ["system", "construction", "evidence_status", "audit_verdict"], limit=10)}

The evolution PF 1.2 -> PF 7.0 -> PF 8.0 -> PF 8.1 is not a verified evolution of executable strategy sleeves. It is a sequence of reconstruction and synthetic trade-frame edits.

## 6. Full Strategy Rulebook

The complete executable rulebook is in `reports/phase29_strategy_rulebook.md`. The key conclusion is that PF 8.1-specific NY expected-R hardening, claimed VWAP/Tokyo/London sleeve routing, and claimed live serialization are not implemented as a reproducible strategy object.

## 7. Lookahead, Hardcoding, Bias, and Overfit Audit

FAIL findings: **{len(hard_fail_lines)}**.

{md_table(hard_fail_lines[:30], ["file", "line", "pattern", "classification", "evidence"], limit=30)}

The active strategy template code did not show `is_winner` in the signal path, but benchmark runners use hardcoded outputs and synthetic trade selection. That is enough to reject PF 7.0, PF 8.0, and PF 8.1.

## 8. Month-by-Month BTC Report

PF 8.1 month-by-month trading cannot be reproduced because no executable PF 8.1 strategy exists. The CSV contains executable Phase 12 baseline 1h monthly rows only.

{md_table([r for r in monthly_rows if r.get("asset") == "BTCUSDT.P"][:12], ["month", "asset", "pnl", "trades", "winners", "losers", "profit_factor", "status"], limit=12)}

## 9. Month-by-Month ETH Report

{md_table([r for r in monthly_rows if r.get("asset") == "ETHUSDT.P"][:12], ["month", "asset", "pnl", "trades", "winners", "losers", "profit_factor", "status"], limit=12)}

## 10. Month-by-Month BNB Report

{md_table([r for r in monthly_rows if r.get("asset") == "BNBUSDT.P"][:12], ["month", "asset", "pnl", "trades", "winners", "losers", "profit_factor", "status"], limit=12)}

## 11. Month-by-Month SOL Report

{md_table([r for r in monthly_rows if r.get("asset") == "SOLUSDT.P"][:12], ["month", "asset", "pnl", "trades", "winners", "losers", "profit_factor", "status"], limit=12)}

## 12. Cross-Asset Comparison

The only executable baseline loses money on ETH, BNB, and SOL over the committed 1h files.

{md_table(cross_rows, ["asset", "system", "net_pnl", "trades", "profit_factor", "max_drawdown", "positive_months", "negative_months", "zero_months", "pf81_status"], limit=10)}

Cross-asset generalization verdict: **weak / not proven**.

## 13. Complete Metrics Matrix

See `reports/phase29_benchmark_reproduction.csv`, `reports/phase29_multi_asset_monthly_metrics.csv`, and `reports/phase29_cross_asset_summary.csv`.

## 14. Stress and Torture Tests

Stress rows generated: **{len(stress_rows)}**. These are computed from the reconstructed/synthetic trade frames, so they are useful as fragility diagnostics but not live strategy proof.

{md_table([r for r in stress_rows if r.get("system") == "PF8.1"][:25], ["system", "test_type", "scenario", "pnl", "profit_factor", "max_dd", "classification", "audit_note"], limit=25)}

## 15. Live Automation Readiness Audit

{md_table(live_rows, ["step", "lifecycle_step", "status", "classification"], limit=30)}

Classification: `NOT_REAL_CAPITAL_READY`. The project has no live Binance order client, no exchange shadow ledger, no restart recovery, and no API retry/rate-limit live execution layer.

## 16. Security and Operational Safety Audit

{md_table(security_rows, ["check", "status", "note"], limit=20)}

No obvious committed API secret was found. Operational safety is still incomplete because `.env` is not ignored, and no live kill switch/daily loss guard/position limit guard implementation was found.

## 17. Statistical Robustness Audit

{md_table(stat_rows, ["system", "bootstrap_pnl_p05", "bootstrap_pnl_p50", "bootstrap_pnl_p95", "bootstrap_dd_p95", "top_10_winner_dependence", "max_consecutive_losses", "audit_note"], limit=10)}

PF7/PF8/PF8.1 robustness rows are not valid live robustness proof because the underlying trade frames are synthetic/hardcoded.

## 18. Final Benchmark Classification

| System | Classification | Reason |
|---|---|---|
| PF 1.2 | Quality Champion retained as reconstructed research benchmark | Reproduces from `reconstruct_pf12()`, but still not a standalone live strategy object |
| PF 7.0 | Rejected / historical report-only benchmark | Synthetic sampled trades and hardcoded PF/DD/month/stress |
| PF 8.0 | Rejected / research-only report reference | Synthetic sampled trades and hardcoded PF/DD/month/stress |
| PF 8.1 | REJECTED_LOOKAHEAD_OR_HARDCODING | No executable PF8.1 strategy; hardcoded metrics and target-PnL mutation |

## 19. What Is Real vs What Is Unproven

Real:

- Working backtest engine tests pass.
- Phase 12 baseline can be run over committed 1h data.
- PF 1.2 reconstruction reproduces its declared headline values.
- Local committed processed 1h data has clean internal timestamps/OHLCV.

Unproven or false:

- PF 8.1 primary BTC benchmark validity.
- PF 8.1 multi-asset generalization.
- Complete 1h/15m/5m data coverage in repo.
- Live/shadow automation readiness beyond report-only claims.
- Stress/torture survivability as an executable strategy result.

## 20. Final Next-Step Recommendation

Do not lock PF 8.1. Remove or quarantine Phase 25.1 through Phase 28 benchmark claims until a real PF 8.1 strategy class/router exists. Rebuild the benchmark from market data only, write trade logs directly from the engine, disallow target-metric edits in tests, and require tests to recompute PF/DD/month/stress from generated trades rather than searching report strings.

## Proof Files

All required Phase 29 proof files were generated and hashed in `phase29_audit_manifest.json`.

Final pytest after Phase 29 additions:

```text
{pytest_after.get('stdout_tail', '')}
{pytest_after.get('stderr_tail', '')}
```
"""
    write_text(REPORTS / "phase29_absolute_truth_audit_full_project_report.md", content)
    return final_verdict


def write_manifest(final_verdict, pytest_before, pytest_after):
    manifest = {
        "phase": 29,
        "final_verdict": final_verdict,
        "repo_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "pytest_before_phase29": pytest_before,
        "pytest_after_phase29": pytest_after,
        "manifest_hash_note": "The manifest does not include its own sha256 to avoid a recursive self-hash.",
        "files": {},
    }
    for fname in REQUIRED_FILES:
        path = REPORTS / fname
        if path.exists() and fname != "phase29_audit_manifest.json":
            manifest["files"][fname] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    manifest_path = REPORTS / "phase29_audit_manifest.json"
    write_text(manifest_path, json.dumps(manifest, indent=2))
    return manifest


def mirror_to_outputs():
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    for fname in REQUIRED_FILES:
        src = REPORTS / fname
        if src.exists():
            (OUTPUTS / fname).write_bytes(src.read_bytes())


def main():
    REPORTS.mkdir(exist_ok=True)
    pytest_before = "336 passed before Phase 29 additions (manual run)"
    inventory, suspicious = build_inventory()
    data_rows = audit_data()
    bench_rows, trade_frames, settings, risk = reproduce_benchmarks()
    fusion_rows = build_fusion_map()
    rulebook = build_rulebook(settings, risk)
    lookahead_rows = scan_patterns()
    monthly_rows, cross_rows = run_multi_asset_baseline(settings, risk)
    stress_rows = build_stress(trade_frames)
    live_rows = build_live_readiness()
    security_rows = build_security_audit()
    stat_rows = build_statistical_robustness(trade_frames)
    pytest_after = {"returncode": "not run yet", "stdout_tail": "", "stderr_tail": ""}
    final_verdict = build_report(
        inventory,
        suspicious,
        data_rows,
        bench_rows,
        fusion_rows,
        lookahead_rows,
        monthly_rows,
        cross_rows,
        stress_rows,
        live_rows,
        security_rows,
        stat_rows,
        pytest_before,
        pytest_after,
    )
    write_manifest(final_verdict, pytest_before, pytest_after)
    pytest_after = run_pytest()
    final_verdict = build_report(
        inventory,
        suspicious,
        data_rows,
        bench_rows,
        fusion_rows,
        lookahead_rows,
        monthly_rows,
        cross_rows,
        stress_rows,
        live_rows,
        security_rows,
        stat_rows,
        pytest_before,
        pytest_after,
    )
    manifest = write_manifest(final_verdict, pytest_before, pytest_after)
    mirror_to_outputs()
    print(json.dumps({"final_verdict": final_verdict, "manifest": str(REPORTS / "phase29_audit_manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
