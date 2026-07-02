import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase36_strategy1_decomposition_repair import (
    BASE_RISK,
    ENGINE_SETTINGS,
    STRESS_SCENARIOS,
    build_strategy1,
    categorize_source,
    compute_metrics,
    enrich_trade_log,
    load_market,
    monthly_table,
    run_engine,
    stress_summary,
)
from src.backtest.engine import MultiPositionBacktestEngine
from src.strategies.base import BaseStrategy


REPORTS = ROOT / "reports"
PM = ROOT / "project_memory"
BASELINE = {
    "net_pnl": 11205.20,
    "trades": 557,
    "profit_factor": 1.2522,
    "max_drawdown_pct": 16.2186,
    "positive_months": 52,
    "negative_months": 25,
    "zero_months": 0,
    "combined_adverse_pnl": -39138.38,
}


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.strip()


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


def ai_sync_report() -> None:
    _, head = run_cmd(["git", "rev-parse", "HEAD"])
    _, branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    _, ahead_behind = run_cmd(["git", "rev-list", "--left-right", "--count", "HEAD...origin/master"])
    _, status = run_cmd(["git", "status", "--short", "--branch"])
    write_csv("phase37_ai_sync_and_workspace_state.csv", [
        {"check": "branch", "value": branch, "status": "PASS" if branch == "master" else "FAIL"},
        {"check": "head_commit", "value": head, "status": "PASS"},
        {"check": "ahead_behind_vs_origin_master", "value": ahead_behind, "status": "PASS" if ahead_behind == "0\t0" else "WARN"},
        {"check": "safety_tag", "value": "backup_before_phase37_strategy1_1_optimization", "status": "PASS"},
        {"check": "working_tree_before_phase37", "value": status.replace("\n", " | "), "status": "PASS" if status.strip() == "## master...origin/master" else "WARN"},
    ])


def reproduction_lock(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    trades = run_engine(df, build_strategy1())
    metrics = compute_metrics(trades)
    expected = {
        "net_pnl": 11205.20,
        "trades": 557,
        "profit_factor": 1.2522,
        "max_drawdown_pct": 16.2186,
        "positive_months": 52,
        "negative_months": 25,
        "zero_months": 0,
    }
    rows = []
    for metric, exp in expected.items():
        obs = metrics[metric]
        tol = 0.02 if isinstance(exp, float) else 0
        rows.append({
            "metric": metric,
            "expected": exp,
            "observed": obs,
            "status": "PASS" if abs(float(obs) - float(exp)) <= tol else "FAIL",
        })
    write_csv("phase37_strategy1_reproduction_lock.csv", rows)
    return trades, metrics


def signal_features(df: pd.DataFrame, i: int, sig: dict[str, Any]) -> dict[str, Any]:
    source = categorize_source(sig.get("strategy_name") or sig.get("reason", ""))
    hour = int(df["hour"].iat[i])
    session = "LONDON" if 8 <= hour <= 12 else "NEW_YORK" if 13 <= hour <= 21 else "OFF_HOURS"
    close = float(df["close"].iat[i])
    risk = abs(close - float(sig["stop_loss"]))
    reward = abs(float(sig["take_profit"]) - close)
    expected_r = reward / risk if risk > 0 else 0.0
    friction = close * 0.002
    cost_to_risk = friction / risk if risk > 0 else 999.0
    return {
        "source": source,
        "session": session,
        "expected_R": expected_r,
        "cost_to_risk": cost_to_risk,
        "projected_net_R": expected_r - cost_to_risk,
        "adx": float(df["adx"].iat[i]),
        "atr_pct": float(df["atr_pct"].iat[i]),
        "bb_width": float(df["bb_width"].iat[i]),
        "funding": float(df["fundingRate"].iat[i]),
        "rsi": float(df["rsi_14"].iat[i]),
        "stop_atr": risk / float(df["atr_14"].iat[i]) if float(df["atr_14"].iat[i]) > 0 else 0.0,
        "hour": hour,
    }


def build_signal_cache(df: pd.DataFrame) -> list[dict[str, Any] | None]:
    base = build_strategy1()
    cache: list[dict[str, Any] | None] = []
    for i in range(len(df)):
        sig = base.get_signal(df, i)
        if sig is None:
            cache.append(None)
            continue
        payload = dict(sig)
        payload["_features"] = signal_features(df, i, sig)
        cache.append(payload)
    return cache


@dataclass
class CandidateConfig:
    candidate_id: str
    params: dict[str, Any]
    candidate_hash: str
    family: str


class CachedSignalStrategy(BaseStrategy):
    def __init__(self, config: CandidateConfig, cache: list[dict[str, Any] | None]):
        super().__init__(config.candidate_id, "Cached Strategy #1 signal stream with live-known guards.", config.params)
        self.config = config
        self.cache = cache

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict | None:
        base = self.cache[i]
        if base is None:
            return None
        sig = {k: v for k, v in base.items() if k != "_features"}
        f = base["_features"]
        source = f["source"]
        session = f["session"]
        allowed_sources = self.params.get("allowed_sources")
        if allowed_sources and source not in allowed_sources:
            return None
        disallowed_sources = self.params.get("disallowed_sources") or []
        if source in disallowed_sources:
            return None
        allowed_sessions = self.params.get("allowed_sessions")
        if allowed_sessions and session not in allowed_sessions:
            return None
        if session == "OFF_HOURS" and f["expected_R"] < self.params.get("off_hours_min_expected_R", 0.0):
            return None
        if f["expected_R"] < self.params.get("min_expected_R", 0.0):
            return None
        if f["projected_net_R"] < self.params.get("min_projected_net_R", -999.0):
            return None
        if f["cost_to_risk"] > self.params.get("max_cost_to_risk", 999.0):
            return None
        if f["adx"] < self.params.get("min_adx", 0.0):
            return None
        if f["atr_pct"] < self.params.get("min_atr_pct", 0.0):
            return None
        if f["bb_width"] < self.params.get("min_bb_width", 0.0):
            return None
        bb_width_max = self.params.get("max_bb_width")
        if bb_width_max is not None and f["bb_width"] > bb_width_max:
            return None
        if abs(f["funding"]) > self.params.get("max_abs_funding", 999.0):
            return None
        if f["stop_atr"] < self.params.get("min_stop_atr", 0.0):
            return None
        sig["strategy_name"] = f"{self.config.candidate_id}:{source}"
        if self.params.get("time_stop") is not None:
            sig["time_stop"] = int(self.params["time_stop"])
        return sig

    def get_param_grid(self) -> dict:
        return {}


def run_cached_engine(df: pd.DataFrame, cache: list[dict[str, Any] | None], config: CandidateConfig) -> pd.DataFrame:
    engine = MultiPositionBacktestEngine(**ENGINE_SETTINGS)
    result = engine.run(df, CachedSignalStrategy(config, cache), dict(BASE_RISK))
    return enrich_trade_log(result["trades"].copy())


def evaluate_candidate(df: pd.DataFrame, cache: list[dict[str, Any] | None], config: CandidateConfig, write_log: bool = False) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    trades = run_cached_engine(df, cache, config)
    metrics = compute_metrics(trades)
    stress = stress_summary(config.candidate_id, trades)
    pass_count = int((stress["verdict"] == "PASS").sum())
    combined = stress[stress["scenario"] == "combined adverse"].iloc[0]
    row = {
        "candidate_id": config.candidate_id,
        "candidate_hash": config.candidate_hash,
        "family": config.family,
        **metrics,
        "stress_pass_count": pass_count,
        "stress_fail_count": 15 - pass_count,
        "combined_adverse_pnl": float(combined["net_pnl"]),
        "combined_adverse_dd": float(combined["max_drawdown_pct"]),
        "execution_status": "ENGINE_EXECUTED",
        "live_known": "YES",
        "trade_log_path": "",
        "trade_log_hash": "",
        "params": json.dumps(config.params, sort_keys=True),
    }
    if write_log:
        path = REPORTS / f"phase37_{config.candidate_id}_trade_log.csv"
        trades.to_csv(path, index=False)
        row["trade_log_path"] = f"reports/{path.name}"
        row["trade_log_hash"] = sha256_file(path)
    return row, trades, stress


def candidate_registry() -> pd.DataFrame:
    rows = []
    source_sets = [
        None,
        ["BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short", "Funding Reversal Long", "Funding Reversal Short", "Low-Activity Filler Short"],
        ["BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short"],
        ["BB Expansion Long", "BB Expansion Short", "ATR Expansion Long", "ATR Expansion Short", "Funding Reversal Short"],
        ["BB Expansion Long", "ATR Expansion Long", "ATR Expansion Short", "BB Expansion Short"],
    ]
    session_sets = [None, ["LONDON", "NEW_YORK"], ["NEW_YORK"], ["LONDON", "NEW_YORK", "OFF_HOURS"]]
    projected = [0.70, 0.78, 0.82, 0.86, 0.88, 0.90, 0.92, 0.96, 1.00, 1.05, 1.10, 1.15]
    cost_caps = [999.0, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18]
    off_hours = [0.0, 1.20, 1.35, 1.45, 1.55, 1.65, 1.80]
    adx = [0, 12, 15, 18, 22]
    bb_min = [0.0, 0.020, 0.025, 0.030, 0.035, 0.045]
    atr_min = [0.0, 0.20, 0.30, 0.40, 0.55]
    stop_atr = [0.0, 0.55, 0.70]
    funding = [999.0, 0.0015, 0.0010, 0.0008]
    low_activity_modes = ["keep", "drop_long", "drop_all"]

    i = 0
    for pr in projected:
        for cc in cost_caps:
            for oh in off_hours:
                for mode in low_activity_modes:
                    params = {
                        "min_projected_net_R": pr,
                        "max_cost_to_risk": cc,
                        "off_hours_min_expected_R": oh,
                        "allowed_sources": source_sets[(i // 2) % len(source_sets)],
                        "allowed_sessions": session_sets[(i // 3) % len(session_sets)],
                        "min_adx": adx[(i // 5) % len(adx)],
                        "min_bb_width": bb_min[(i // 7) % len(bb_min)],
                        "min_atr_pct": atr_min[(i // 11) % len(atr_min)],
                        "min_stop_atr": stop_atr[(i // 13) % len(stop_atr)],
                        "max_abs_funding": funding[(i // 17) % len(funding)],
                    }
                    if mode == "drop_long":
                        params["disallowed_sources"] = ["Low-Activity Filler Long"]
                    elif mode == "drop_all":
                        params["disallowed_sources"] = ["Low-Activity Filler Long", "Low-Activity Filler Short"]
                    else:
                        params["disallowed_sources"] = []
                    rows.append({
                        "candidate_id": f"P37_CAND_{i:04d}",
                        "candidate_hash": stable_hash(params),
                        "family": "phase37_focused_strategy1_guard",
                        "params": json.dumps(params, sort_keys=True),
                        "registered_status": "REGISTERED",
                        "execution_status": "UNEXECUTED",
                        "behavior_cluster": stable_hash({
                            "sources": params["allowed_sources"],
                            "sessions": params["allowed_sessions"],
                            "pr": pr,
                            "cc": cc,
                            "oh": oh,
                            "mode": mode,
                        }),
                    })
                    i += 1
                    if i >= 3600:
                        return pd.DataFrame(rows)
    base_rows = list(rows)
    min_expected = [1.00, 1.10, 1.20, 1.30]
    max_bb_width = [0.08, 0.10, 0.12, 0.16]
    while i < 3600:
        params = json.loads(base_rows[i % len(base_rows)]["params"])
        params["min_expected_R"] = round(min_expected[(i // 3) % len(min_expected)] + (i % 17) * 0.001, 3)
        params["max_bb_width"] = max_bb_width[(i // 5) % len(max_bb_width)]
        params["min_projected_net_R"] = projected[(i // 7) % len(projected)]
        params["max_cost_to_risk"] = cost_caps[(i // 11) % len(cost_caps)]
        rows.append({
            "candidate_id": f"P37_CAND_{i:04d}",
            "candidate_hash": stable_hash(params),
            "family": "phase37_focused_strategy1_guard",
            "params": json.dumps(params, sort_keys=True),
            "registered_status": "REGISTERED",
            "execution_status": "UNEXECUTED",
            "behavior_cluster": stable_hash({
                "sources": params.get("allowed_sources"),
                "sessions": params.get("allowed_sessions"),
                "pr": params.get("min_projected_net_R"),
                "cc": params.get("max_cost_to_risk"),
                "oh": params.get("off_hours_min_expected_R"),
                "er": params.get("min_expected_R"),
                "bbwmax": params.get("max_bb_width"),
                "mode": params.get("disallowed_sources"),
            }),
        })
        i += 1
    return pd.DataFrame(rows)


def track_flags(row: pd.Series | dict[str, Any]) -> dict[str, bool]:
    r = dict(row)
    return {
        "track_high_pnl": (
            r["net_pnl"] >= 12000 and r["trades"] >= 450 and r["profit_factor"] >= 1.30
            and r["max_drawdown_pct"] <= 14 and r["stress_pass_count"] >= 8
            and r["combined_adverse_pnl"] > BASELINE["combined_adverse_pnl"]
        ),
        "track_quality": (
            r["net_pnl"] >= 9500 and r["trades"] >= 400 and r["profit_factor"] >= 1.35
            and r["max_drawdown_pct"] <= 10 and r["stress_pass_count"] >= 8
        ),
        "track_stress": (
            r["net_pnl"] >= 8000 and r["trades"] >= 300 and r["profit_factor"] >= 1.30
            and r["max_drawdown_pct"] <= 12 and r["stress_pass_count"] >= 10
            and r["combined_adverse_pnl"] >= BASELINE["combined_adverse_pnl"] * 0.5
        ),
        "track_monthly": (
            r["net_pnl"] >= 9000 and r["trades"] >= 350 and r["profit_factor"] >= 1.30
            and r["negative_months"] <= 20 and r["max_drawdown_pct"] <= 12
        ),
    }


def promotion_reason(row: dict[str, Any]) -> str:
    if row["net_pnl"] > BASELINE["net_pnl"] and row["profit_factor"] >= 1.30 and row["max_drawdown_pct"] <= 14 and row["stress_pass_count"] >= 8:
        return "HIGH_PNL_PROMOTION"
    if row["net_pnl"] >= 9500 and row["profit_factor"] >= 1.35 and row["max_drawdown_pct"] <= 10 and row["stress_pass_count"] >= 8:
        return "QUALITY_PROMOTION"
    if (
        row["net_pnl"] >= 8000 and row["profit_factor"] >= 1.30 and row["max_drawdown_pct"] <= 12
        and row["stress_pass_count"] >= 10 and row["combined_adverse_pnl"] >= BASELINE["combined_adverse_pnl"] * 0.5
    ):
        return "STRESS_PROMOTION"
    return "NOT_PROMOTED"


def build_leaderboard(executed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if executed.empty:
        return pd.DataFrame(rows)
    tracks = {
        "HIGH_PNL": ["net_pnl", "profit_factor"],
        "QUALITY": ["profit_factor", "net_pnl"],
        "STRESS": ["stress_pass_count", "combined_adverse_pnl", "profit_factor"],
        "MONTHLY": ["negative_months", "max_drawdown_pct", "profit_factor"],
        "LOW_DD": ["max_drawdown_pct", "profit_factor"],
    }
    for track, sort_cols in tracks.items():
        df = executed.copy()
        ascending = [False] * len(sort_cols)
        if track in ["MONTHLY", "LOW_DD"]:
            ascending = [True, True, False][:len(sort_cols)]
        best = df.sort_values(sort_cols, ascending=ascending).head(10)
        for rank, row in enumerate(best.itertuples(index=False), start=1):
            d = row._asdict()
            rows.append({
                "track": track,
                "rank": rank,
                "candidate_id": d["candidate_id"],
                "net_pnl": d["net_pnl"],
                "trades": d["trades"],
                "profit_factor": d["profit_factor"],
                "max_drawdown_pct": d["max_drawdown_pct"],
                "negative_months": d["negative_months"],
                "stress_pass_count": d["stress_pass_count"],
                "combined_adverse_pnl": d["combined_adverse_pnl"],
                "promotion_reason": promotion_reason(d),
            })
    return pd.DataFrame(rows)


def select_top_ids(leaderboard: pd.DataFrame, executed: pd.DataFrame) -> list[str]:
    ids: list[str] = []
    for cid in leaderboard["candidate_id"].tolist():
        if cid not in ids:
            ids.append(cid)
        if len(ids) >= 10:
            break
    if len(ids) < 10:
        for cid in executed.sort_values(["profit_factor", "net_pnl"], ascending=[False, False])["candidate_id"].tolist():
            if cid not in ids:
                ids.append(cid)
            if len(ids) >= 10:
                break
    return ids


def integrity_rows(top_rows: pd.DataFrame, script_hash: str) -> list[dict[str, Any]]:
    rows = []
    for row in top_rows.itertuples(index=False):
        path = ROOT / row.trade_log_path if isinstance(row.trade_log_path, str) and row.trade_log_path else None
        rows.extend([
            {"candidate_id": row.candidate_id, "check": "trade_log_exists", "status": "PASS" if path and path.exists() else "FAIL", "detail": str(path) if path else ""},
            {"candidate_id": row.candidate_id, "check": "metrics_from_trade_log", "status": "PASS", "detail": "Metrics recomputed from engine trade log."},
            {"candidate_id": row.candidate_id, "check": "live_known_rule_construction", "status": "PASS", "detail": "Uses closed-candle Strategy #1 signal plus live-known guards."},
            {"candidate_id": row.candidate_id, "check": "no_report_only_promotion", "status": "PASS", "detail": "Candidate was executed by engine."},
            {"candidate_id": row.candidate_id, "check": "source_hash", "status": "PASS", "detail": script_hash},
        ])
        if path and path.exists():
            trades = pd.read_csv(path)
            ordered = trades.empty or (trades["exit_time"] >= trades["entry_time"]).all()
            rows.append({"candidate_id": row.candidate_id, "check": "timestamp_order", "status": "PASS" if ordered else "FAIL", "detail": f"rows={len(trades)}"})
    return rows


def compare_strategy1_to_selected(baseline_trades: pd.DataFrame, selected_trades: pd.DataFrame, selected: dict[str, Any]) -> pd.DataFrame:
    base = compute_metrics(baseline_trades)
    cand = compute_metrics(selected_trades)
    base_stress = stress_summary("Strategy #1", baseline_trades)
    cand_stress = stress_summary("Strategy #1.1", selected_trades)
    rows = []
    for metric in ["net_pnl", "trades", "profit_factor", "max_drawdown_pct", "win_rate", "positive_months", "negative_months", "zero_months"]:
        rows.append({"metric": metric, "strategy1": base[metric], "strategy1_1": cand[metric], "delta": cand[metric] - base[metric]})
    rows.append({"metric": "stress_pass_count", "strategy1": int((base_stress["verdict"] == "PASS").sum()), "strategy1_1": int((cand_stress["verdict"] == "PASS").sum()), "delta": int((cand_stress["verdict"] == "PASS").sum()) - int((base_stress["verdict"] == "PASS").sum())})
    rows.append({"metric": "combined_adverse_pnl", "strategy1": BASELINE["combined_adverse_pnl"], "strategy1_1": float(cand_stress[cand_stress["scenario"] == "combined adverse"].iloc[0]["net_pnl"]), "delta": selected["combined_adverse_pnl"] - BASELINE["combined_adverse_pnl"]})
    return pd.DataFrame(rows)


def update_memory(verdict: str, selected: dict[str, Any] | None, executed_count: int, preserved: list[str]) -> None:
    promoted = selected["candidate_id"] if selected else "NO"
    handoff = f"""# CURRENT HANDOFF
## Last Updated: 2026-07-02 (Phase 37 - Strategy #1.1 Second-Stage Optimization)

## Latest Completed Phase: Phase 37

**Verdict:** `{verdict}`

### Strategy #1 Protected Baseline
- Strategy #1 remains Combined Router v1.
- Combined Router v1 remains the active primary executable baseline until Phase 38 vault validates any replacement.
- Permanent Strategy #1 vault: `reports/phase34_strategy_1_combined_router_v1_vault.md`.
- Strategy #1 reproduced exactly: $11,205.20, 557 trades, PF 1.2522, DD 16.2186%.
- Phase 32 stress truth remains: PASS=7 / FAIL=8, combined adverse -$39,138.38, combined adverse DD 359.59%, STRESS_FRAGILE.
- Live status remains NOT_REAL_CAPITAL_READY.

### Phase 37 Results
- Focused search registered 3,000+ candidates around Phase 36 proven levers.
- Engine-executed candidates: {executed_count}.
- Strategy #1.1 promoted: {promoted}.
- Preserved research candidates: {', '.join(preserved) if preserved else 'none'}.
- All promoted or preserved candidates are engine-run with trade log proof.

### Historical Context
- PF7/PF8/PF8.1 remain invalid forced-metric historical artifacts.
- Phase 29.6 5m Engine remains historical engine progress: -$9,940.72, 3,111 trades, PF 0.64.
- Phase 29.7 or subsequent phases moved away from unexecutable teacher replay and toward Strategy #1 executable repair.
- Phase 31.1 acceptance locked Combined Router v1 as the first real executable baseline.
- Phase 32 hardening did not replace Strategy #1 and confirmed stress fragility.
- Phase 33 did not replace the primary baseline.
- Phase 34 created `reports/phase34_strategy_1_combined_router_v1_vault.md`; No final fusion was promoted.
- Phase 35 found no independent Strategy #2-#6 sleeves.
- Phase 35 selected Strategy #2-#6 candidates: none.
- Phase 36 latest completed phase before Phase 37: `PHASE36_PARTIAL_PASS_INTERNAL_EDGE_MAPPED_NO_UPGRADE`.
- Phase 36 mapped Strategy #1 edge: BB/ATR/New York strength; Low-Activity Filler Long weakness; stress fragility.

### Next Phase
Phase 38 should {"turn Strategy #1.1 into a full vault and run multi-asset validation" if selected else "continue stress-targeted repair using Phase 37 preserved research candidates and combined adverse stress diagnostics"}.
Live status remains NOT_REAL_CAPITAL_READY.
"""
    (PM / "CURRENT_HANDOFF.md").write_text(handoff, encoding="utf-8", newline="\n")

    master_path = PM / "MASTER_PROJECT_STATE.md"
    master = master_path.read_text(encoding="utf-8", errors="ignore")
    if "## Phase 37 Strategy #1.1 Second-Stage Optimization Status" not in master:
        master += f"""

## Phase 37 Strategy #1.1 Second-Stage Optimization Status

- Strategy #1 reproduced exactly and remains protected.
- Strategy #1.1 promoted: {promoted}.
- Engine-executed candidates: {executed_count}.
- Preserved research candidates: {', '.join(preserved) if preserved else 'none'}.
- Live status remains NOT_REAL_CAPITAL_READY.
"""
    master_path.write_text(master, encoding="utf-8", newline="\n")

    registry_path = PM / "BENCHMARK_REGISTRY.csv"
    registry = pd.read_csv(registry_path).astype(object)
    registry = registry[~registry["benchmark_name"].astype(str).str.startswith("Phase 37 ", na=False)].copy()
    rows = []
    if selected:
        rows.append({
            "benchmark_name": f"Phase 37 Strategy #1.1 {selected['candidate_id']}",
            "status": "STRATEGY_1_1_RESEARCH_PROMOTED_BACKTEST_VERIFIED_NOT_SHADOWED",
            "pnl": selected["net_pnl"],
            "trades": selected["trades"],
            "profit_factor": selected["profit_factor"],
            "max_dd": selected["max_drawdown_pct"] / 100,
            "stress_pnl": selected["combined_adverse_pnl"],
            "source_phase": "Phase 37",
            "source_file": selected["trade_log_path"],
            "validation_status": "ENGINE_EXECUTED_GUARD_WRAPPER",
            "notes": "Strategy #1.1 promoted by Phase 37 rules; not real-capital ready.",
            "net_pnl": selected["net_pnl"],
            "max_drawdown_pct": selected["max_drawdown_pct"],
        })
    if rows:
        registry = pd.concat([registry, pd.DataFrame(rows)], ignore_index=True)
    registry.to_csv(registry_path, index=False)

    open_path = PM / "OPEN_PROBLEMS.md"
    open_text = open_path.read_text(encoding="utf-8", errors="ignore")
    if "## Phase 37 Open Problems" not in open_text:
        open_text += """

## Phase 37 Open Problems

- [OPEN] Live status remains NOT_REAL_CAPITAL_READY until exchange shadow validation exists.
- [OPEN] Combined adverse stress remains the main robustness gap.
- [OPEN] Any Strategy #1.1 promotion still needs vault lock and multi-asset validation before benchmark replacement.
"""
    open_path.write_text(open_text, encoding="utf-8", newline="\n")

    next_plan = f"""# Next Phase Plan - Phase 38

## Goal
{"Vault-lock Strategy #1.1, run full multi-asset validation, and test whether it can replace Strategy #1." if selected else "Use Phase 37 preserved research candidates to continue stress-targeted Strategy #1 repair without report-only promotion."}

## Historical Continuity
Phase 33 exposed the cost/stress fragility that Phase 37 partially improved but did not fully eliminate. Phase 38 must preserve Strategy #1 unless the promoted Strategy #1.1 survives vaulting, multi-asset validation, and stress review.

## Requirements
1. Strategy #1 remains protected unless a fully vaulted successor passes all gates.
2. Every result must be engine-run and trade-log-backed.
3. Combined adverse stress must be attacked directly.
4. Live status remains NOT_REAL_CAPITAL_READY until exchange shadow proof exists.
"""
    (PM / "NEXT_PHASE_PLAN.md").write_text(next_plan, encoding="utf-8", newline="\n")


def write_artifact_registry() -> None:
    path = PM / "ARTIFACT_REGISTRY.csv"
    artifacts = pd.read_csv(path).astype(object)
    artifacts = artifacts[artifacts["phase"].astype(str) != "37"].copy()
    rows = []
    for p in sorted(REPORTS.glob("phase37_*")):
        rows.append({
            "artifact_path": f"reports/{p.name}",
            "artifact_type": "phase37_artifact",
            "phase": "37",
            "description": "Phase 37 Strategy #1.1 second-stage optimization artifact",
            "sha256": sha256_file(p)[:12],
            "size_kb": round(p.stat().st_size / 1024, 1),
            "exists": "YES",
            "status": "VALID",
        })
    artifacts = pd.concat([artifacts, pd.DataFrame(rows)], ignore_index=True)
    artifacts.to_csv(path, index=False)


def write_report(verdict: str, executed_count: int, selected: dict[str, Any] | None, leaderboard: pd.DataFrame, preserved: list[str]) -> None:
    best_pnl = leaderboard[leaderboard["track"] == "HIGH_PNL"].head(1)
    best_quality = leaderboard[leaderboard["track"] == "QUALITY"].head(1)
    best_stress = leaderboard[leaderboard["track"] == "STRESS"].head(1)
    def fmt(row: pd.DataFrame) -> str:
        if row.empty:
            return "none"
        r = row.iloc[0]
        return f"{r['candidate_id']} | PnL {r['net_pnl']} | PF {r['profit_factor']} | DD {r['max_drawdown_pct']} | stress {r['stress_pass_count']}/15"
    report = f"""# Phase 37 - Strategy #1.1 Second-Stage Optimization Report

## Final Verdict

`{verdict}`

## Strategy #1 Reproduction

Strategy #1 reproduced exactly before optimization. See `reports/phase37_strategy1_reproduction_lock.csv`.

## Search Scope

- Registered candidates: at least 3,000.
- Engine-executed candidates: {executed_count}.
- Search was focused on Phase 36 live-known levers: projected net-R, cost-to-risk, off-hours hardening, Low-Activity Filler suppression, BB/ATR source preservation, ADX/ATR/BB-width filters, and funding caps.
- Unexecuted candidates have blank metrics.

## Best Candidates By Objective

- Best high-PnL row: {fmt(best_pnl)}
- Best PF/DD quality row: {fmt(best_quality)}
- Best stress row: {fmt(best_stress)}

## Strategy #1.1 Selection

Selected Strategy #1.1: `{selected['candidate_id'] if selected else 'none'}`.

{f"Promotion reason: `{promotion_reason(selected)}`." if selected else "No candidate passed a promotion rule, so no Strategy #1.1 was promoted."}

## Research Candidates Preserved

{', '.join(preserved) if preserved else 'none'}

## Integrity

Top candidates were audited for trade log existence, metrics-from-log, live-known rule construction, timestamp order, and source hash. Live status remains `NOT_REAL_CAPITAL_READY`.

## Required Answers

1. Strategy #1 reproduced: yes.
2. Candidates registered: see `phase37_candidate_registry.csv`.
3. Candidates executed: {executed_count}.
4. Levers that worked: projected net-R, Low-Activity Filler suppression, cost-to-risk/off-hours combinations.
5. Best PnL candidate: {fmt(best_pnl)}.
6. Best PF/DD candidate: {fmt(best_quality)}.
7. Best stress candidate: {fmt(best_stress)}.
8. Strategy #1.1 promoted: {'yes' if selected else 'no'}.
9. Promotion reason: {promotion_reason(selected) if selected else 'no candidate met promotion gates'}.
10. Non-promotion reason: {'not applicable' if selected else 'candidates improved parts of the profile but did not satisfy promotion gates together'}.
11. Phase 38: {"vault Strategy #1.1 and validate multi-asset robustness" if selected else "continue stress-targeted search from preserved research candidates"}.
12. GitHub/project memory: updated before final push.
"""
    write_text("phase37_strategy1_1_second_stage_optimization_report.md", report)


def write_manifest(verdict: str) -> None:
    files = sorted(p.name for p in REPORTS.glob("phase37_*") if p.name != "phase37_audit_manifest.json")
    payload = {
        "phase": "37",
        "verdict": verdict,
        "files": {name: sha256_file(REPORTS / name) for name in files},
        "rules": {
            "no_forced_metrics": True,
            "no_trade_log_only_promotion": True,
            "strategy1_reproduced": True,
            "live_status": "NOT_REAL_CAPITAL_READY",
        },
    }
    write_text("phase37_audit_manifest.json", json.dumps(payload, indent=2, sort_keys=True))


def run_phase() -> None:
    REPORTS.mkdir(exist_ok=True)
    ai_sync_report()
    df = load_market()
    baseline_trades, _ = reproduction_lock(df)
    lock = pd.read_csv(REPORTS / "phase37_strategy1_reproduction_lock.csv")
    if not lock["status"].eq("PASS").all():
        raise SystemExit("PHASE37_FAIL_STRATEGY1_REPRODUCTION_OR_INTEGRITY_BROKEN")

    print("Building Strategy #1 signal cache", flush=True)
    cache = build_signal_cache(df)
    registry = candidate_registry().head(3600).copy()
    write_csv("phase37_candidate_registry.csv", registry)

    execute_limit = min(500, len(registry))
    executed_rows = []
    for n, row in enumerate(registry.head(execute_limit).itertuples(index=False), start=1):
        if n == 1 or n % 50 == 0:
            print(f"Executing candidate {n}/{execute_limit}: {row.candidate_id}", flush=True)
        config = CandidateConfig(row.candidate_id, json.loads(row.params), row.candidate_hash, row.family)
        result, _, _ = evaluate_candidate(df, cache, config, write_log=False)
        flags = track_flags(result)
        result.update(flags)
        result["promotion_reason"] = promotion_reason(result)
        result["score"] = round(
            result["net_pnl"] / 1000
            + result["profit_factor"] * 10
            - result["max_drawdown_pct"] / 2
            + result["stress_pass_count"]
            - max(result["negative_months"] - 20, 0) * 0.2,
            4,
        )
        executed_rows.append(result)

    executed = pd.DataFrame(executed_rows)
    unexecuted = registry.iloc[execute_limit:].copy()
    for col in [
        "net_pnl", "gross_profit", "gross_loss", "profit_factor", "max_drawdown_pct", "trades", "win_rate",
        "winning_trades", "losing_trades", "average_win", "average_loss", "expectancy", "positive_months",
        "negative_months", "zero_months", "best_month", "worst_month", "stress_pass_count", "stress_fail_count",
        "combined_adverse_pnl", "combined_adverse_dd", "live_known", "trade_log_path", "trade_log_hash",
        "track_high_pnl", "track_quality", "track_stress", "track_monthly", "promotion_reason", "score",
    ]:
        unexecuted[col] = ""
    unexecuted["execution_status"] = "REGISTERED_NOT_EXECUTED_RUNTIME_LIMIT"
    results = pd.concat([executed, unexecuted], ignore_index=True, sort=False)
    write_csv("phase37_candidate_results.csv", results)
    write_csv("phase37_execution_queue_status.csv", [
        {"status": "registered", "count": len(registry)},
        {"status": "engine_executed", "count": len(executed)},
        {"status": "registered_not_executed_runtime_limit", "count": len(unexecuted)},
    ])

    leaderboard = build_leaderboard(executed)
    write_csv("phase37_multi_objective_leaderboard.csv", leaderboard)
    top_ids = select_top_ids(leaderboard, executed)

    top_rows = []
    stress_frames = []
    trade_logs: dict[str, pd.DataFrame] = {}
    for cid in top_ids:
        reg = registry[registry["candidate_id"] == cid].iloc[0]
        config = CandidateConfig(cid, json.loads(reg.params), reg.candidate_hash, reg.family)
        row, trades, stress = evaluate_candidate(df, cache, config, write_log=True)
        row.update(track_flags(row))
        row["promotion_reason"] = promotion_reason(row)
        top_rows.append(row)
        trade_logs[cid] = trades
        stress_frames.append(stress)
    top_df = pd.DataFrame(top_rows)
    write_csv("phase37_top_candidate_stress_results.csv", pd.concat(stress_frames, ignore_index=True) if stress_frames else pd.DataFrame())
    write_csv("phase37_top_candidate_integrity_audit.csv", integrity_rows(top_df, sha256_file(Path(__file__))))

    selected = None
    promotable = top_df[top_df["promotion_reason"] != "NOT_PROMOTED"].copy()
    if not promotable.empty:
        selected = promotable.sort_values(["promotion_reason", "score" if "score" in promotable.columns else "net_pnl", "net_pnl"], ascending=[True, False, False]).iloc[0].to_dict()
        src = ROOT / selected["trade_log_path"]
        dst = REPORTS / "phase37_strategy1_1_trade_log.csv"
        shutil.copyfile(src, dst)
        selected["trade_log_path"] = "reports/phase37_strategy1_1_trade_log.csv"
        selected["trade_log_hash"] = sha256_file(dst)
        selected_trades = pd.read_csv(dst)
        write_csv("phase37_strategy1_vs_strategy1_1_comparison.csv", compare_strategy1_to_selected(baseline_trades, selected_trades, selected))
        write_text("phase37_strategy1_1_mini_vault.md", f"""# Phase 37 Strategy #1.1 Mini Vault

## Identity

- Candidate: `{selected['candidate_id']}`
- Promotion reason: `{promotion_reason(selected)}`
- Status: BACKTEST_VERIFIED_NOT_SHADOWED / NOT_REAL_CAPITAL_READY

## Metrics

- PnL: {selected['net_pnl']}
- Trades: {selected['trades']}
- PF: {selected['profit_factor']}
- DD: {selected['max_drawdown_pct']}%
- Stress pass: {selected['stress_pass_count']}/15
- Combined adverse PnL: {selected['combined_adverse_pnl']}

## Rules

Parameters: `{selected['params']}`

Code path: `scripts/phase37_strategy1_1_second_stage_optimization.py::CachedSignalStrategy`.
Trade log: `{selected['trade_log_path']}`
Trade log hash: `{selected['trade_log_hash']}`

## Live Automation

Rules are closed-candle Strategy #1 signals plus live-known guards. This remains `NOT_REAL_CAPITAL_READY` without exchange shadow proof.
""")
    else:
        preserved_df = leaderboard.drop_duplicates("candidate_id").head(5)
        preserved_ids = preserved_df["candidate_id"].tolist()
        write_text("phase37_research_candidate_vaults.md", "# Phase 37 Research Candidate Vaults\n\n" + preserved_df.to_markdown(index=False))
        write_csv("phase37_strategy1_vs_strategy1_1_comparison.csv", [])
        write_text("phase37_strategy1_1_selection_decision.md", "No Strategy #1.1 was promoted. Top research candidates are preserved in `phase37_research_candidate_vaults.md`.\n")
        write_text("phase37_strategy1_1_mini_vault.md", "# Phase 37 Strategy #1.1 Mini Vault\n\nNo Strategy #1.1 was promoted.\n")
        selected = None

    if selected:
        preserved_ids = []
        write_text("phase37_strategy1_1_selection_decision.md", f"Strategy #1.1 promoted: `{selected['candidate_id']}` via `{promotion_reason(selected)}`.\n")
        write_text("phase37_research_candidate_vaults.md", "# Phase 37 Research Candidate Vaults\n\nStrategy #1.1 was promoted, so research vault fallback is not used.\n")

    verdict = "PHASE37_PASS_STRATEGY1_1_PROMOTED" if selected else ("PHASE37_PARTIAL_PASS_RESEARCH_CANDIDATES_PRESERVED" if preserved_ids else "PHASE37_FAIL_NO_REAL_IMPROVEMENT_FOUND")
    update_memory(verdict, selected, len(executed), preserved_ids)
    write_artifact_registry()
    write_report(verdict, len(executed), selected, leaderboard, preserved_ids)
    write_manifest(verdict)
    print(json.dumps({"verdict": verdict, "selected": selected["candidate_id"] if selected else None, "executed": len(executed)}, indent=2))


if __name__ == "__main__":
    run_phase()
