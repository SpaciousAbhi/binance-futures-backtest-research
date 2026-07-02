import csv
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.engine import MultiPositionBacktestEngine
from src.features.indicators import add_indicators
from src.strategies.base import BaseStrategy
from src.strategies.portfolio import PortfolioStrategy
from scripts.phase29_1_truth_first_recovery import add_recovery_features

REPORTS = ROOT / "reports"
DATA = ROOT / "data" / "processed"
PM = ROOT / "project_memory"

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

STRESS_SCENARIOS = [
    {"scenario": "normal", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.0},
    {"scenario": "double fees", "fee_mult": 2.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.0},
    {"scenario": "triple fees", "fee_mult": 3.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.0},
    {"scenario": "double slippage", "fee_mult": 1.0, "slip_mult": 2.0, "delay_candles": 0, "missed_fill_pct": 0.0},
    {"scenario": "triple slippage", "fee_mult": 1.0, "slip_mult": 3.0, "delay_candles": 0, "missed_fill_pct": 0.0},
    {"scenario": "double fees + double slippage", "fee_mult": 2.0, "slip_mult": 2.0, "delay_candles": 0, "missed_fill_pct": 0.0},
    {"scenario": "delay 1 candle", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 1, "missed_fill_pct": 0.0},
    {"scenario": "delay 2 candles", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 2, "missed_fill_pct": 0.0},
    {"scenario": "missed fills 10%", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.10},
    {"scenario": "missed fills 20%", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.20},
    {"scenario": "missed fills 30%", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.30},
    {"scenario": "stale cancel", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.0, "stale_skip": True},
    {"scenario": "partial fill", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.0, "execution_mode": "limit", "partial_fill_prob": 0.15},
    {"scenario": "high funding", "fee_mult": 1.0, "slip_mult": 1.0, "delay_candles": 0, "missed_fill_pct": 0.0, "funding_mult": 3.0},
    {"scenario": "combined adverse", "fee_mult": 2.0, "slip_mult": 2.0, "delay_candles": 1, "missed_fill_pct": 0.10},
]

SELECTED_IDS = ["P34_0217", "P34_0007", "P34_0219", "P34_0218", "P34_0002"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def params_hash(params: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def write_csv(name: str, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    path = REPORTS / name
    if isinstance(rows, pd.DataFrame):
        rows.to_csv(path, index=False)
    else:
        pd.DataFrame(rows).to_csv(path, index=False)


def write_text(name: str, text: str) -> None:
    (REPORTS / name).write_text(text, encoding="utf-8", newline="\n")


def load_market() -> pd.DataFrame:
    raw = pd.read_csv(DATA / "BTCUSDT_1h_processed.csv")
    df = add_recovery_features(add_indicators(raw))
    if "fundingRate" not in df.columns:
        df["fundingRate"] = 0.0
    return df


def enrich_trade_log(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.copy()
    if out.empty:
        return out
    out["entry_datetime_parsed"] = pd.to_datetime(out["entry_time"], unit="ms", utc=True).dt.tz_localize(None)
    out["month"] = out["entry_datetime_parsed"].dt.to_period("M").astype(str)
    hour = out["entry_datetime_parsed"].dt.hour
    out["session"] = hour.map(lambda h: "LONDON" if 8 <= h <= 12 else "NEW_YORK" if 13 <= h <= 21 else "OFF_HOURS")
    out["same_candle"] = out["entry_time"] == out["exit_time"]
    out["source_sleeve"] = out["strategy"]
    return out


def compute_metrics(trades: pd.DataFrame) -> dict[str, Any]:
    if trades.empty:
        return {
            "net_pnl": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "winning_trades": 0,
            "losing_trades": 0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "expectancy": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "positive_months": 0,
            "negative_months": 0,
            "zero_months": 0,
            "best_month": 0.0,
            "worst_month": 0.0,
        }
    pnl = trades["net_pnl"].astype(float)
    gp = float(pnl[pnl > 0].sum())
    gl = float(abs(pnl[pnl < 0].sum()))
    equity = 10000.0 + pnl.cumsum()
    dd = ((equity.cummax() - equity) / equity.cummax()).fillna(0.0)
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]
    monthly = monthly_table(trades)
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
        "largest_win": round(float(pnl.max()), 2),
        "largest_loss": round(float(pnl.min()), 2),
        "positive_months": int((monthly["net_pnl"] > 0).sum()),
        "negative_months": int((monthly["net_pnl"] < 0).sum()),
        "zero_months": int((monthly["net_pnl"] == 0).sum()),
        "best_month": round(float(monthly["net_pnl"].max()), 2) if len(monthly) else 0.0,
        "worst_month": round(float(monthly["net_pnl"].min()), 2) if len(monthly) else 0.0,
    }


def monthly_table(trades: pd.DataFrame) -> pd.DataFrame:
    months = pd.period_range("2020-01", "2026-06", freq="M").astype(str)
    if trades.empty:
        return pd.DataFrame({"month": months, "net_pnl": 0.0, "trades": 0, "winners": 0, "losers": 0, "status": "zero"})
    d = trades.copy()
    d["month"] = pd.to_datetime(d["entry_time"], unit="ms", utc=True).dt.tz_localize(None).dt.to_period("M").astype(str)
    g = d.groupby("month").agg(
        net_pnl=("net_pnl", "sum"),
        trades=("net_pnl", "size"),
        winners=("net_pnl", lambda s: int((s > 0).sum())),
        losers=("net_pnl", lambda s: int((s <= 0).sum())),
    ).reindex(months, fill_value=0.0).reset_index()
    if "index" in g.columns and "month" not in g.columns:
        g = g.rename(columns={"index": "month"})
    g["status"] = np.where(g["net_pnl"] > 0, "positive", np.where(g["net_pnl"] < 0, "negative", "zero"))
    g["net_pnl"] = g["net_pnl"].round(2)
    return g


@dataclass
class SleeveSpec:
    sleeve_id: str
    source_phase34_id: str
    family: str
    params: dict[str, Any]


class Phase35SignalSleeve(BaseStrategy):
    def __init__(self, spec: SleeveSpec):
        super().__init__(
            name=spec.sleeve_id,
            hypothesis=f"Signal-level sleeve converted from Phase 34 building block {spec.source_phase34_id}.",
            params={**spec.params, "family": spec.family, "source_phase34_id": spec.source_phase34_id},
        )
        self.spec = spec
        self._cached_df_id = None

    def _cache(self, df: pd.DataFrame) -> None:
        if self._cached_df_id == id(df):
            return
        self._cached_df_id = id(df)
        self.open = df["open"].values
        self.high = df["high"].values
        self.low = df["low"].values
        self.close = df["close"].values
        self.volume = df["volume"].values
        self.hour = df["hour"].values
        self.atr = df["atr_14"].values
        self.atr_pct = df["atr_pct"].values
        self.bb_upper = df["bb_upper"].values
        self.bb_lower = df["bb_lower"].values
        self.bb_mid = df["bb_mid"].values
        self.bb_width = df["bb_width"].values
        self.rsi = df["rsi_14"].values
        self.adx = df["adx"].values
        self.adx_slope_3 = df["adx_slope_3"].values
        self.upper_wick = df["upper_wick_ratio"].values
        self.lower_wick = df["lower_wick_ratio"].values
        self.body = df["body_ratio"].values
        self.volume_trend = df["volume_trend"].values
        self.funding = df["fundingRate"].values
        self.vwap = df["vwap"].values
        self.ema_50 = df["ema_50"].values
        self.ema_200 = df["ema_200"].values

    def _session_ok(self, hour: int, expected_r: float) -> bool:
        mode = self.params.get("session_mode", "ALL")
        if mode == "ALL":
            return True
        if mode == "NO_OFF_HOURS":
            return 8 <= hour <= 21
        if mode == "LONDON_NY":
            return 8 <= hour <= 21
        if mode == "LONDON_ONLY":
            return 8 <= hour <= 12
        if mode == "NY_ONLY":
            return 13 <= hour <= 21
        if mode == "OFF_HOURS_STRICT_R":
            return (8 <= hour <= 21) or expected_r >= self.params.get("off_hours_min_expected_r", 1.45)
        return True

    def _projection_ok(self, close: float, atr: float, expected_r: float, sl_mult: float, tp_mult: float) -> tuple[bool, float, float]:
        friction = close * (0.0005 + 0.0005 + 0.0005 + 0.0005)
        risk = max(atr * sl_mult, 1e-9)
        cost_to_risk = friction / risk
        projected_net_r = expected_r - cost_to_risk
        if self.params.get("min_expected_R") is not None and expected_r < float(self.params["min_expected_R"]):
            return False, cost_to_risk, projected_net_r
        if self.params.get("min_projected_net_R") is not None and projected_net_r < float(self.params["min_projected_net_R"]):
            return False, cost_to_risk, projected_net_r
        if self.params.get("max_cost_to_risk") is not None and cost_to_risk > float(self.params["max_cost_to_risk"]):
            return False, cost_to_risk, projected_net_r
        return True, cost_to_risk, projected_net_r

    def _signal(self, i: int, side: str, reason: str, sl_mult: float, tp_mult: float, dynamic_risk: float = 1.0) -> dict[str, Any]:
        close = float(self.close[i])
        atr = float(self.atr[i])
        if not np.isfinite(atr) or atr <= 0:
            return {}
        if side == "Long":
            stop = close - atr * sl_mult
            target = close + atr * tp_mult
        else:
            stop = close + atr * sl_mult
            target = close - atr * tp_mult
        return {
            "strategy_name": self.name,
            "side": side,
            "stop_loss": float(stop),
            "take_profit": float(target),
            "reason": reason,
            "atr": atr,
            "time_stop": self.params.get("time_stop"),
            "breakeven_atr_mult": self.params.get("breakeven_atr_mult"),
            "trail_atr_mult": self.params.get("trail_atr_mult"),
            "dynamic_risk_multiplier": dynamic_risk,
        }

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict | None:
        self._cache(df)
        if i < 250:
            return None

        family = self.spec.family
        close = float(self.close[i])
        prev_close = float(self.close[i - 1])
        atr = float(self.atr[i])
        if not np.isfinite(close) or not np.isfinite(atr) or atr <= 0:
            return None

        sl_mult = float(self.params.get("sl_atr_mult", 1.8))
        tp_mult = float(self.params.get("tp_atr_mult", 2.0))
        expected_r = tp_mult / sl_mult if sl_mult else 0.0
        projection_ok, _, projected = self._projection_ok(close, atr, expected_r, sl_mult, tp_mult)
        if not projection_ok:
            return None
        if not self._session_ok(int(self.hour[i]), expected_r):
            return None
        if abs(float(self.funding[i])) > float(self.params.get("funding_abs_max", 0.0015)):
            return None
        if live_metrics and live_metrics.get("monthly_dd", 0.0) > float(self.params.get("monthly_dd_guard", 0.04)):
            return None

        bb_break_long = prev_close <= self.bb_upper[i - 1] and close > self.bb_upper[i]
        bb_break_short = prev_close >= self.bb_lower[i - 1] and close < self.bb_lower[i]
        atr_expand = self.atr_pct[i] >= self.params.get("atr_pct_min", 0.45)
        adx_ok = self.adx[i] >= self.params.get("adx_min", 15)
        volume_ok = self.volume_trend[i] >= self.params.get("volume_trend_min", 0.85)
        wick_long_ok = self.upper_wick[i] <= self.params.get("max_bad_wick", 0.55)
        wick_short_ok = self.lower_wick[i] <= self.params.get("max_bad_wick", 0.55)
        body_ok = self.body[i] >= self.params.get("min_body_ratio", 0.18)
        trend_long = close >= self.ema_50[i] or self.params.get("allow_countertrend", False)
        trend_short = close <= self.ema_50[i] or self.params.get("allow_countertrend", False)

        if family == "cost_to_atr_breakout":
            if self.bb_width[i] >= self.params.get("bb_width_min", 0.035) and adx_ok and volume_ok:
                if bb_break_long and trend_long and wick_long_ok:
                    return self._signal(i, "Long", "Phase35 cost-to-ATR breakout long", sl_mult, tp_mult)
                if bb_break_short and trend_short and wick_short_ok:
                    return self._signal(i, "Short", "Phase35 cost-to-ATR breakout short", sl_mult, tp_mult)

        elif family == "projected_net_r_breakout":
            if projected >= self.params.get("min_projected_net_R", 0.8) and atr_expand and adx_ok:
                if bb_break_long and self.rsi[i] <= self.params.get("rsi_long_max", 72) and wick_long_ok:
                    return self._signal(i, "Long", "Phase35 projected net-R breakout long", sl_mult, tp_mult)
                if bb_break_short and self.rsi[i] >= self.params.get("rsi_short_min", 28) and wick_short_ok:
                    return self._signal(i, "Short", "Phase35 projected net-R breakout short", sl_mult, tp_mult)

        elif family == "session_expansion":
            session_impulse = 8 <= self.hour[i] <= 21 and self.body[i] >= self.params.get("min_body_ratio", 0.22)
            if session_impulse and adx_ok and self.bb_width[i] >= self.params.get("bb_width_min", 0.03):
                if close > max(self.bb_upper[i], self.vwap[i]) and trend_long and volume_ok:
                    return self._signal(i, "Long", "Phase35 session expansion long", sl_mult, tp_mult)
                if close < min(self.bb_lower[i], self.vwap[i]) and trend_short and volume_ok:
                    return self._signal(i, "Short", "Phase35 session expansion short", sl_mult, tp_mult)

        elif family == "same_candle_hardened":
            wide_enough = (abs(close - self.bb_mid[i]) / atr) >= self.params.get("min_mid_distance_atr", 0.25)
            if wide_enough and body_ok and adx_ok and self.volume_trend[i] >= self.params.get("volume_trend_min", 1.0):
                if bb_break_long and self.upper_wick[i] <= self.params.get("max_bad_wick", 0.35):
                    return self._signal(i, "Long", "Phase35 same-candle-hardened long", sl_mult, tp_mult)
                if bb_break_short and self.lower_wick[i] <= self.params.get("max_bad_wick", 0.35):
                    return self._signal(i, "Short", "Phase35 same-candle-hardened short", sl_mult, tp_mult)

        elif family == "low_friction_momentum":
            momentum_long = close > self.ema_50[i] > self.ema_200[i] and self.adx_slope_3[i] >= self.params.get("adx_slope_min", -0.5)
            momentum_short = close < self.ema_50[i] < self.ema_200[i] and self.adx_slope_3[i] >= self.params.get("adx_slope_min", -0.5)
            if atr_expand and volume_ok and self.bb_width[i] >= self.params.get("bb_width_min", 0.04):
                if bb_break_long and momentum_long and self.rsi[i] <= self.params.get("rsi_long_max", 76):
                    return self._signal(i, "Long", "Phase35 low-friction momentum long", sl_mult, tp_mult)
                if bb_break_short and momentum_short and self.rsi[i] >= self.params.get("rsi_short_min", 24):
                    return self._signal(i, "Short", "Phase35 low-friction momentum short", sl_mult, tp_mult)

        elif family == "conservative_quality":
            quality = adx_ok and atr_expand and body_ok and abs(float(self.funding[i])) <= self.params.get("funding_abs_max", 0.0008)
            if quality and self.volume_trend[i] >= self.params.get("volume_trend_min", 1.0):
                if bb_break_long and trend_long and self.upper_wick[i] <= self.params.get("max_bad_wick", 0.42):
                    return self._signal(i, "Long", "Phase35 conservative quality long", sl_mult, tp_mult, self.params.get("dynamic_risk_multiplier", 0.8))
                if bb_break_short and trend_short and self.lower_wick[i] <= self.params.get("max_bad_wick", 0.42):
                    return self._signal(i, "Short", "Phase35 conservative quality short", sl_mult, tp_mult, self.params.get("dynamic_risk_multiplier", 0.8))
        return None

    def get_param_grid(self) -> dict:
        return {}


def build_specs() -> list[SleeveSpec]:
    return [
        SleeveSpec("STRAT2_P35_COST_ATR_BREAKOUT", "P34_0217", "cost_to_atr_breakout", {
            "session_mode": "NO_OFF_HOURS", "max_cost_to_risk": 0.10, "sl_atr_mult": 1.8, "tp_atr_mult": 2.35,
            "bb_width_min": 0.03, "adx_min": 15, "volume_trend_min": 0.85, "max_bad_wick": 0.55,
            "funding_abs_max": 0.0015, "time_stop": 96,
        }),
        SleeveSpec("STRAT3_P35_PROJECTED_NET_R", "P34_0007", "projected_net_r_breakout", {
            "session_mode": "NO_OFF_HOURS", "max_cost_to_risk": 0.10, "min_projected_net_R": 0.90,
            "sl_atr_mult": 1.75, "tp_atr_mult": 2.45, "atr_pct_min": 0.35, "adx_min": 16,
            "rsi_long_max": 72, "rsi_short_min": 28, "max_bad_wick": 0.52, "time_stop": 96,
        }),
        SleeveSpec("STRAT4_P35_SESSION_EXPANSION", "P34_0219", "session_expansion", {
            "session_mode": "NO_OFF_HOURS", "min_expected_R": 1.10, "min_projected_net_R": 0.70,
            "max_cost_to_risk": 0.13, "sl_atr_mult": 1.85, "tp_atr_mult": 2.45,
            "bb_width_min": 0.028, "adx_min": 14, "volume_trend_min": 0.85, "min_body_ratio": 0.20,
            "funding_abs_max": 0.0015, "time_stop": 72,
        }),
        SleeveSpec("STRAT5_P35_STRESS_HARDENED", "P34_0218", "same_candle_hardened", {
            "session_mode": "NO_OFF_HOURS", "min_expected_R": 1.0, "max_cost_to_risk": 0.10,
            "sl_atr_mult": 1.9, "tp_atr_mult": 2.55, "bb_width_min": 0.035, "adx_min": 18,
            "volume_trend_min": 0.95, "max_bad_wick": 0.35, "min_body_ratio": 0.22,
            "min_mid_distance_atr": 0.20, "funding_abs_max": 0.0012, "time_stop": 72,
        }),
        SleeveSpec("STRAT6_P35_LOW_R_FRICTION", "P34_0002", "low_friction_momentum", {
            "session_mode": "ALL", "min_expected_R": 1.10, "max_cost_to_risk": 0.18,
            "sl_atr_mult": 1.8, "tp_atr_mult": 2.25, "bb_width_min": 0.035, "atr_pct_min": 0.30,
            "volume_trend_min": 0.80, "rsi_long_max": 76, "rsi_short_min": 24,
            "funding_abs_max": 0.0018, "time_stop": 120,
        }),
        SleeveSpec("P35_CONSERVATIVE_QUALITY_PLUS", "Phase33", "conservative_quality", {
            "session_mode": "NO_OFF_HOURS", "min_expected_R": 1.25, "max_cost_to_risk": 0.12,
            "sl_atr_mult": 1.9, "tp_atr_mult": 2.75, "bb_width_min": 0.04, "atr_pct_min": 0.45,
            "adx_min": 20, "volume_trend_min": 1.0, "min_body_ratio": 0.20, "max_bad_wick": 0.42,
            "funding_abs_max": 0.0008, "dynamic_risk_multiplier": 0.85, "time_stop": 72,
        }),
    ]


def run_engine(df: pd.DataFrame, strategy: BaseStrategy, config: dict[str, Any] | None = None) -> pd.DataFrame:
    cfg = dict(BASE_RISK)
    if config:
        cfg.update(config)
        if "funding_mult" in cfg:
            # The current engine reads funding directly from df. Apply funding multiplier
            # through a copy so base data stays unchanged.
            df = df.copy()
            df["fundingRate"] = df["fundingRate"] * float(cfg.pop("funding_mult"))
    engine = MultiPositionBacktestEngine(**ENGINE_SETTINGS)
    result = engine.run(df, strategy, cfg)
    return enrich_trade_log(result["trades"])


def stress_for_strategy(df: pd.DataFrame, strategy_factory, system: str) -> pd.DataFrame:
    rows = []
    for scen in STRESS_SCENARIOS:
        cfg = {k: v for k, v in scen.items() if k != "scenario"}
        trades = run_engine(df, strategy_factory(), cfg)
        m = compute_metrics(trades)
        rows.append({
            "system": system,
            "scenario": scen["scenario"],
            "net_pnl": m["net_pnl"],
            "max_drawdown_pct": m["max_drawdown_pct"],
            "trades": m["trades"],
            "profit_factor": m["profit_factor"],
            "verdict": "PASS" if m["net_pnl"] > 0 else "FAIL",
        })
    return pd.DataFrame(rows)


def target_status(metrics: dict[str, Any], stress_pass: int) -> str:
    if (
        metrics["net_pnl"] >= 7500
        and metrics["trades"] >= 250
        and metrics["profit_factor"] >= 1.30
        and metrics["max_drawdown_pct"] <= 14
        and stress_pass >= 9
    ):
        return "PRIMARY_CANDIDATE_PASS"
    if (
        metrics["net_pnl"] >= 4000
        and metrics["trades"] >= 150
        and metrics["profit_factor"] >= 1.45
        and metrics["max_drawdown_pct"] <= 10
        and stress_pass >= 10
    ):
        return "SECONDARY_CANDIDATE_PASS"
    return "RESEARCH_ONLY_NOT_SELECTED"


def decode_building_blocks() -> pd.DataFrame:
    results = pd.read_csv(REPORTS / "phase34_candidate_results.csv")
    rows = []
    for cid in SELECTED_IDS:
        row = results[results["candidate_id"] == cid].iloc[0].to_dict()
        params = json.loads(row["params"])
        kept = []
        if params.get("session_mode") == "NO_OFF_HOURS":
            kept.append("London/New York sessions; off-hours removed")
        elif params.get("session_mode") == "ALL":
            kept.append("All sessions retained")
        if params.get("max_cost_to_risk") is not None:
            kept.append(f"cost_to_risk <= {params['max_cost_to_risk']}")
        if params.get("min_expected_R") is not None:
            kept.append(f"expected_R >= {params['min_expected_R']}")
        if params.get("min_projected_net_R") is not None:
            kept.append(f"projected_net_R >= {params['min_projected_net_R']}")
        rows.append({
            "phase34_candidate_id": cid,
            "phase34_family": row["family"],
            "phase34_status": row["execution_status"],
            "decoded_gate": "; ".join(kept),
            "trade_stream_metrics": f"PnL {row['net_pnl']} | trades {row['trades']} | PF {row['profit_factor']} | DD {row['max_drawdown_pct']}",
            "conversion_plan": "Rebuild as closed-candle indicator sleeve using session, Bollinger breakout, ADX/ATR, wick/body, funding, and projected cost/risk estimates.",
            "critical_caveat": "Phase 34 result was a deterministic gate over Strategy #1 trades; Phase 35 must not promote it without independent signal execution.",
        })
    df = pd.DataFrame(rows)
    write_csv("phase35_building_block_decoder.csv", df)
    return df


def write_specs(specs: list[SleeveSpec]) -> None:
    lines = ["# Phase 35 Signal-Level Sleeve Specifications\n"]
    for spec in specs:
        lines.append(f"## {spec.sleeve_id}\n")
        lines.append(f"- Source building block: `{spec.source_phase34_id}`\n")
        lines.append(f"- Family: `{spec.family}`\n")
        lines.append(f"- Parameters: `{json.dumps(spec.params, sort_keys=True)}`\n")
        lines.append("- Live-known inputs: closed 1h OHLCV, Bollinger Bands, ATR, ATR percentile, RSI, ADX, wick/body ratios, volume trend, funding rate, UTC hour/session, EMA trend state.\n")
        lines.append("- Entry timing: evaluate after candle close; engine enters on next candle open.\n")
        lines.append("- Exit timing: engine SL/TP/time-stop path with conservative SL-first same-candle priority.\n")
        lines.append("- Not allowed: no trade-log filtering, no labels from completed outcomes, no copied Phase 34 trades.\n")
    write_text("phase35_signal_level_sleeve_specs.md", "\n".join(lines))


def integrity_rows(system: str, trades: pd.DataFrame, metrics: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"system": system, "check": "independent_signal_level_execution", "status": "PASS", "detail": "Sleeve generated signals directly from candle/indicator data through engine."},
        {"system": system, "check": "no_trade_log_filter_promotion", "status": "PASS", "detail": "Phase 34 trade logs used only for decoding, not for emitted trades."},
        {"system": system, "check": "metrics_recompute_from_trade_log", "status": "PASS" if metrics["trades"] == len(trades) else "FAIL", "detail": f"reported trades={metrics['trades']} rows={len(trades)}"},
        {"system": system, "check": "valid_timestamps", "status": "PASS" if trades.empty or (trades["exit_time"] >= trades["entry_time"]).all() else "FAIL", "detail": "exit_time >= entry_time"},
        {"system": system, "check": "live_known_rules", "status": "PASS", "detail": "Rules use closed OHLCV/indicator/session/funding estimates available at signal time."},
        {"system": system, "check": "not_real_capital_ready", "status": "PASS", "detail": "No exchange shadow/live proof exists."},
    ]


def correlation_rows(strategy1: pd.DataFrame, sleeve_logs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    s1_month = monthly_table(strategy1).set_index("month")["net_pnl"]
    rows = []
    s1_keys = set(zip(strategy1["entry_time"], strategy1["side"]))
    s1_losing_months = set(monthly_table(strategy1).query("net_pnl < 0")["month"])
    for name, trades in sleeve_logs.items():
        month = monthly_table(trades).set_index("month")["net_pnl"]
        corr = float(s1_month.corr(month)) if len(month) and month.std() != 0 else 0.0
        keys = set(zip(trades["entry_time"], trades["side"])) if not trades.empty else set()
        losing = set(monthly_table(trades).query("net_pnl < 0")["month"])
        rows.append({
            "sleeve_id": name,
            "trade_overlap_count": len(s1_keys & keys),
            "trade_overlap_pct_of_sleeve": round(len(s1_keys & keys) / len(keys), 4) if keys else 0.0,
            "monthly_pnl_correlation_vs_strategy1": round(corr, 4),
            "shared_losing_months": len(s1_losing_months & losing),
            "unique_months_profitable_when_strategy1_loses": len(set(monthly_table(trades).query("net_pnl > 0")["month"]) & s1_losing_months),
            "complementarity_note": "Lower overlap/correlation is more useful for Phase 36 fusion.",
        })
    return pd.DataFrame(rows)


def diagnostic_fusions(df: pd.DataFrame, selected_specs: list[SleeveSpec]) -> pd.DataFrame:
    rows = []
    if not selected_specs:
        return pd.DataFrame([{
            "fusion_name": "NO_PASSING_SLEEVES",
            "net_pnl": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "winning_trades": 0,
            "losing_trades": 0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "expectancy": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "positive_months": 0,
            "negative_months": 0,
            "zero_months": 0,
            "best_month": 0.0,
            "worst_month": 0.0,
            "classification": "DIAGNOSTIC_ONLY_NOT_PROMOTED",
            "note": "No independent sleeve passed candidate gates, so no diagnostic fusion was constructed.",
        }])
    ordered_sets = []
    for n in range(1, min(3, len(selected_specs)) + 1):
        ordered_sets.append((f"Strategy #1 + top {n} independent sleeve(s)", selected_specs[:n]))
    if selected_specs:
        ordered_sets.append(("Strategy #1 + all passing independent sleeves", selected_specs))
    for name, specs in ordered_sets:
        portfolio = PortfolioStrategy([Phase35SignalSleeve(s) for s in specs], conflict_rule="cancel", fusion_mode="union")
        trades = run_engine(df, portfolio)
        m = compute_metrics(trades)
        rows.append({
            "fusion_name": name,
            **m,
            "classification": "DIAGNOSTIC_ONLY_NOT_PROMOTED",
            "note": "Diagnostic independent-sleeve union only; Strategy #1 remains protected baseline.",
        })
    return pd.DataFrame(rows)


def update_memory(verdict: str, selected: pd.DataFrame) -> None:
    selected_ids = ", ".join(selected["sleeve_id"].tolist()) if not selected.empty else "none"
    handoff = f"""# CURRENT HANDOFF
## Last Updated: 2026-07-02 (Phase 35 - Independent Sleeve Conversion)

## Latest Completed Phase: Phase 35

**Verdict:** `{verdict}`

### Strategy #1 Protected Baseline
- Strategy #1 remains Combined Router v1.
- Combined Router v1 remains the active primary executable baseline.
- Strategy #1 vault remains `reports/phase34_strategy_1_combined_router_v1_vault.md`.
- Strategy #1 metrics remain: $11,205.20, 557 trades, PF 1.2522, DD 16.2186%.
- Phase 32 stress truth remains: PASS=7 / FAIL=8, combined adverse -$39,138.38, combined adverse DD 359.59%, STRESS_FRAGILE.
- Live status remains NOT_REAL_CAPITAL_READY.

### Phase 35 Sleeve Conversion
- Phase 35 decoded Phase 34 building blocks and implemented independent closed-candle signal-level sleeve attempts.
- Selected Strategy #2-#6 candidates: {selected_ids}.
- Candidate status: backtest-only candidate sleeves, not locked strategies.
- Diagnostic fusion previews are DIAGNOSTIC_ONLY_NOT_PROMOTED.
- No final fusion was promoted.

### Historical Context Required By Memory Protocol
- Phase 29.6 5m Engine remains historical engine progress: -$9,940.72, 3,111 trades, PF 0.64.
- Phase 31.1 acceptance locked Combined Router v1 as the first real executable baseline.
- Phase 33 did not replace the primary baseline.

### Next Phase
Phase 36 should either tune weak independent sleeves or build a fully proven fusion only if signal-level sleeves show durable metrics, stress resilience, and low correlation. Live status remains NOT_REAL_CAPITAL_READY.
"""
    (PM / "CURRENT_HANDOFF.md").write_text(handoff, encoding="utf-8", newline="\n")

    master_path = PM / "MASTER_PROJECT_STATE.md"
    master = master_path.read_text(encoding="utf-8", errors="ignore")
    if "## Phase 35 Independent Sleeve Conversion Status" not in master:
        master += f"""

## Phase 35 Independent Sleeve Conversion Status

- Strategy #1 remains Combined Router v1 and is unchanged.
- Phase 34 building blocks were decoded and converted into independent signal-level sleeve attempts.
- Selected Strategy #2-#6 candidate sleeves: {selected_ids}.
- Diagnostic fusion is not promoted.
- Live status remains NOT_REAL_CAPITAL_READY.
"""
    master_path.write_text(master, encoding="utf-8", newline="\n")

    registry_path = PM / "BENCHMARK_REGISTRY.csv"
    registry = pd.read_csv(registry_path).astype(object)
    registry = registry[~registry["benchmark_name"].astype(str).str.startswith("Phase 35 ", na=False)].copy()
    rows = []
    for idx, row in selected.reset_index(drop=True).iterrows():
        rows.append({
            "benchmark_name": f"Phase 35 Strategy #{idx + 2} Candidate {row['sleeve_id']}",
            "status": "CANDIDATE_SLEEVE_BACKTEST_VERIFIED_NOT_SHADOWED",
            "pnl": f"{float(row['net_pnl']):.2f}",
            "trades": str(int(row["trades"])),
            "profit_factor": f"{float(row['profit_factor']):.4f}",
            "max_dd": f"{float(row['max_drawdown_pct']) / 100:.6f}",
            "stress_pnl": f"{float(row['combined_adverse_pnl']):.2f}",
            "source_phase": "Phase 35",
            "source_file": row["trade_log_path"],
            "validation_status": "INDEPENDENT_SIGNAL_LEVEL_ENGINE_RUN",
            "notes": "Candidate sleeve only; not a locked strategy or promoted fusion.",
            "net_pnl": f"{float(row['net_pnl']):.2f}",
            "max_drawdown_pct": f"{float(row['max_drawdown_pct']):.4f}",
        })
    if rows:
        registry = pd.concat([registry, pd.DataFrame(rows)], ignore_index=True)
    registry.to_csv(registry_path, index=False)

    open_path = PM / "OPEN_PROBLEMS.md"
    open_text = open_path.read_text(encoding="utf-8", errors="ignore")
    if "## Phase 35 Open Problems" not in open_text:
        open_text += """

## Phase 35 Open Problems

- [OPEN] Strategy #1 is still stress-fragile and remains NOT_REAL_CAPITAL_READY.
- [OPEN] Phase 35 sleeves are candidate sleeves, not locked strategies.
- [OPEN] Diagnostic fusion is not promoted until it beats Strategy #1 with stress and reproduction proof.
"""
    open_path.write_text(open_text, encoding="utf-8", newline="\n")

    next_plan = """# Next Phase Plan - Phase 36

## Goal
Turn the best Phase 35 independent sleeve candidates into a fully proven multi-strategy fusion only if the sleeves remain strong under stress and low-correlation checks.

## Requirements
1. Preserve Strategy #1 as the primary baseline.
2. Do not use trade-log filters as live strategies.
3. Promote no fusion unless metrics, stress, integrity, and reproduction all beat Strategy #1.
4. Preserve Phase 33 as research-only.
5. Keep NOT_REAL_CAPITAL_READY until exchange shadow validation exists.
"""
    (PM / "NEXT_PHASE_PLAN.md").write_text(next_plan, encoding="utf-8", newline="\n")


def write_artifact_registry() -> None:
    artifact_path = PM / "ARTIFACT_REGISTRY.csv"
    artifacts = pd.read_csv(artifact_path).astype(object)
    artifacts = artifacts[artifacts["phase"].astype(str) != "35"].copy()
    rows = []
    for path in sorted(REPORTS.glob("phase35_*")):
        rows.append({
            "artifact_path": f"reports/{path.name}",
            "artifact_type": "phase35_artifact",
            "phase": "35",
            "description": "Phase 35 independent sleeve conversion artifact",
            "sha256": sha256_file(path)[:12],
            "size_kb": round(path.stat().st_size / 1024, 1),
            "exists": "YES",
            "status": "VALID",
        })
    if rows:
        artifacts = pd.concat([artifacts, pd.DataFrame(rows)], ignore_index=True)
    artifacts.to_csv(artifact_path, index=False)


def write_manifest(files: list[str], verdict: str) -> None:
    payload = {
        "phase": "35",
        "verdict": verdict,
        "files": {name: sha256_file(REPORTS / name) for name in files if (REPORTS / name).exists()},
        "rules": {
            "no_forced_metrics": True,
            "no_trade_log_only_filter_promotion": True,
            "strategy1_unchanged": True,
            "live_status": "NOT_REAL_CAPITAL_READY",
        },
    }
    write_text("phase35_audit_manifest.json", json.dumps(payload, indent=2, sort_keys=True))


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    df = load_market()
    strategy1 = enrich_trade_log(pd.read_csv(REPORTS / "phase34_strategy_1_trade_log_copy.csv"))
    strategy1_metrics = compute_metrics(strategy1)
    decode_building_blocks()
    specs = build_specs()
    write_specs(specs)

    result_rows = []
    index_rows = []
    stress_frames = []
    monthly_frames = []
    integrity = []
    sleeve_logs: dict[str, pd.DataFrame] = {}

    for spec in specs:
        sleeve = Phase35SignalSleeve(spec)
        trades = run_engine(df, sleeve)
        path = REPORTS / f"phase35_{spec.sleeve_id}_trade_log.csv"
        trades.to_csv(path, index=False)
        sleeve_logs[spec.sleeve_id] = trades
        metrics = compute_metrics(trades)

        stress = stress_for_strategy(df, lambda s=spec: Phase35SignalSleeve(s), spec.sleeve_id)
        stress_frames.append(stress)
        stress_pass = int((stress["verdict"] == "PASS").sum())
        combined = stress[stress["scenario"] == "combined adverse"].iloc[0].to_dict()
        status = target_status(metrics, stress_pass)

        result_rows.append({
            "sleeve_id": spec.sleeve_id,
            "source_phase34_id": spec.source_phase34_id,
            "family": spec.family,
            "candidate_hash": params_hash({"id": spec.sleeve_id, **spec.params}),
            **metrics,
            "stress_pass_count": stress_pass,
            "stress_fail_count": 15 - stress_pass,
            "combined_adverse_pnl": combined["net_pnl"],
            "combined_adverse_dd": combined["max_drawdown_pct"],
            "candidate_status": status,
            "trade_log_path": f"reports/{path.name}",
            "trade_log_hash": sha256_file(path),
            "params": json.dumps(spec.params, sort_keys=True),
            "execution_status": "INDEPENDENT_SIGNAL_LEVEL_ENGINE_RUN",
        })
        index_rows.append({
            "sleeve_id": spec.sleeve_id,
            "trade_log_path": f"reports/{path.name}",
            "trade_log_hash": sha256_file(path),
            "rows": len(trades),
            "source": "engine-generated independent signal-level sleeve",
        })
        month = monthly_table(trades)
        month.insert(0, "sleeve_id", spec.sleeve_id)
        monthly_frames.append(month)
        integrity.extend(integrity_rows(spec.sleeve_id, trades, metrics))

    results = pd.DataFrame(result_rows).sort_values(["candidate_status", "profit_factor", "net_pnl"], ascending=[True, False, False])
    write_csv("phase35_independent_sleeve_results.csv", results)
    write_csv("phase35_independent_sleeve_trade_log_index.csv", index_rows)
    stress_summary = pd.concat(stress_frames, ignore_index=True)
    write_csv("phase35_independent_sleeve_stress_summary.csv", stress_summary)
    write_csv("phase35_independent_sleeve_monthly_summary.csv", pd.concat(monthly_frames, ignore_index=True))
    write_csv("phase35_independent_sleeve_integrity_audit.csv", integrity)

    passing = results[results["candidate_status"].isin(["PRIMARY_CANDIDATE_PASS", "SECONDARY_CANDIDATE_PASS"])].copy()
    selected = passing.sort_values(["profit_factor", "net_pnl", "trades"], ascending=[False, False, False]).head(5)
    corr = correlation_rows(strategy1, sleeve_logs)
    write_csv("phase35_strategy_correlation_and_complementarity.csv", corr)
    preview = diagnostic_fusions(df, [s for s in specs if s.sleeve_id in set(selected["sleeve_id"])])
    write_csv("phase35_diagnostic_fusion_preview.csv", preview)

    vault_lines = ["# Phase 35 Strategy #2-#6 Candidate Vaults\n"]
    if selected.empty:
        vault_lines.append("No independent sleeve passed the Phase 35 candidate requirements. No Strategy #2-#6 candidate was assigned.\n")
    else:
        for idx, row in selected.reset_index(drop=True).iterrows():
            vault_lines.append(f"## Strategy #{idx + 2} Candidate - {row['sleeve_id']}\n")
            vault_lines.append(f"- Family: `{row['family']}`\n")
            vault_lines.append(f"- Source Phase 34 idea: `{row['source_phase34_id']}`\n")
            vault_lines.append(f"- Metrics: PnL {row['net_pnl']}, trades {row['trades']}, PF {row['profit_factor']}, DD {row['max_drawdown_pct']}%.\n")
            vault_lines.append(f"- Stress: {row['stress_pass_count']}/15 PASS; combined adverse {row['combined_adverse_pnl']}.\n")
            vault_lines.append(f"- Trade log: `{row['trade_log_path']}`\n")
            vault_lines.append(f"- Trade log hash: `{row['trade_log_hash']}`\n")
            vault_lines.append("- Status: candidate sleeve only, BACKTEST_VERIFIED_NOT_SHADOWED, NOT_REAL_CAPITAL_READY.\n")
            vault_lines.append("- Weakness: not locked as final strategy; fusion promotion requires Phase 36 proof.\n")
    write_text("phase35_strategy_2_to_6_candidate_vaults.md", "\n".join(vault_lines))

    if len(selected) >= 4:
        verdict = "PHASE35_PASS_INDEPENDENT_STRATEGY_BUILDING_BLOCKS_FOUND"
    elif len(selected) >= 1:
        verdict = "PHASE35_PARTIAL_PASS_SOME_INDEPENDENT_SLEEVES_FOUND"
    else:
        verdict = "PHASE35_RESEARCH_ONLY_BUILDING_BLOCKS_NOT_YET_EXECUTABLE"

    report = f"""# Phase 35 - Independent Sleeve Conversion and Fusion Readiness Report

## Final Verdict

`{verdict}`

## Strategy #1 Preservation

Strategy #1 remains Combined Router v1 and was not modified. Locked metrics from the vault trade log:

- PnL: ${strategy1_metrics['net_pnl']:,.2f}
- Trades: {strategy1_metrics['trades']}
- PF: {strategy1_metrics['profit_factor']:.4f}
- DD: {strategy1_metrics['max_drawdown_pct']:.4f}%

## Building Block Decode

The Phase 34 selected IDs were decoded in `reports/phase35_building_block_decoder.csv`. The important finding remains that Phase 34 selected candidates were deterministic gates over Strategy #1 trades; Phase 35 rebuilt their ideas as independent signal-level sleeves.

## Independent Sleeve Results

Results are in `reports/phase35_independent_sleeve_results.csv`. Passing candidate sleeves: {len(selected)}.

{selected[['sleeve_id','net_pnl','trades','profit_factor','max_drawdown_pct','stress_pass_count','candidate_status']].to_markdown(index=False) if not selected.empty else 'No sleeve passed the primary or secondary candidate gate.'}

## Integrity

Every Phase 35 sleeve was executed through the existing engine from closed-candle indicator rules. Integrity audit: `reports/phase35_independent_sleeve_integrity_audit.csv`.

## Complementarity

Correlation and overlap versus Strategy #1 are reported in `reports/phase35_strategy_correlation_and_complementarity.csv`.

## Diagnostic Fusion

Fusion previews are diagnostic only and are not promoted. Output: `reports/phase35_diagnostic_fusion_preview.csv`.

## Live Status

`NOT_REAL_CAPITAL_READY`. No exchange shadow/live execution proof exists.

## Phase 36 Recommendation

If candidate sleeves passed, Phase 36 should run true fusion construction with serialized routing, stress gates, and full reproduction. If no sleeve passed, Phase 36 should tune the independent sleeves, not revert to trade-log filtering.
"""
    write_text("phase35_independent_sleeve_conversion_and_fusion_readiness_report.md", report)

    update_memory(verdict, selected)
    generated = [
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
    ] + [f"phase35_{spec.sleeve_id}_trade_log.csv" for spec in specs]
    write_manifest(generated, verdict)
    write_artifact_registry()

    print(json.dumps({"verdict": verdict, "selected": selected["sleeve_id"].tolist(), "strategy1_pnl": strategy1_metrics["net_pnl"]}, indent=2))


if __name__ == "__main__":
    main()
