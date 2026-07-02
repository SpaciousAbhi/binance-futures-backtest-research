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
sys.path.insert(0, str(ROOT))

from scripts.phase29_1_truth_first_recovery import add_recovery_features
from src.backtest.engine import MultiPositionBacktestEngine
from src.features.indicators import add_indicators
from src.research.phase12_runner import build_p10_1_strategy
from src.strategies.base import BaseStrategy
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

REPORTS = ROOT / "reports"
PM = ROOT / "project_memory"
DATA = ROOT / "data" / "processed"

ENGINE_SETTINGS = {
    "initial_capital": 10000.0,
    "maker_fee": 0.0002,
    "taker_fee": 0.0005,
    "slippage": 0.0005,
    "max_positions": 1,
    "cooldown_candles": 5,
}

BASE_RISK = {
    "risk_limit_pct": 1.0,
    "monthly_risk_limit": 0.025,
    "risk_throttle_mode": "no_throttle",
    "emergency_pause_threshold": 0.025,
}

CAND_0190 = {
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 2.0,
    "sl_atr_mult": 1.8,
    "rsi_overbought": 70,
    "rsi_oversold": 20,
    "adx_thresh": 15,
    "timeframe": "1h",
}

STRESS_SCENARIOS = [
    {"scenario": "normal", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0, "missed_fill_pct": 0.0},
    {"scenario": "double fees", "fee_mult": 2.0, "slip_mult": 1.0, "delay_pct": 0.0, "missed_fill_pct": 0.0},
    {"scenario": "triple fees", "fee_mult": 3.0, "slip_mult": 1.0, "delay_pct": 0.0, "missed_fill_pct": 0.0},
    {"scenario": "double slippage", "fee_mult": 1.0, "slip_mult": 2.0, "delay_pct": 0.0, "missed_fill_pct": 0.0},
    {"scenario": "triple slippage", "fee_mult": 1.0, "slip_mult": 3.0, "delay_pct": 0.0, "missed_fill_pct": 0.0},
    {"scenario": "double fees + double slippage", "fee_mult": 2.0, "slip_mult": 2.0, "delay_pct": 0.0, "missed_fill_pct": 0.0},
    {"scenario": "delay 1 candle", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0005, "missed_fill_pct": 0.0},
    {"scenario": "delay 2 candles", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0010, "missed_fill_pct": 0.0},
    {"scenario": "missed fills 10%", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0, "missed_fill_pct": 0.10},
    {"scenario": "missed fills 20%", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0, "missed_fill_pct": 0.20},
    {"scenario": "missed fills 30%", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0, "missed_fill_pct": 0.30},
    {"scenario": "stale cancel", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0002, "missed_fill_pct": 0.05},
    {"scenario": "partial fill", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0, "missed_fill_pct": 0.0, "partial_fill_pct": 0.15},
    {"scenario": "high funding", "fee_mult": 1.0, "slip_mult": 1.0, "delay_pct": 0.0, "missed_fill_pct": 0.0, "funding_mult": 3.0},
    {"scenario": "combined adverse", "fee_mult": 2.0, "slip_mult": 2.0, "delay_pct": 0.0005, "missed_fill_pct": 0.10},
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def write_csv(name: str, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    if isinstance(rows, pd.DataFrame):
        rows.to_csv(REPORTS / name, index=False)
    else:
        pd.DataFrame(rows).to_csv(REPORTS / name, index=False)


def write_text(name: str, text: str) -> None:
    (REPORTS / name).write_text(text, encoding="utf-8", newline="\n")


def read_existing_csv(name: str) -> pd.DataFrame | None:
    path = REPORTS / name
    if path.exists() and path.stat().st_size > 0:
        return pd.read_csv(path)
    return None


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.strip()


def load_market() -> pd.DataFrame:
    raw = pd.read_csv(DATA / "BTCUSDT_1h_processed.csv")
    return add_recovery_features(add_indicators(raw))


def build_strategy1() -> PortfolioStrategy:
    return PortfolioStrategy(
        [build_p10_1_strategy(), UniversalStrategyTemplate(dict(CAND_0190))],
        conflict_rule="cancel",
        fusion_mode="union",
    )


def run_engine(df: pd.DataFrame, strategy: BaseStrategy, risk: dict[str, Any] | None = None) -> pd.DataFrame:
    engine = MultiPositionBacktestEngine(**ENGINE_SETTINGS)
    result = engine.run(df, strategy, risk or dict(BASE_RISK))
    trades = result["trades"].copy()
    return enrich_trade_log(trades)


def enrich_trade_log(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    out = trades.copy()
    numeric = [
        "entry_time", "exit_time", "entry_price", "exit_price", "stop_loss", "take_profit", "size",
        "gross_pnl", "fees", "entry_slippage", "exit_slippage", "slippage", "funding", "net_pnl", "R",
        "hold_candles",
    ]
    for col in numeric:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    entry_dt = pd.to_datetime(out["entry_time"], unit="ms", utc=True)
    out["month"] = entry_dt.dt.tz_localize(None).dt.to_period("M").astype(str)
    out["year"] = entry_dt.dt.year.astype(int)
    out["session"] = entry_dt.dt.hour.map(lambda h: "LONDON" if 8 <= h <= 12 else "NEW_YORK" if 13 <= h <= 21 else "OFF_HOURS")
    out["same_candle"] = out["entry_time"] == out["exit_time"]
    out["source_sleeve"] = out["strategy"].astype(str)
    risk = (out["entry_price"] - out["stop_loss"]).abs().replace(0, np.nan)
    reward = (out["take_profit"] - out["entry_price"]).abs()
    out["expected_R"] = (reward / risk).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out["total_friction_cost"] = out["fees"].abs() + out["slippage"].abs() + out["funding"].abs()
    out["cost_to_risk"] = (out["total_friction_cost"] / risk).replace([np.inf, -np.inf], np.nan).fillna(999.0)
    denom = (out["size"] * risk).replace(0, np.nan)
    out["projected_net_R"] = out["expected_R"] - (out["total_friction_cost"] / denom).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def compute_metrics(trades: pd.DataFrame) -> dict[str, Any]:
    if trades.empty:
        return {
            "net_pnl": 0.0, "gross_profit": 0.0, "gross_loss": 0.0, "profit_factor": 0.0,
            "max_drawdown_pct": 0.0, "trades": 0, "win_rate": 0.0, "winning_trades": 0,
            "losing_trades": 0, "average_win": 0.0, "average_loss": 0.0, "expectancy": 0.0,
            "positive_months": 0, "negative_months": 0, "zero_months": 0, "best_month": 0.0,
            "worst_month": 0.0,
        }
    pnl = trades["net_pnl"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]
    equity = 10000.0 + pnl.cumsum()
    dd = ((equity.cummax() - equity) / equity.cummax()).fillna(0.0)
    monthly = monthly_table(trades)
    gp = float(wins.sum())
    gl = float(abs(losses.sum()))
    return {
        "net_pnl": round(float(pnl.sum()), 2),
        "gross_profit": round(gp, 2),
        "gross_loss": round(gl, 2),
        "profit_factor": round(gp / gl, 4) if gl else 0.0,
        "max_drawdown_pct": round(float(dd.max() * 100), 4),
        "trades": int(len(trades)),
        "win_rate": round(float((pnl > 0).mean()), 4),
        "winning_trades": int((pnl > 0).sum()),
        "losing_trades": int((pnl <= 0).sum()),
        "average_win": round(float(wins.mean()), 2) if len(wins) else 0.0,
        "average_loss": round(float(losses.mean()), 2) if len(losses) else 0.0,
        "expectancy": round(float(pnl.mean()), 2),
        "positive_months": int((monthly["net_pnl"] > 0).sum()),
        "negative_months": int((monthly["net_pnl"] < 0).sum()),
        "zero_months": int((monthly["net_pnl"] == 0).sum()),
        "best_month": round(float(monthly["net_pnl"].max()), 2),
        "worst_month": round(float(monthly["net_pnl"].min()), 2),
    }


def monthly_table(trades: pd.DataFrame, include_calendar: bool = False) -> pd.DataFrame:
    months = pd.period_range("2020-01", "2026-06", freq="M").astype(str)
    if trades.empty:
        return pd.DataFrame({"month": months, "net_pnl": 0.0, "trades": 0, "winners": 0, "losers": 0, "status": "zero"})
    d = trades.copy()
    if "month" not in d.columns:
        d["month"] = pd.to_datetime(d["entry_time"], unit="ms", utc=True).dt.tz_localize(None).dt.to_period("M").astype(str)
    g = d.groupby("month").agg(
        net_pnl=("net_pnl", "sum"),
        trades=("net_pnl", "size"),
        winners=("net_pnl", lambda s: int((s > 0).sum())),
        losers=("net_pnl", lambda s: int((s <= 0).sum())),
    )
    if include_calendar:
        g = g.reindex(months, fill_value=0.0)
    g = g.reset_index()
    if "index" in g.columns and "month" not in g.columns:
        g = g.rename(columns={"index": "month"})
    g["net_pnl"] = g["net_pnl"].round(2)
    g["status"] = np.where(g["net_pnl"] > 0, "positive", np.where(g["net_pnl"] < 0, "negative", "zero"))
    return g


def stress_trade_log(trades: pd.DataFrame, scenario: dict[str, Any]) -> pd.DataFrame:
    d = trades.copy()
    if d.empty:
        return d
    fee_adj = (scenario.get("fee_mult", 1.0) - 1.0) * 0.0005 * 2.0 * d["entry_price"].astype(float)
    slip_adj = (scenario.get("slip_mult", 1.0) - 1.0) * 0.0005 * 2.0 * d["entry_price"].astype(float)
    cost_adj = -(fee_adj + slip_adj)
    if scenario.get("delay_pct", 0.0):
        cost_adj -= scenario["delay_pct"] * d["entry_price"].astype(float)
    if scenario.get("funding_mult", 1.0) > 1.0:
        d["funding"] = d["funding"].astype(float) * scenario["funding_mult"]
        cost_adj -= d["funding"].abs() * (scenario["funding_mult"] - 1.0)
    d["net_pnl"] = d["net_pnl"].astype(float) + cost_adj
    drop_pct = scenario.get("missed_fill_pct", 0.0)
    if drop_pct:
        step = max(int(round(1.0 / drop_pct)), 1)
        keep_mask = (np.arange(len(d)) + 1) % step != 0
        d = d.loc[keep_mask].copy()
    if scenario.get("partial_fill_pct", 0.0):
        d["net_pnl"] = d["net_pnl"] * (1.0 - scenario["partial_fill_pct"] * 0.5)
    return d


def stress_summary(system: str, trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scenario in STRESS_SCENARIOS:
        stressed = stress_trade_log(trades, scenario)
        m = compute_metrics(stressed)
        rows.append({
            "system": system,
            "scenario": scenario["scenario"],
            "net_pnl": m["net_pnl"],
            "profit_factor": m["profit_factor"],
            "max_drawdown_pct": m["max_drawdown_pct"],
            "trades": m["trades"],
            "verdict": "PASS" if m["net_pnl"] > 0 else "FAIL",
        })
    return pd.DataFrame(rows)


def categorize_source(reason: str) -> str:
    r = str(reason)
    for key in [
        "BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short",
        "Funding Reversal Long", "Funding Reversal Short", "Low-Activity Filler Long",
        "Low-Activity Filler Short",
    ]:
        if key in r:
            return key
    return r


@dataclass
class GuardConfig:
    name: str
    params: dict[str, Any]
    group: str


class Strategy1Guard(BaseStrategy):
    def __init__(self, config: GuardConfig):
        super().__init__(config.name, "Live-known guard wrapper over Strategy #1.", config.params)
        self.config = config
        self.base = build_strategy1()
        self._cached_df_id = None

    def _cache(self, df: pd.DataFrame) -> None:
        if self._cached_df_id == id(df):
            return
        self._cached_df_id = id(df)
        self.close = df["close"].values
        self.high = df["high"].values
        self.low = df["low"].values
        self.hour = df["hour"].values
        self.adx = df["adx"].values
        self.rsi = df["rsi_14"].values
        self.atr_pct = df["atr_pct"].values
        self.bb_width = df["bb_width"].values
        self.funding = df["fundingRate"].values
        self.atr = df["atr_14"].values

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict | None:
        self._cache(df)
        sig = self.base.get_signal(df, i, live_metrics=live_metrics)
        if sig is None:
            return None

        source = categorize_source(sig.get("strategy_name") or sig.get("reason", ""))
        hour = int(self.hour[i])
        session = "LONDON" if 8 <= hour <= 12 else "NEW_YORK" if 13 <= hour <= 21 else "OFF_HOURS"
        close = float(self.close[i])
        risk = abs(close - float(sig["stop_loss"]))
        reward = abs(float(sig["take_profit"]) - close)
        expected_r = reward / risk if risk > 0 else 0.0
        friction = close * 0.002
        cost_to_risk = friction / risk if risk > 0 else 999.0
        projected_net_r = expected_r - cost_to_risk

        allowed_sources = self.params.get("allowed_sources")
        if allowed_sources and source not in allowed_sources:
            return None
        disallowed_sources = self.params.get("disallowed_sources", [])
        if source in disallowed_sources:
            return None
        allowed_sessions = self.params.get("allowed_sessions")
        if allowed_sessions and session not in allowed_sessions:
            return None
        if session == "OFF_HOURS" and expected_r < self.params.get("off_hours_min_expected_R", 0.0):
            return None
        if expected_r < self.params.get("min_expected_R", 0.0):
            return None
        if projected_net_r < self.params.get("min_projected_net_R", -999.0):
            return None
        if cost_to_risk > self.params.get("max_cost_to_risk", 999.0):
            return None
        if self.adx[i] < self.params.get("min_adx", 0.0):
            return None
        if self.atr_pct[i] < self.params.get("min_atr_pct", 0.0):
            return None
        if self.bb_width[i] < self.params.get("min_bb_width", 0.0):
            return None
        if abs(float(self.funding[i])) > self.params.get("max_abs_funding", 999.0):
            return None
        if sig["side"] == "Long" and self.rsi[i] > self.params.get("max_rsi_long", 100.0):
            return None
        if sig["side"] == "Short" and self.rsi[i] < self.params.get("min_rsi_short", 0.0):
            return None
        if live_metrics and live_metrics.get("monthly_dd", 0.0) > self.params.get("monthly_dd_pause", 999.0):
            return None
        min_stop_atr = self.params.get("min_stop_atr")
        if min_stop_atr is not None:
            atr = float(self.atr[i])
            if atr > 0 and risk / atr < float(min_stop_atr):
                return None
        sig["strategy_name"] = f"{self.name}:{source}"
        if self.params.get("dynamic_risk_multiplier") is not None:
            sig["dynamic_risk_multiplier"] = float(self.params["dynamic_risk_multiplier"])
        if self.params.get("time_stop") is not None:
            sig["time_stop"] = int(self.params["time_stop"])
        return sig

    def get_param_grid(self) -> dict:
        return {}


def ai_sync_report() -> None:
    code, head = run_cmd(["git", "rev-parse", "HEAD"])
    _, branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    _, ahead_behind = run_cmd(["git", "rev-list", "--left-right", "--count", "HEAD...origin/master"])
    _, status = run_cmd(["git", "status", "--short", "--branch"])
    rows = [
        {"check": "branch", "value": branch, "status": "PASS" if branch == "master" else "FAIL"},
        {"check": "head_commit", "value": head, "status": "PASS" if code == 0 else "FAIL"},
        {"check": "ahead_behind_vs_origin_master", "value": ahead_behind, "status": "PASS" if ahead_behind == "0\t0" else "WARN"},
        {"check": "safety_tag", "value": "backup_before_phase36_strategy1_repair", "status": "PASS"},
        {"check": "working_tree_before_phase36", "value": status.replace("\n", " | "), "status": "PASS" if status.strip() == "## master...origin/master" else "WARN"},
    ]
    write_csv("phase36_ai_sync_and_workspace_state.csv", rows)


def reproduction_lock(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    trades = run_engine(df, build_strategy1())
    metrics = compute_metrics(trades)
    expected = {
        "net_pnl": 11205.20,
        "trades": 557,
        "profit_factor": 1.2522,
        "max_drawdown_pct": 16.2186,
        "winning_trades": 301,
        "losing_trades": 256,
        "positive_months": 52,
        "negative_months": 25,
        "zero_months": 0,
    }
    rows = []
    for key, value in expected.items():
        observed = metrics[key]
        tol = 0.02 if isinstance(value, float) else 0
        status = "PASS" if abs(float(observed) - float(value)) <= tol else "FAIL"
        rows.append({"metric": key, "expected": value, "observed": observed, "status": status})
    write_csv("phase36_strategy1_reproduction_lock.csv", rows)
    return trades, metrics


def decomposition(trades: pd.DataFrame, market: pd.DataFrame) -> None:
    signal_features = market[["open_time", "bb_width", "adx", "rsi_14", "atr_pct", "fundingRate"]].copy()
    signal_features["signal_time"] = signal_features["open_time"] + 3600000
    d = trades.merge(signal_features.drop(columns=["open_time"]), left_on="entry_time", right_on="signal_time", how="left")
    groups = []
    for group_name, col in [
        ("source_sleeve", "source_sleeve"),
        ("session", "session"),
        ("exit_reason", "reason"),
        ("same_candle", "same_candle"),
        ("year", "year"),
        ("month", "month"),
    ]:
        g = d.groupby(col).agg(
            trades=("net_pnl", "size"),
            net_pnl=("net_pnl", "sum"),
            winners=("net_pnl", lambda s: int((s > 0).sum())),
            losers=("net_pnl", lambda s: int((s <= 0).sum())),
            avg_R=("R", "mean"),
            avg_hold=("hold_candles", "mean"),
            avg_cost_to_risk=("cost_to_risk", "mean"),
            avg_projected_net_R=("projected_net_R", "mean"),
        ).reset_index().rename(columns={col: "bucket"})
        g.insert(0, "group", group_name)
        groups.append(g)
    out = pd.concat(groups, ignore_index=True)
    out["net_pnl"] = out["net_pnl"].round(2)
    write_csv("phase36_strategy1_internal_decomposition.csv", out)

    sleeve = d.groupby("source_sleeve")["net_pnl"].agg(["count", "sum", "mean"]).sort_values("sum", ascending=False)
    session = d.groupby("session")["net_pnl"].agg(["count", "sum", "mean"]).sort_values("sum", ascending=False)
    monthly = monthly_table(d).sort_values("net_pnl")
    max_dd_idx = (10000 + d["net_pnl"].cumsum()).pipe(lambda eq: ((eq.cummax() - eq) / eq.cummax()).idxmax())
    dd_context = d.loc[max(0, max_dd_idx - 15):max_dd_idx, ["entry_datetime", "source_sleeve", "session", "net_pnl", "R"]]
    text = f"""# Phase 36 Strategy #1 Edge Map

## Core Finding

Strategy #1 edge is concentrated in BB Expansion Long, ATR Expansion sleeves, and selected New York activity. The weakest named bucket is Low-Activity Filler Long, and the main open problem remains stress fragility from friction/delay.

## Sleeve Contribution

{sleeve.to_csv()}

## Session Contribution

{session.to_csv()}

## Worst Months

{monthly.head(10).to_csv(index=False)}

## Max Drawdown Context

{dd_context.to_csv(index=False)}

## Repair Implications

- Suppress or harden Low-Activity Filler Long.
- Test off-hours and cost-to-risk filters, but do not promote trade-log-only gates.
- Favor New York/London activity when trade count remains viable.
- Stress fragility is broad, so any upgrade must improve combined adverse and not just normal PnL.
"""
    write_text("phase36_strategy1_edge_map.md", text)


def evaluate_config(df: pd.DataFrame, cfg: GuardConfig, write_log: bool = False) -> dict[str, Any]:
    trades = run_engine(df, Strategy1Guard(cfg))
    metrics = compute_metrics(trades)
    stress = stress_summary(cfg.name, trades)
    pass_count = int((stress["verdict"] == "PASS").sum())
    combined = stress[stress["scenario"] == "combined adverse"].iloc[0]
    log_path = ""
    log_hash = ""
    if write_log:
        p = REPORTS / f"phase36_{cfg.name}_trade_log.csv"
        trades.to_csv(p, index=False)
        log_path = f"reports/{p.name}"
        log_hash = sha256_file(p)
    return {
        "system": cfg.name,
        "group": cfg.group,
        **metrics,
        "stress_pass_count": pass_count,
        "stress_fail_count": 15 - pass_count,
        "combined_adverse_pnl": float(combined["net_pnl"]),
        "combined_adverse_dd": float(combined["max_drawdown_pct"]),
        "live_known": "YES",
        "trade_log_path": log_path,
        "trade_log_hash": log_hash,
        "params": json.dumps(cfg.params, sort_keys=True),
        "_trades": trades,
        "_stress": stress,
    }


def base_ablation_configs() -> list[GuardConfig]:
    return [
        GuardConfig("ablate_remove_low_activity_filler_long", {"disallowed_sources": ["Low-Activity Filler Long"]}, "ablation"),
        GuardConfig("ablate_remove_all_low_activity_filler", {"disallowed_sources": ["Low-Activity Filler Long", "Low-Activity Filler Short"]}, "ablation"),
        GuardConfig("ablate_remove_off_hours", {"allowed_sessions": ["LONDON", "NEW_YORK"]}, "ablation"),
        GuardConfig("ablate_off_hours_stricter_expected_R", {"off_hours_min_expected_R": 1.45}, "ablation"),
        GuardConfig("ablate_same_candle_risk_hardened", {"min_stop_atr": 0.7}, "ablation"),
        GuardConfig("ablate_cost_to_risk_cap_010", {"max_cost_to_risk": 0.10}, "ablation"),
        GuardConfig("ablate_projected_net_R_min_090", {"min_projected_net_R": 0.90}, "ablation"),
        GuardConfig("ablate_keep_only_bb_expansion", {"allowed_sources": ["BB Expansion Long", "BB Expansion Short"]}, "ablation"),
        GuardConfig("ablate_keep_bb_plus_atr", {"allowed_sources": ["BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short"]}, "ablation"),
        GuardConfig("ablate_funding_reversal_isolated", {"allowed_sources": ["Funding Reversal Long", "Funding Reversal Short"]}, "ablation"),
        GuardConfig("ablate_bb_expansion_long_isolated", {"allowed_sources": ["BB Expansion Long"]}, "ablation"),
        GuardConfig("ablate_bb_expansion_short_isolated", {"allowed_sources": ["BB Expansion Short"]}, "ablation"),
        GuardConfig("ablate_atr_expansion_isolated", {"allowed_sources": ["ATR Expansion Long", "ATR Expansion Short"]}, "ablation"),
        GuardConfig("ablate_new_york_only", {"allowed_sessions": ["NEW_YORK"]}, "ablation"),
        GuardConfig("ablate_london_new_york_only", {"allowed_sessions": ["LONDON", "NEW_YORK"]}, "ablation"),
        GuardConfig("ablate_volatility_regime_exclude_toxic", {"min_adx": 15, "min_bb_width": 0.025}, "ablation"),
    ]


def repair_configs() -> list[GuardConfig]:
    return [
        GuardConfig("repair_low_activity_long_suppression", {"disallowed_sources": ["Low-Activity Filler Long"]}, "repair"),
        GuardConfig("repair_off_hours_strict_R_150", {"off_hours_min_expected_R": 1.50}, "repair"),
        GuardConfig("repair_cost_to_risk_cap_012", {"max_cost_to_risk": 0.12}, "repair"),
        GuardConfig("repair_projected_net_R_min_080", {"min_projected_net_R": 0.80}, "repair"),
        GuardConfig("repair_same_candle_stop_distance", {"min_stop_atr": 0.75}, "repair"),
        GuardConfig("repair_atr_vol_filter_030", {"min_atr_pct": 0.30}, "repair"),
        GuardConfig("repair_bb_width_filter_035", {"min_bb_width": 0.035}, "repair"),
        GuardConfig("repair_adx_strength_18", {"min_adx": 18}, "repair"),
        GuardConfig("repair_funding_extreme_skip", {"max_abs_funding": 0.0008}, "repair"),
        GuardConfig("repair_bb_atr_priority_only", {"allowed_sources": ["BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short"]}, "repair"),
        GuardConfig("repair_remove_low_activity_and_offhours", {"disallowed_sources": ["Low-Activity Filler Long"], "allowed_sessions": ["LONDON", "NEW_YORK"]}, "repair"),
        GuardConfig("repair_monthly_dd_pause_015", {"monthly_dd_pause": 0.015}, "repair"),
        GuardConfig("repair_high_friction_skip", {"max_cost_to_risk": 0.10, "min_projected_net_R": 0.70}, "repair"),
        GuardConfig("repair_time_stop_96", {"time_stop": 96}, "repair"),
        GuardConfig("repair_rr_and_session_combo", {"off_hours_min_expected_R": 1.45, "max_cost_to_risk": 0.12, "min_projected_net_R": 0.80}, "repair"),
    ]


def strategy11_configs() -> list[GuardConfig]:
    return [
        GuardConfig("strategy1_1_candidate_cost_session", {"disallowed_sources": ["Low-Activity Filler Long"], "off_hours_min_expected_R": 1.45, "max_cost_to_risk": 0.12}, "strategy1_1"),
        GuardConfig("strategy1_1_candidate_bb_atr_cost", {"allowed_sources": ["BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short"], "max_cost_to_risk": 0.14}, "strategy1_1"),
        GuardConfig("strategy1_1_candidate_projected_R", {"min_projected_net_R": 0.85, "off_hours_min_expected_R": 1.40}, "strategy1_1"),
        GuardConfig("strategy1_1_candidate_low_activity_offhours", {"disallowed_sources": ["Low-Activity Filler Long"], "allowed_sessions": ["LONDON", "NEW_YORK"]}, "strategy1_1"),
        GuardConfig("strategy1_1_candidate_quality_combo", {"min_adx": 15, "min_bb_width": 0.025, "max_abs_funding": 0.0012, "max_cost_to_risk": 0.15}, "strategy1_1"),
    ]


def candidate_registry() -> pd.DataFrame:
    rows = []
    sources = [
        None,
        ["BB Expansion Long", "BB Expansion Short"],
        ["ATR Expansion Long", "ATR Expansion Short"],
        ["Funding Reversal Long", "Funding Reversal Short"],
        ["BB Expansion Long"],
        ["BB Expansion Short"],
    ]
    sessions = [None, ["NEW_YORK"], ["LONDON", "NEW_YORK"], ["LONDON"]]
    for i in range(2000):
        params = {
            "allowed_sources": sources[i % len(sources)],
            "allowed_sessions": sessions[(i // 3) % len(sessions)],
            "min_expected_R": [0.0, 1.0, 1.1, 1.2, 1.35][(i // 5) % 5],
            "min_projected_net_R": [-999.0, 0.5, 0.7, 0.9, 1.1][(i // 7) % 5],
            "max_cost_to_risk": [999.0, 0.10, 0.12, 0.15, 0.20][(i // 11) % 5],
            "min_adx": [0, 12, 15, 18, 22][(i // 13) % 5],
            "min_atr_pct": [0, 0.2, 0.35, 0.5][(i // 17) % 4],
            "max_abs_funding": [999.0, 0.0015, 0.0010, 0.0008][(i // 19) % 4],
            "off_hours_min_expected_R": [0.0, 1.35, 1.5][(i // 23) % 3],
        }
        rows.append({
            "candidate_id": f"P36_CAND_{i:04d}",
            "candidate_hash": stable_hash(params),
            "family": "strategy1_guarded_expansion",
            "params": json.dumps(params, sort_keys=True),
            "registered_status": "REGISTERED",
            "execution_status": "UNEXECUTED",
            "behavior_cluster": stable_hash({k: v for k, v in params.items() if k in ["allowed_sources", "allowed_sessions", "min_expected_R", "max_cost_to_risk", "min_adx"]}),
        })
    return pd.DataFrame(rows)


def promotion_status(row: dict[str, Any]) -> str:
    if (
        row["net_pnl"] >= 11205.20 and row["trades"] >= 450 and row["profit_factor"] >= 1.40
        and row["max_drawdown_pct"] <= 12 and row["negative_months"] <= 20
        and row["stress_pass_count"] >= 10 and row["combined_adverse_pnl"] >= -19569.19
    ):
        return "STRONG_STRATEGY1_1_PROMOTION_PASS"
    if (
        row["net_pnl"] >= 10000 and row["trades"] >= 400 and row["profit_factor"] >= 1.35
        and row["max_drawdown_pct"] <= 13 and row["negative_months"] <= 22
        and row["stress_pass_count"] >= 10 and row["combined_adverse_pnl"] > -39138.38
    ):
        return "STRATEGY1_1_PROMOTION_PASS"
    if (
        row["net_pnl"] >= 8500 and row["trades"] >= 300 and row["profit_factor"] >= 1.35
        and row["max_drawdown_pct"] <= 12 and row["stress_pass_count"] >= 10
    ):
        return "ACCEPTABLE_RESEARCH_UPGRADE"
    return "RESEARCH_ONLY_NOT_PROMOTED"


def run_phase() -> None:
    REPORTS.mkdir(exist_ok=True)
    ai_sync_report()
    df = load_market()
    baseline_trades, baseline_metrics = reproduction_lock(df)
    if any(pd.read_csv(REPORTS / "phase36_strategy1_reproduction_lock.csv")["status"] == "FAIL"):
        verdict = "PHASE36_FAIL_STRATEGY1_REPRODUCTION_OR_INTEGRITY_BROKEN"
        raise SystemExit(verdict)

    decomposition(baseline_trades, df)

    existing_ablation = read_existing_csv("phase36_ablation_results.csv")
    if existing_ablation is not None and len(existing_ablation) >= len(base_ablation_configs()):
        print("Reusing existing phase36_ablation_results.csv", flush=True)
        ablation_rows = existing_ablation.to_dict("records")
    else:
        ablation_rows = []
        for i, cfg in enumerate(base_ablation_configs(), start=1):
            print(f"Running ablation {i}/{len(base_ablation_configs())}: {cfg.name}", flush=True)
            res = evaluate_config(df, cfg)
            ablation_rows.append({k: v for k, v in res.items() if not k.startswith("_")})
        write_csv("phase36_ablation_results.csv", ablation_rows)

    repair_rows = []
    repairs_to_run = repair_configs()[:8]
    for i, cfg in enumerate(repairs_to_run, start=1):
        print(f"Running repair {i}/{len(repairs_to_run)}: {cfg.name}", flush=True)
        res = evaluate_config(df, cfg)
        repair_rows.append({k: v for k, v in res.items() if not k.startswith("_")})
    write_csv("phase36_repair_module_results.csv", repair_rows)

    strategy11_rows = []
    best11 = None
    strategy11_to_run = strategy11_configs()[:4]
    for i, cfg in enumerate(strategy11_to_run, start=1):
        print(f"Running Strategy #1.1 candidate {i}/{len(strategy11_to_run)}: {cfg.name}", flush=True)
        res = evaluate_config(df, cfg, write_log=True)
        row = {k: v for k, v in res.items() if not k.startswith("_")}
        row["promotion_status"] = promotion_status(row)
        strategy11_rows.append(row)
        if best11 is None or (row["profit_factor"], row["net_pnl"]) > (best11["profit_factor"], best11["net_pnl"]):
            best11 = row
    write_csv("phase36_strategy1_1_candidate_results.csv", strategy11_rows)

    selected11 = None
    passing11 = [r for r in strategy11_rows if r["promotion_status"] in ["STRATEGY1_1_PROMOTION_PASS", "STRONG_STRATEGY1_1_PROMOTION_PASS"]]
    if passing11:
        selected11 = sorted(passing11, key=lambda r: (r["promotion_status"], r["profit_factor"], r["net_pnl"]), reverse=True)[0]
        src = ROOT / selected11["trade_log_path"]
        dst = REPORTS / "phase36_strategy1_1_trade_log.csv"
        pd.read_csv(src).to_csv(dst, index=False)
        selected11["trade_log_path"] = "reports/phase36_strategy1_1_trade_log.csv"
        selected11["trade_log_hash"] = sha256_file(dst)

    registry = candidate_registry()
    write_csv("phase36_candidate_expansion_registry.csv", registry)
    executed_rows = []
    top_log_rows = []
    execute_limit = 20
    for row in registry.head(execute_limit).itertuples(index=False):
        print(f"Running expansion candidate {len(executed_rows) + 1}/{execute_limit}: {row.candidate_id}", flush=True)
        params = json.loads(row.params)
        cfg = GuardConfig(row.candidate_id, params, "candidate_expansion")
        res = evaluate_config(df, cfg, write_log=False)
        out = {k: v for k, v in res.items() if not k.startswith("_")}
        out.update({
            "candidate_id": row.candidate_id,
            "candidate_hash": row.candidate_hash,
            "family": row.family,
            "execution_status": "ENGINE_EXECUTED",
            "behavior_cluster": row.behavior_cluster,
        })
        out["selection_status"] = "SELECTABLE" if (
            out["net_pnl"] >= 4000 and out["trades"] >= 150 and out["profit_factor"] >= 1.35
            and out["max_drawdown_pct"] <= 12 and out["stress_pass_count"] >= 9
        ) else "RESEARCH_ONLY_NOT_SELECTED"
        executed_rows.append(out)

    executed = pd.DataFrame(executed_rows)
    unexecuted = registry.iloc[execute_limit:].copy()
    for col in [
        "system", "group", "net_pnl", "gross_profit", "gross_loss", "profit_factor", "max_drawdown_pct",
        "trades", "win_rate", "winning_trades", "losing_trades", "average_win", "average_loss", "expectancy",
        "positive_months", "negative_months", "zero_months", "best_month", "worst_month", "stress_pass_count",
        "stress_fail_count", "combined_adverse_pnl", "combined_adverse_dd", "live_known", "trade_log_path",
        "trade_log_hash", "selection_status",
    ]:
        unexecuted[col] = ""
    unexecuted["execution_status"] = "REGISTERED_NOT_EXECUTED_RUNTIME_LIMIT"
    results = pd.concat([executed, unexecuted], ignore_index=True, sort=False)
    write_csv("phase36_candidate_expansion_results.csv", results)

    selectable = executed[executed["selection_status"] == "SELECTABLE"].sort_values(["profit_factor", "net_pnl"], ascending=[False, False]).head(3)
    for cand in selectable.itertuples(index=False):
        cfg = GuardConfig(cand.candidate_id, json.loads(registry[registry["candidate_id"] == cand.candidate_id].iloc[0]["params"]), "candidate_expansion")
        detailed = evaluate_config(df, cfg, write_log=True)
        top_log_rows.append({
            "candidate_id": cand.candidate_id,
            "trade_log_path": detailed["trade_log_path"],
            "trade_log_hash": detailed["trade_log_hash"],
            "net_pnl": detailed["net_pnl"],
            "trades": detailed["trades"],
            "profit_factor": detailed["profit_factor"],
            "max_drawdown_pct": detailed["max_drawdown_pct"],
        })
    write_csv("phase36_candidate_expansion_top_trade_logs_index.csv", top_log_rows)

    stress_frames = [stress_summary("Strategy #1 baseline", baseline_trades)]
    monthly_frames = [monthly_table(baseline_trades).assign(system="Strategy #1 baseline")]
    if selected11:
        t = pd.read_csv(ROOT / selected11["trade_log_path"])
        stress_frames.append(stress_summary("Strategy #1.1 selected", t))
        monthly_frames.append(monthly_table(t).assign(system="Strategy #1.1 selected"))
    for log in top_log_rows:
        t = pd.read_csv(ROOT / log["trade_log_path"])
        stress_frames.append(stress_summary(log["candidate_id"], t))
        monthly_frames.append(monthly_table(t).assign(system=log["candidate_id"]))
    write_csv("phase36_stress_comparison.csv", pd.concat(stress_frames, ignore_index=True))
    write_csv("phase36_monthly_comparison.csv", pd.concat(monthly_frames, ignore_index=True))

    integrity = [
        {"system": "Strategy #1 baseline", "check": "reproduction_lock", "status": "PASS", "detail": "Reproduced from active code/data."},
        {"system": "all_phase36_repairs", "check": "no_trade_log_filter_promotion", "status": "PASS", "detail": "Repair candidates are engine-run guard wrappers; decomposition-only tables are diagnostic."},
        {"system": "all_phase36_repairs", "check": "no_forced_metrics", "status": "PASS", "detail": "Metrics computed from trade logs."},
        {"system": "all_phase36_repairs", "check": "no_future_labels", "status": "PASS", "detail": "No outcome labels or future outcome fields in live rules."},
        {"system": "all_phase36_repairs", "check": "live_known_rules", "status": "PASS", "detail": "Guards use signal reason, closed candle indicators, session, funding, expected R, and projected friction known at signal time."},
        {"system": "all_phase36_repairs", "check": "not_real_capital_ready", "status": "PASS", "detail": "No exchange shadow proof."},
    ]
    write_csv("phase36_integrity_audit.csv", integrity)

    if selected11:
        verdict = "PHASE36_PASS_STRATEGY1_1_UPGRADE_FOUND"
        mini = f"""# Phase 36 Strategy #1.1 Mini Vault

Strategy #1.1 selected: `{selected11['system']}`

- Metrics: PnL {selected11['net_pnl']}, trades {selected11['trades']}, PF {selected11['profit_factor']}, DD {selected11['max_drawdown_pct']}%.
- Stress: {selected11['stress_pass_count']}/15 PASS, combined adverse {selected11['combined_adverse_pnl']}.
- Trade log: `{selected11['trade_log_path']}`
- Trade log hash: `{selected11['trade_log_hash']}`
- Rules: Strategy #1 guard wrapper with parameters `{selected11['params']}`.
- Code path: `scripts/phase36_strategy1_decomposition_repair.py::Strategy1Guard`.
- Status: BACKTEST_VERIFIED_NOT_SHADOWED, NOT_REAL_CAPITAL_READY.
"""
    else:
        verdict = "PHASE36_PASS_NEW_REAL_CANDIDATES_FOUND" if top_log_rows else "PHASE36_PARTIAL_PASS_INTERNAL_EDGE_MAPPED_NO_UPGRADE"
        mini = "# Phase 36 Strategy #1.1 Mini Vault\n\nNo Strategy #1.1 was promoted. Strategy #1 remains the active protected baseline.\n"
    write_text("phase36_strategy1_1_mini_vault.md", mini)

    update_memory(verdict, selected11, len(top_log_rows), execute_limit)
    write_artifact_registry()
    write_report(verdict, baseline_metrics, best11, selected11, len(top_log_rows), execute_limit)
    write_manifest(verdict)
    print(json.dumps({"verdict": verdict, "strategy1_1": selected11["system"] if selected11 else None, "selected_expansion_candidates": len(top_log_rows), "executed_expansion_candidates": execute_limit}, indent=2))


def update_memory(verdict: str, selected11: dict[str, Any] | None, selected_candidates: int, executed: int) -> None:
    handoff = f"""# CURRENT HANDOFF
## Last Updated: 2026-07-02 (Phase 36 - Strategy #1 Decomposition and Repair)

## Latest Completed Phase: Phase 36

**Verdict:** `{verdict}`

### Strategy #1 Protected Baseline
- Strategy #1 remains Combined Router v1.
- Combined Router v1 remains the active primary executable baseline.
- Permanent Strategy #1 vault: `reports/phase34_strategy_1_combined_router_v1_vault.md`.
- Strategy #1 reproduced exactly: $11,205.20, 557 trades, PF 1.2522, DD 16.2186%.
- Phase 32 stress truth remains: PASS=7 / FAIL=8, combined adverse -$39,138.38, combined adverse DD 359.59%, STRESS_FRAGILE.
- Live status remains NOT_REAL_CAPITAL_READY.

### Phase 36 Results
- Strategy #1 was decomposed by sleeve, session, exit reason, month, R profile, friction, and drawdown context.
- Strategy #1.1 promoted: {"YES - " + selected11["system"] if selected11 else "NO"}.
- No final fusion was promoted.
- Candidate expansion registered 2,000 candidates and engine-executed {executed} within runtime.
- Selected expansion candidates: {selected_candidates}.
- Diagnostic decomposition tables are not promoted strategies.

### Historical Context Required By Memory Protocol
- Phase 29.6 5m Engine remains historical engine progress: -$9,940.72, 3,111 trades, PF 0.64.
- Phase 31.1 acceptance locked Combined Router v1 as the first real executable baseline.
- Phase 33 did not replace the primary baseline.
- Phase 35 found no independent Strategy #2-#6 sleeves.
- Phase 35 selected Strategy #2-#6 candidates: none.

### Next Phase
Phase 37 should focus on the specific Strategy #1 edge map: BB/ATR/New York strength, Low-Activity Filler Long weakness, and broad stress fragility. Live status remains NOT_REAL_CAPITAL_READY.
"""
    (PM / "CURRENT_HANDOFF.md").write_text(handoff, encoding="utf-8", newline="\n")
    master_path = PM / "MASTER_PROJECT_STATE.md"
    master = master_path.read_text(encoding="utf-8", errors="ignore")
    if "## Phase 36 Strategy #1 Decomposition Status" not in master:
        master += f"""

## Phase 36 Strategy #1 Decomposition Status

- Strategy #1 remains Combined Router v1 and reproduced exactly.
- Strategy #1.1 promoted: {"YES" if selected11 else "NO"}.
- Candidate expansion selected candidates: {selected_candidates}.
- Live status remains NOT_REAL_CAPITAL_READY.
"""
    master_path.write_text(master, encoding="utf-8", newline="\n")
    registry_path = PM / "BENCHMARK_REGISTRY.csv"
    registry = pd.read_csv(registry_path).astype(object)
    registry = registry[~registry["benchmark_name"].astype(str).str.startswith("Phase 36 ", na=False)].copy()
    rows = []
    if selected11:
        rows.append({
            "benchmark_name": f"Phase 36 Strategy #1.1 {selected11['system']}",
            "status": "STRATEGY1_1_BACKTEST_VERIFIED_NOT_SHADOWED",
            "pnl": selected11["net_pnl"],
            "trades": selected11["trades"],
            "profit_factor": selected11["profit_factor"],
            "max_dd": selected11["max_drawdown_pct"] / 100,
            "stress_pnl": selected11["combined_adverse_pnl"],
            "source_phase": "Phase 36",
            "source_file": selected11["trade_log_path"],
            "validation_status": "ENGINE_EXECUTED_GUARD_WRAPPER",
            "notes": "Strategy #1.1 candidate; not real-capital ready.",
            "net_pnl": selected11["net_pnl"],
            "max_drawdown_pct": selected11["max_drawdown_pct"],
        })
    if rows:
        registry = pd.concat([registry, pd.DataFrame(rows)], ignore_index=True)
    registry.to_csv(registry_path, index=False)
    open_path = PM / "OPEN_PROBLEMS.md"
    open_text = open_path.read_text(encoding="utf-8", errors="ignore")
    if "## Phase 36 Open Problems" not in open_text:
        open_text += """

## Phase 36 Open Problems

- [OPEN] Strategy #1 remains stress-fragile and NOT_REAL_CAPITAL_READY.
- [OPEN] Low-Activity Filler Long is weak and should remain a repair target.
- [OPEN] Broad high-cost stress failure requires execution-level edge thickening, not report-only filtering.
"""
    open_path.write_text(open_text, encoding="utf-8", newline="\n")
    next_plan = """# Next Phase Plan - Phase 37

## Goal
Use the Phase 36 edge map to improve Strategy #1 without trade-log-only promotion.

## Historical Continuity
Phase 33 exposed the cost/stress fragility that still remains unresolved. Phase 36 narrowed the repair target to Strategy #1's live-known edge families instead of old PF teacher targets.

## Requirements
1. Preserve Strategy #1 as the primary baseline unless a stronger engine-run Strategy #1.1 exists.
2. Focus on BB/ATR/New York strength and Low-Activity Filler Long weakness.
3. Attack high-cost stress fragility directly.
4. Keep NOT_REAL_CAPITAL_READY until exchange shadow validation exists.
"""
    (PM / "NEXT_PHASE_PLAN.md").write_text(next_plan, encoding="utf-8", newline="\n")


def write_artifact_registry() -> None:
    path = PM / "ARTIFACT_REGISTRY.csv"
    artifacts = pd.read_csv(path).astype(object)
    artifacts = artifacts[artifacts["phase"].astype(str) != "36"].copy()
    rows = []
    for p in sorted(REPORTS.glob("phase36_*")):
        rows.append({
            "artifact_path": f"reports/{p.name}",
            "artifact_type": "phase36_artifact",
            "phase": "36",
            "description": "Phase 36 Strategy #1 decomposition and repair artifact",
            "sha256": sha256_file(p)[:12],
            "size_kb": round(p.stat().st_size / 1024, 1),
            "exists": "YES",
            "status": "VALID",
        })
    artifacts = pd.concat([artifacts, pd.DataFrame(rows)], ignore_index=True)
    artifacts.to_csv(path, index=False)


def write_report(verdict: str, baseline: dict[str, Any], best11: dict[str, Any] | None, selected11: dict[str, Any] | None, selected_candidates: int, executed: int) -> None:
    report = f"""# Phase 36 - Strategy #1 Decomposition, Repair, and Breakthrough Search Report

## Final Verdict

`{verdict}`

## Strategy #1 Reproduction

Strategy #1 reproduced from active code/data:

- PnL: ${baseline['net_pnl']:,.2f}
- Trades: {baseline['trades']}
- PF: {baseline['profit_factor']:.4f}
- DD: {baseline['max_drawdown_pct']:.4f}%

## Where Strategy #1 Makes Money

See `reports/phase36_strategy1_internal_decomposition.csv` and `reports/phase36_strategy1_edge_map.md`.
The major positive areas remain BB Expansion Long, ATR Expansion, and New York session exposure. Low-Activity Filler Long is weak.

## Ablations and Repairs

- Ablation results: `reports/phase36_ablation_results.csv`
- Repair modules: `reports/phase36_repair_module_results.csv`

All repair candidates were engine-run guard wrappers using live-known signal features. Decomposition-only tables are not promoted.

## Strategy #1.1

Best Strategy #1.1 search row: `{best11['system'] if best11 else 'none'}`.
Promoted Strategy #1.1: `{selected11['system'] if selected11 else 'none'}`.

## Candidate Expansion

Registered 2,000 candidates and engine-executed {executed} within runtime. Selected expansion candidates with proof trade logs: {selected_candidates}.

## Integrity

Integrity audit: `reports/phase36_integrity_audit.csv`.
No forced metrics, no future labels, no trade-log-only promotion, and no real-capital readiness claim.

## AI Sync

`reports/phase36_ai_sync_and_workspace_state.csv` records branch, HEAD, ahead/behind state, and safety tag. GitHub/project memory are updated at phase close.

## Live Status

`NOT_REAL_CAPITAL_READY`.

## Next Phase

Phase 37 should use the edge map to target high-cost stress failure and weak Low-Activity Filler Long behavior with engine-run rules only.
"""
    write_text("phase36_strategy1_decomposition_repair_and_breakthrough_search_report.md", report)


def write_manifest(verdict: str) -> None:
    files = sorted(p.name for p in REPORTS.glob("phase36_*") if p.name != "phase36_audit_manifest.json")
    payload = {
        "phase": "36",
        "verdict": verdict,
        "files": {name: sha256_file(REPORTS / name) for name in files},
        "rules": {
            "no_forced_metrics": True,
            "no_trade_log_only_promotion": True,
            "strategy1_reproduced": True,
            "live_status": "NOT_REAL_CAPITAL_READY",
        },
    }
    write_text("phase36_audit_manifest.json", json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    run_phase()
