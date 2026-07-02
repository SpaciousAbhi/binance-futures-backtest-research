"""
Phase 29.3 precision-fusion lineage recovery.

The runner preserves old Variant B/C/PF1.2 reconstructed trade sets as teacher
evidence, then attempts live-known executable rebuilds through the backtest
engine. It does not promote reconstructed trade sets to live executable proof.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUTPUTS = ROOT.parents[1] / "outputs"
sys.path.insert(0, str(ROOT))

from src.backtest.engine import MultiPositionBacktestEngine
from src.research.phase12_runner import CAND_A_CFG, CAND_C_CFG, build_p10_1_strategy
from src.research.phase21_runner import reconstruct_pf12 as reconstruct_pf12_with_variants
from src.strategies.base import BaseStrategy
from src.strategies.candidates import UniversalStrategyTemplate
from scripts.phase29_1_truth_first_recovery import monthly_table, standard_stress
from scripts.phase29_2_precision_fusion_truth import (
    ENGINE_SETTINGS,
    RISK_SETTINGS,
    benchmark_matrix,
    candidate_registry,
    combined_adverse,
    enrich_dirty_trades,
    execute_candidates,
    load_btc_1h,
    metric_row,
    metrics_with_stress,
    multitimeframe_audit,
    no_lookahead_scan,
    pf12_lineage_map,
    run_engine,
    sha256_file,
    sleeve_standalone,
    trade_key_rows,
    write_csv,
    write_dirty_cluster_report,
    write_text,
)

REQUIRED_FILES = [
    "phase29_3_precision_fusion_lineage_recovery_and_pf8_rebuild_report.md",
    "phase29_3_variant_b_rebuild.csv",
    "phase29_3_variant_c_rebuild.csv",
    "phase29_3_pf12_fusion_lineage_map.csv",
    "phase29_3_pf12_executable_rebuild_trade_log.csv",
    "phase29_3_pf12_trade_diff_audit.csv",
    "phase29_3_precision_fusion_compiler_spec.md",
    "phase29_3_dirty_pf8_quality_surgery.csv",
    "phase29_3_recovered_candidate_registry.csv",
    "phase29_3_recovered_candidate_results.csv",
    "phase29_3_best_recovered_router_trade_log.csv",
    "phase29_3_benchmark_comparison_matrix.csv",
    "phase29_3_live_rule_audit.md",
    "phase29_3_audit_manifest.json",
]
EXTRA_FILES = [
    "phase29_3_pf12_executable_rebuild_monthly_table.csv",
    "phase29_3_best_recovered_router_monthly_table.csv",
    "phase29_3_best_recovered_router_stress_table.csv",
    "phase29_3_multitimeframe_data_audit.csv",
    "phase29_3_sleeve_standalone_results.csv",
    "phase29_3_no_lookahead_hardcoding_scan.csv",
]


class PrecisionFusionCompiler(BaseStrategy):
    def __init__(self, sleeves: list[tuple[str, Any, float, int]], max_positions: int = 1):
        super().__init__(
            name="phase29_3_precision_fusion_compiler",
            hypothesis="Deterministic Precision Fusion router with core priority, rescue gate, and conflict logging.",
        )
        self.sleeves = sleeves
        self.max_positions = max_positions
        self.rejected_signals: list[dict[str, Any]] = []
        self.conflicts: list[dict[str, Any]] = []

    def get_param_grid(self) -> dict:
        return {}

    @staticmethod
    def expected_r(sig: dict[str, Any], close_value: float) -> float:
        risk = abs(close_value - float(sig["stop_loss"]))
        reward = abs(float(sig["take_profit"]) - close_value)
        return reward / risk if risk > 0 else 0.0

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict | None = None) -> dict | None:
        if i < 250:
            return None
        close_value = float(df["close"].values[i])
        signals: list[dict[str, Any]] = []
        current_time = int(df["open_time"].values[i])
        for sleeve_name, sleeve, min_r, priority in self.sleeves:
            sig = sleeve.get_signal(df, i, live_metrics=live_metrics) if "live_metrics" in sleeve.get_signal.__code__.co_varnames else sleeve.get_signal(df, i)
            if sig is None:
                continue
            er = self.expected_r(sig, close_value)
            sig = dict(sig)
            sig["sleeve"] = sleeve_name
            sig["expected_r"] = er
            sig["priority"] = priority
            if er < min_r:
                self.rejected_signals.append(
                    {
                        "signal_time": current_time,
                        "sleeve": sleeve_name,
                        "side": sig.get("side"),
                        "expected_r": er,
                        "action": "rejected_expected_r",
                    }
                )
                continue
            signals.append(sig)
        if not signals:
            return None
        sides = {s["side"] for s in signals}
        if len(sides) > 1:
            self.conflicts.append({"signal_time": current_time, "conflict_type": "long_short", "candidates": len(signals)})
        signals.sort(key=lambda s: (-float(s["expected_r"]), int(s["priority"]), abs(close_value - float(s["stop_loss"]))))
        chosen = signals[0]
        if len(signals) > 1:
            self.conflicts.append({"signal_time": current_time, "conflict_type": "same_time_priority", "chosen": chosen["sleeve"], "candidates": len(signals)})
        chosen["reason"] = f"PF compiler {chosen['sleeve']}: {chosen.get('reason', '')}"
        chosen["strategy_name"] = chosen["sleeve"]
        return chosen


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def df_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(df.to_csv(index=False).encode("utf-8")).hexdigest()


def cfg_strategy(cfg: dict[str, Any]) -> UniversalStrategyTemplate:
    params = dict(cfg)
    params["bb_width_thresh"] = params.get("bb_width_thresh", 0.06)
    return UniversalStrategyTemplate(params)


def build_variant_rebuilds(df: pd.DataFrame) -> dict[str, Any]:
    floor = run_engine(df, build_p10_1_strategy())["trades"].copy()
    pf12_teacher, variant_b_teacher, variant_c_teacher = reconstruct_pf12_with_variants(floor.copy())

    variant_b_live = run_engine(df, cfg_strategy(CAND_A_CFG))["trades"].copy()
    variant_c_live = run_engine(df, cfg_strategy(CAND_C_CFG))["trades"].copy()

    b_rows = [
        metric_row("Variant B protected teacher/reference", "TEACHER_TRADESET_RECONSTRUCTED", variant_b_teacher, {"source": "phase17_3/phase21 reconstructed Variant B"}),
        metric_row("Variant B live-known executable proxy", "EXECUTABLE_PROXY_NOT_EXACT", variant_b_live, {"source": "CAND_A_CFG UniversalStrategyTemplate"}),
    ]
    c_rows = [
        metric_row("Variant C protected teacher/reference", "TEACHER_TRADESET_RECONSTRUCTED", variant_c_teacher, {"source": "phase17_3/phase21 reconstructed Variant C"}),
        metric_row("Variant C live-known executable proxy", "EXECUTABLE_PROXY_NOT_EXACT", variant_c_live, {"source": "CAND_C_CFG UniversalStrategyTemplate"}),
    ]
    write_csv(REPORTS / "phase29_3_variant_b_rebuild.csv", b_rows)
    write_csv(REPORTS / "phase29_3_variant_c_rebuild.csv", c_rows)
    return {
        "floor": floor,
        "pf12_teacher": pf12_teacher.copy(),
        "variant_b_teacher": variant_b_teacher.copy(),
        "variant_c_teacher": variant_c_teacher.copy(),
        "variant_b_live": variant_b_live,
        "variant_c_live": variant_c_live,
        "variant_b_rows": b_rows,
        "variant_c_rows": c_rows,
    }


def build_pf12_executable_rebuild(df: pd.DataFrame) -> tuple[pd.DataFrame, PrecisionFusionCompiler]:
    c_core = cfg_strategy(CAND_C_CFG)
    b_rescue = cfg_strategy(CAND_A_CFG)
    compiler = PrecisionFusionCompiler(
        [
            ("variant_c_core_live_proxy", c_core, 1.15, 1),
            ("variant_b_rescue_live_proxy", b_rescue, 1.40, 2),
        ]
    )
    result = run_engine(df, compiler)
    trades = result["trades"].copy()
    trades.to_csv(REPORTS / "phase29_3_pf12_executable_rebuild_trade_log.csv", index=False)
    write_csv(REPORTS / "phase29_3_pf12_executable_rebuild_monthly_table.csv", monthly_table(trades))
    write_csv(REPORTS / "phase29_3_pf12_compiler_rejected_signals.csv", compiler.rejected_signals)
    write_csv(REPORTS / "phase29_3_pf12_compiler_conflicts.csv", compiler.conflicts)
    return trades, compiler


def write_pf12_diff(teacher: pd.DataFrame, rebuilt: pd.DataFrame) -> str:
    teacher_keys = trade_key_rows(teacher)
    rebuilt_keys = trade_key_rows(rebuilt)
    missing = sorted(teacher_keys - rebuilt_keys)
    extra = sorted(rebuilt_keys - teacher_keys)
    common = len(teacher_keys & rebuilt_keys)
    t_metrics = metrics_with_stress(teacher)
    r_metrics = metrics_with_stress(rebuilt)
    pnl_gap = float(r_metrics["net_pnl"]) - float(t_metrics["net_pnl"])
    pf_gap = float(r_metrics["profit_factor"]) - float(t_metrics["profit_factor"])
    dd_gap = float(r_metrics["max_dd_pct"]) - float(t_metrics["max_dd_pct"])
    status = "PF12_PARTIAL_EXECUTABLE_REBUILD_REQUIRES_MORE_RECOVERY"
    if not missing and not extra and round(pnl_gap, 2) == 0:
        status = "PF12_EXECUTABLE_FUSION_EXACTLY_PROVEN"
    rows = [
        {
            "diff_type": "summary",
            "protected_trades": len(teacher),
            "rebuilt_trades": len(rebuilt),
            "common_keys": common,
            "missing_from_rebuild": len(missing),
            "extra_in_rebuild": len(extra),
            "pnl_gap": pnl_gap,
            "pf_gap": pf_gap,
            "dd_gap": dd_gap,
            "status": status,
        }
    ]
    for key in missing[:60]:
        rows.append({"diff_type": "missing_protected_key", "key": json.dumps(key), "status": status})
    for key in extra[:60]:
        rows.append({"diff_type": "extra_rebuilt_key", "key": json.dumps(key), "status": status})
    write_csv(REPORTS / "phase29_3_pf12_trade_diff_audit.csv", rows)
    return status


def write_compiler_spec() -> None:
    text = """# Phase 29.3 Precision Fusion Compiler Spec

PF means Precision Fusion: a deterministic compiler/router over multiple live-known sleeves.

## Required Behavior

- Accept multiple sleeve configs with explicit priority.
- Compute live-known expected R from current signal stop/target distance.
- Reject rescue signals below their expected-R gate.
- Resolve same-candle conflicts by expected R, fixed priority, then lower stop distance.
- Keep max concurrent positions controlled by `MultiPositionBacktestEngine(max_positions=1)`.
- Emit final trade log, rejected signal table, conflict table, monthly table, stress table, and manifest hash.
- Never convert teacher/reconstructed trade sets into executable proof.

## Phase 29.3 Compiler Instance

- Sleeve 1: `variant_c_core_live_proxy`, priority 1, expected-R gate 1.15.
- Sleeve 2: `variant_b_rescue_live_proxy`, priority 2, expected-R gate 1.40.
- Engine: `MultiPositionBacktestEngine`, max positions 1, cooldown 5.
"""
    write_text(REPORTS / "phase29_3_precision_fusion_compiler_spec.md", text)


def historical_map_text() -> str:
    return """## Phase 1 to Phase 29 Historical Recovery Map

| Phase Area | Claim / Workstream | Current Recovery Classification | Evidence |
|---|---|---|---|
| Phase 10-12 | Fusion-of-fusions floor using A/C/D/F/G candidates | Real executable floor, but not PF1.2 exact | `src/research/phase12_runner.py` |
| Phase 17.3 | Variant B, Variant C, PF1.2 B/C fusion | Reconstructed teacher trade sets; useful but not live-executable proof | `src/research/phase17_3_runner.py` |
| Phase 18-24 | Repair/search attempts around PF1.2 | Mostly research infrastructure and report comparisons | phase reports/tests |
| Phase 21-22 | Candidate registries and mechanism dataset | Real registry infrastructure; PF1.2 still reconstructed | `phase21_candidate_registry.csv` |
| Phase 25-28 | PF7/PF8/PF8.1 growth claims | Invalid as benchmarks because forced/synthetic metrics appear | Phase 29 audits |
| Phase 29-29.2 | Truth reset | PF1.2 exact as trade-set; executable exact fusion not proven | Phase 29.2 proof files |
"""


def dirty_surgery(df: pd.DataFrame) -> list[dict[str, Any]]:
    dirty_path = REPORTS / "phase29_1_dirty_pf8_recompute_trade_log.csv"
    dirty = pd.read_csv(dirty_path) if dirty_path.exists() else pd.DataFrame()
    rows = enrich_dirty_trades(dirty, df) if not dirty.empty else []
    write_csv(REPORTS / "phase29_3_dirty_pf8_quality_surgery.csv", rows)
    return rows


def write_candidate_outputs(df: pd.DataFrame, pf12_teacher_metrics: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None, pd.DataFrame]:
    registry = candidate_registry()
    write_csv(REPORTS / "phase29_3_recovered_candidate_registry.csv", registry)
    results, best, best_trades = execute_candidates(df, registry, pf12_teacher_metrics)
    write_csv(REPORTS / "phase29_3_recovered_candidate_results.csv", results)
    if best_trades is None or best_trades.empty:
        best_trades = pd.DataFrame(columns=["entry_time", "net_pnl", "side"])
    best_trades.to_csv(REPORTS / "phase29_3_best_recovered_router_trade_log.csv", index=False)
    write_csv(REPORTS / "phase29_3_best_recovered_router_monthly_table.csv", monthly_table(best_trades))
    write_csv(REPORTS / "phase29_3_best_recovered_router_stress_table.csv", standard_stress(best_trades))
    return results, best, best_trades


def write_benchmark_matrix(
    rebuilds: dict[str, Any],
    pf12_rebuilt: pd.DataFrame,
    dirty_rows: list[dict[str, Any]],
    best: dict[str, Any] | None,
) -> None:
    dirty_path = REPORTS / "phase29_1_dirty_pf8_recompute_trade_log.csv"
    dirty = pd.read_csv(dirty_path) if dirty_path.exists() else pd.DataFrame()
    systems = [
        ("Executable floor fusion", rebuilds["floor"]),
        ("Protected PF1.2 reconstructed trade set", rebuilds["pf12_teacher"]),
        ("Rebuilt Variant B executable proxy", rebuilds["variant_b_live"]),
        ("Rebuilt Variant C executable proxy", rebuilds["variant_c_live"]),
        ("Rebuilt PF1.2 executable fusion", pf12_rebuilt),
        ("Dirty PF8 no-forcing baseline", dirty),
    ]
    rows = []
    for name, trades in systems:
        m = metrics_with_stress(trades) if trades is not None and not trades.empty else {}
        rows.append(
            {
                "benchmark": name,
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
                "stress_pnl": m.get("combined_adverse", ""),
                "positive_months": m.get("positive_months", ""),
                "negative_months": m.get("negative_months", ""),
                "zero_months": m.get("zero_months", ""),
                "sleeve_contribution": "see lineage/compiler files",
                "conflict_count": "",
                "rejected_signal_count": "",
            }
        )
    if best:
        rows.append(
            {
                "benchmark": "Best real recovered PF8/PF8.1 candidate",
                "net_pnl": best.get("net_pnl", ""),
                "trades": best.get("trades", ""),
                "winning_trades": best.get("winners", ""),
                "losing_trades": best.get("losers", ""),
                "win_rate": best.get("win_rate", ""),
                "average_win": best.get("average_winner", ""),
                "average_loss": best.get("average_loser", ""),
                "expectancy": best.get("expectancy", ""),
                "profit_factor": best.get("profit_factor", ""),
                "max_dd_pct": best.get("max_dd_pct", ""),
                "stress_pnl": best.get("combined_adverse", ""),
                "positive_months": best.get("positive_months", ""),
                "negative_months": best.get("negative_months", ""),
                "zero_months": best.get("zero_months", ""),
                "sleeve_contribution": best.get("family", ""),
                "conflict_count": "",
                "rejected_signal_count": "",
            }
        )
    write_csv(REPORTS / "phase29_3_benchmark_comparison_matrix.csv", rows)


def write_live_audit(final_status: str) -> None:
    text = f"""# Phase 29.3 Live Rule Audit

## Rebuilt PF1.2

- Entry timing: closed-candle only in executable rebuild.
- Exit timing: engine-managed TP/SL/time handling.
- SL/TP: deterministic signal stop and target fields.
- Trailing/breakeven/time stop: only used where engine/sleeve exposes live-known fields.
- Same-candle SL/TP priority: inherited conservative backtest engine behavior.
- Tick/step/min-notional: modeled, not exchange-shadow verified.
- Funding handling: available as candle-aligned feature; no future funding used.
- Reduce-only exit concept: not exchange-tested.
- Max concurrent positions: 1.
- Cooldown: 5 candles.
- Exchange shadow readiness: not proven.

## Best Recovered PF8 Attempt

- Candidate metrics are assigned only to engine-executed rows.
- Unexecuted candidates remain blank-metric registry rows.
- Status: NOT_REAL_CAPITAL_READY.

Final live status: `{final_status}` and NOT_REAL_CAPITAL_READY. No real-capital readiness exists without exchange-level shadow/live proof.
"""
    write_text(REPORTS / "phase29_3_live_rule_audit.md", text)


def scan_new_runner() -> bool:
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden = [
        "29386" + ".59",
        "30580" + ".40",
        "31250" + ".80",
        ".sam" + "ple(",
        "is_" + "winner",
        "future_" + "pnl",
        "future_" + "mfe",
        "future_" + "mae",
        "selected_" + "trade_ids",
    ]
    if any(item in source for item in forbidden):
        return False
    tree = ast.parse(source)
    forbidden_targets = {
        "diff" + "_pnl",
        "forced" + "_pnl",
        "pnl" + "_70",
        "pnl" + "_80",
        "pnl" + "_81",
        "pf" + "_70",
        "pf" + "_80",
        "pf" + "_81",
        "dd" + "_70",
        "dd" + "_80",
        "dd" + "_81",
    }
    assigned = set()
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                assigned.add(target.id)
    return not (assigned & forbidden_targets)


def choose_status(pf12_status: str, best: dict[str, Any] | None) -> str:
    if not scan_new_runner():
        return "AUDIT_FAIL_FORCED_METRICS_REMAIN"
    if pf12_status == "PF12_EXECUTABLE_FUSION_EXACTLY_PROVEN":
        return "PF12_EXECUTABLE_FUSION_EXACTLY_PROVEN_AND_REAL_PF8_RECOVERED" if best and best.get("beats_pf12") == "YES" else "PF12_EXECUTABLE_FUSION_EXACTLY_PROVEN_BUT_PF8_RECOVERY_RESEARCH_ONLY"
    return "PF12_PARTIAL_EXECUTABLE_REBUILD_REQUIRES_MORE_RECOVERY"


def write_main_report(
    final_status: str,
    rebuilds: dict[str, Any],
    pf12_rebuilt: pd.DataFrame,
    pf12_status: str,
    candidate_results: list[dict[str, Any]],
    best: dict[str, Any] | None,
    mtf_rows: list[dict[str, Any]],
) -> None:
    b_teacher = rebuilds["variant_b_rows"][0]
    c_teacher = rebuilds["variant_c_rows"][0]
    b_live = rebuilds["variant_b_rows"][1]
    c_live = rebuilds["variant_c_rows"][1]
    pf12_teacher_m = metrics_with_stress(rebuilds["pf12_teacher"])
    pf12_live_m = metrics_with_stress(pf12_rebuilt)
    executed = len([r for r in candidate_results if r.get("status") == "EXECUTED_ENGINE"])
    best_line = "No best candidate" if not best else f"{best['candidate_id']} / {best['family']} / PnL {float(best['net_pnl']):.2f} / trades {int(float(best['trades']))} / PF {float(best['profit_factor']):.2f}"
    btc_5m = next((r for r in mtf_rows if r["asset"] == "BTCUSDT" and r["timeframe"] == "5m"), {})
    text = f"""# Phase 29.3 Precision Fusion Lineage Recovery and PF8 Rebuild Report

**FINAL VERDICT: {final_status}**

PF means Precision Fusion: a router of candidates, sleeves, filters, rescue layers, and risk rules. This phase is recovery-focused: it preserves old B/C/PF1.2 work as teacher evidence while rebuilding live-known executable approximations through the engine.

{historical_map_text()}

## Variant B Recovery

Variant B first appears as the consistency benchmark in the Phase 17.3 B/C fusion repair path. The protected B result is a reconstructed teacher trade set, not a saved live executable strategy.

| Metric | Protected B teacher | Live-known B proxy |
|---|---:|---:|
| PnL | {float(b_teacher['net_pnl']):.2f} | {float(b_live['net_pnl']):.2f} |
| Trades | {int(b_teacher['trades'])} | {int(b_live['trades'])} |
| PF | {float(b_teacher['profit_factor']):.2f} | {float(b_live['profit_factor']):.2f} |
| DD % | {float(b_teacher['max_dd_pct']):.2f} | {float(b_live['max_dd_pct']):.2f} |
| Stress | {float(b_teacher['combined_adverse']):.2f} | {float(b_live['combined_adverse']):.2f} |

## Variant C Recovery

Variant C was the quality core teacher set. The live-known proxy uses the C candidate config from Phase 12, but it does not exactly regenerate the reconstructed C teacher rows.

| Metric | Protected C teacher | Live-known C proxy |
|---|---:|---:|
| PnL | {float(c_teacher['net_pnl']):.2f} | {float(c_live['net_pnl']):.2f} |
| Trades | {int(c_teacher['trades'])} | {int(c_live['trades'])} |
| PF | {float(c_teacher['profit_factor']):.2f} | {float(c_live['profit_factor']):.2f} |
| DD % | {float(c_teacher['max_dd_pct']):.2f} | {float(c_live['max_dd_pct']):.2f} |
| Stress | {float(c_teacher['combined_adverse']):.2f} | {float(c_live['combined_adverse']):.2f} |

## How Variant C + Variant B Became PF1.2

The recovered source trail shows Variant C as the 318-trade quality teacher set. PF1.2 then adds a small B-rescue overlay selected from B-unique teacher rows. The historical implementation used completed trade transformations and completed trade `R`, so it is teacher evidence rather than live-safe executable proof.

## PF1.2 Executable Fusion Rebuild

Status: `{pf12_status}`.

| Metric | Protected PF1.2 teacher | Rebuilt executable PF1.2 |
|---|---:|---:|
| PnL | {float(pf12_teacher_m['net_pnl']):.2f} | {float(pf12_live_m['net_pnl']):.2f} |
| Trades | {int(pf12_teacher_m['trades'])} | {int(pf12_live_m['trades'])} |
| PF | {float(pf12_teacher_m['profit_factor']):.2f} | {float(pf12_live_m['profit_factor']):.2f} |
| DD % | {float(pf12_teacher_m['max_dd_pct']):.2f} | {float(pf12_live_m['max_dd_pct']):.2f} |
| Stress | {float(pf12_teacher_m['combined_adverse']):.2f} | {float(pf12_live_m['combined_adverse']):.2f} |

## Why $8426 vs $21684 Happens

The executable floor path evaluates live candle signals and accepts 490 raw engine trades. The protected PF1.2 teacher path removes many completed low-quality floor trades, reconstructs Variant B and C from completed trade logs, shifts entries, and adds only a small B-rescue set. That selection uses information available only after trade completion, so it explains the quality jump but cannot be used directly in live routing.

## Dirty PF8 Surgery

Dirty PF8 is retained as research material only. It is audited trade by trade in `phase29_3_dirty_pf8_quality_surgery.csv`. The goal is to learn live-known filters, not to remove historical losing rows by hindsight.

## Real PF7/PF8/PF8.1 Recovery Attempt

Registered candidates: 1000. Engine-executed candidates: {executed}. Best engine-executed recovery attempt: {best_line}. It does not supersede protected PF1.2 unless the candidate table says `beats_pf12=YES`.

## Multi-Timeframe Recovery

BTC 5m availability: {btc_5m.get('exists', '')}. If missing, 5m trigger proof remains blocked. BTC 15m is audited in the multi-timeframe table and can be used in a later rebuild.

## What Was Reusable vs Not Live-Safe

Reusable: closed-candle candidate configs, FusionOfFusions routing concepts, expected-R gates, session/funding filters, VWAP/retest/breakout sleeves, deterministic compiler outputs.

Not live-safe as strategy logic: completed trade PnL ranking, completed trade `R` selection, synthetic entry shifting, report-only PF7/PF8/PF8.1 constants, and any forced metric assignment.

## Phase 29.4 Work

Rebuild Variant C and B rescue from first-principles candle features instead of teacher trade transformations. Use BTC 15m confirmation where available, regenerate BTC 5m if the downloader supports it, and train live-known filters against teacher clusters without using outcome labels in the final router.
"""
    write_text(REPORTS / "phase29_3_precision_fusion_lineage_recovery_and_pf8_rebuild_report.md", text)


def write_manifest(final_status: str) -> None:
    files: dict[str, Any] = {}
    for name in REQUIRED_FILES + EXTRA_FILES:
        if name == "phase29_3_audit_manifest.json":
            continue
        path = REPORTS / name
        if path.exists():
            files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    manifest = {
        "phase": "29.3",
        "final_verdict": final_status,
        "repo_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "files": files,
        "manifest_hash_note": "Manifest excludes self hash.",
    }
    write_text(REPORTS / "phase29_3_audit_manifest.json", json.dumps(manifest, indent=2) + "\n")
    if OUTPUTS.exists():
        for name in REQUIRED_FILES + EXTRA_FILES:
            src = REPORTS / name
            if src.exists():
                (OUTPUTS / name).write_bytes(src.read_bytes())


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    df = load_btc_1h()
    rebuilds = build_variant_rebuilds(df)
    write_csv(REPORTS / "phase29_3_pf12_fusion_lineage_map.csv", pf12_lineage_map())
    pf12_rebuilt, compiler = build_pf12_executable_rebuild(df)
    pf12_status = write_pf12_diff(rebuilds["pf12_teacher"], pf12_rebuilt)
    write_compiler_spec()
    dirty_rows = dirty_surgery(df)
    write_dirty_cluster_report(dirty_rows)
    mtf_rows = multitimeframe_audit()
    write_csv(REPORTS / "phase29_3_multitimeframe_data_audit.csv", mtf_rows)
    sleeve_rows = sleeve_standalone(df)
    write_csv(REPORTS / "phase29_3_sleeve_standalone_results.csv", sleeve_rows)
    pf12_teacher_metrics = metrics_with_stress(rebuilds["pf12_teacher"])
    candidate_results, best, best_trades = write_candidate_outputs(df, pf12_teacher_metrics)
    scan_rows = no_lookahead_scan()
    write_csv(REPORTS / "phase29_3_no_lookahead_hardcoding_scan.csv", scan_rows)
    write_benchmark_matrix(rebuilds, pf12_rebuilt, dirty_rows, best)
    final_status = choose_status(pf12_status, best)
    write_live_audit(final_status)
    write_main_report(final_status, rebuilds, pf12_rebuilt, pf12_status, candidate_results, best, mtf_rows)
    write_manifest(final_status)
    print(json.dumps({"final_verdict": final_status, "executed_candidates": len([r for r in candidate_results if r.get("status") == "EXECUTED_ENGINE"])}, indent=2))


if __name__ == "__main__":
    main()
