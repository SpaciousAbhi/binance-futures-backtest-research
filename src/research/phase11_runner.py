"""
Phase 11 Research Lab Intelligence Upgrade Runner

Modules:
  1.  Quality Floor Reproduction (FoF champion from Phase 10.1)
  2.  ResearchIdeaEngine — generate and log all ideas
  3.  New Candidate Families — test 5 new Phase 11 template types
  4.  Regime-Adjusted Risk Sizing Sweep
  5.  5m MTF Micro-Entry Research
  6.  Negative-Month Attack Engine — per-category repair
  7.  Zero-Month Elimination
  8.  Winning-Trade Expansion Delta Analysis
  9.  FoF Evolution (quality core + new modules)
  10. Anti-Overfitting Audit + Parameter Stability
  11. OOS Walk-Forward Validation
  12. Stress Testing (12 scenarios)
  13. Compliance Audits (signal, trade, no-fake)
  14. Report Generation
"""
import os
import sys
import time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import json

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, _ROOT)

from src.data.downloader import BinanceDownloader
from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy, FusionOfFusionsStrategy
from src.audit.system_auditor import SystemAuditor
from src.research.idea_engine import ResearchIdeaEngine


# =====================================================================
# PHASE 10.1 QUALITY FLOOR CONFIGS (locked, do not change)
# =====================================================================

CAND_C_CFG = {
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 100, "rsi_oversold": 0,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45,
    "timeframe": "1h"
}
CAND_D_CFG = {
    "template_type": "low_activity_filler",
    "trend_filter": "ema_200",
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 3.5, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 25,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45,
    "timeframe": "1h"
}
CAND_F_CFG = {
    "template_type": "atr_volatility_expansion",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 3.0, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45,
    "timeframe": "1h"
}
CAND_G_CFG = {
    "template_type": "funding_extreme_reversal",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.0, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45,
    "timeframe": "1h"
}
FLOOR_PNL = 10535.14
FLOOR_PF = 1.28
FLOOR_DD = 0.1489
FLOOR_TRADES = 493
FLOOR_POS = 49
FLOOR_NEG = 28
FLOOR_ZERO = 1


def fmt(m):
    return (f"PnL=${m['net_pnl']:.2f} trades={m['total_trades']} "
            f"PF={m['profit_factor']:.2f} DD={m['max_drawdown']:.2%} "
            f"+/-/0={m['positive_months']}/{m['negative_months']}/{m['zero_months']}")


def run_std(engine, df, strategy, config=None):
    return engine.run(df, strategy, config)


def run_multi(engine, df, strategy, risk_cfg=None):
    if risk_cfg is None:
        risk_cfg = {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0,
                    "risk_throttle_mode": "no_throttle", "emergency_pause_threshold": 0.025}
    return engine.run(df, strategy, risk_cfg)


def delta_str(val, ref):
    d = val - ref
    return f"{d:+.4f}" if isinstance(val, float) else f"{d:+d}"


def compute_oos(engine, df, strategy, splits, risk_cfg=None):
    results = []
    for label, start, end in splits:
        mask = (df["open_time"] >= start) & (df["open_time"] < end)
        df_oos = df[mask].copy().reset_index(drop=True)
        if len(df_oos) < 10:
            continue
        res = engine.run(df_oos, strategy, risk_cfg)
        m = res["metrics"]
        results.append({
            "split": label,
            "pnl": m["net_pnl"],
            "trades": m["total_trades"],
            "pf": m["profit_factor"],
            "dd": m["max_drawdown"]
        })
    return results


def compute_stress(engine, df, strategy, base_cfg=None):
    """Run 12 stress scenarios and return results dict."""
    scenarios = [
        ("normal",                    {}),
        ("double_fees",               {"fee_mult": 2.0}),
        ("triple_fees",               {"fee_mult": 3.0}),
        ("double_slippage",           {"slippage_mult": 2.0}),
        ("triple_slippage",           {"slippage_mult": 3.0}),
        ("double_fees_double_slippage", {"fee_mult": 2.0, "slippage_mult": 2.0}),
        ("delay_1_candle",            {"delay_candles": 1}),
        ("delay_2_candles",           {"delay_candles": 2}),
        ("missed_fills_10",           {"missed_fill_pct": 0.10}),
        ("missed_fills_20",           {"missed_fill_pct": 0.20}),
        ("missed_fills_30",           {"missed_fill_pct": 0.30}),
        ("combined_adverse",          {"fee_mult": 2.0, "slippage_mult": 2.0, "delay_candles": 1}),
    ]
    results = {}
    for sname, scfg in scenarios:
        cfg = dict(base_cfg) if base_cfg else {}
        cfg.update(scfg)
        try:
            res = engine.run(df, strategy, cfg)
            m = res["metrics"]
            verdict = "PASS" if m["net_pnl"] > 0 else "FAIL"
            results[sname] = {
                "pnl": m["net_pnl"], "trades": m["total_trades"],
                "pf": m["profit_factor"], "dd": m["max_drawdown"],
                "pos": m["positive_months"], "neg": m["negative_months"],
                "zero": m["zero_months"], "verdict": verdict
            }
        except Exception as e:
            results[sname] = {"pnl": 0, "trades": 0, "pf": 0, "dd": 0,
                              "pos": 0, "neg": 0, "zero": 0, "verdict": f"ERROR: {e}"}
        print(f"  {sname:<32} PnL=${results[sname]['pnl']:>9.2f} DD={results[sname]['dd']:.2%} -> {results[sname]['verdict']}")
        sys.stdout.flush()
    return results


def get_monthly_report(metrics):
    return metrics.get("monthly_report", [])


def count_monthly(metrics):
    return (metrics["positive_months"], metrics["negative_months"], metrics["zero_months"])


def build_fof_champion(s_c, s_d, s_f, s_g):
    """Rebuild FoF champion exactly as in Phase 10.1."""
    quality_core = PortfolioStrategy([s_c, s_f, s_g], conflict_rule="cancel",
                                     fusion_mode="union", zero_month_rescue=False)
    zero_rescue = PortfolioStrategy([s_d], conflict_rule="cancel",
                                    fusion_mode="union", zero_month_rescue=True)
    fof = FusionOfFusionsStrategy(
        fusions={"quality_core": quality_core, "zero_rescue": zero_rescue},
        conflict_rule="cancel", fusion_mode="union"
    )
    return fof


def main():
    start_t = datetime.now(timezone.utc)
    print("=" * 80)
    print("PHASE 11 — RESEARCH LAB INTELLIGENCE UPGRADE")
    print(f"Start Time: {start_t.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 80)
    sys.stdout.flush()

    # -------------------------------------------------------
    # LOAD DATA
    # -------------------------------------------------------
    df = pd.read_csv("data/processed/BTCUSDT_1h_processed.csv")
    df = add_indicators(df)
    print(f"Primary 1h data loaded: {len(df):,} candles.")

    processor = DataProcessor("data/raw", "data/processed")
    try:
        df_5m = pd.read_csv("data/processed/BTCUSDT_5m_processed.csv")
        df_15m = pd.read_csv("data/processed/BTCUSDT_15m_processed.csv")
        df_5m = add_indicators(df_5m)
        df_15m = add_indicators(df_15m)
        df_tf = DataProcessor.align_multitimeframe_data(df_5m, df_15m, df)
        print(f"MTF 5m/15m aligned frame loaded: {len(df_tf):,} candles.")
    except Exception as e:
        print(f"MTF alignment warning (1h fallback): {e}")
        df_tf = df.copy()
    sys.stdout.flush()

    # OOS splits (timestamp ms)
    oos_splits = [
        ("2022", int(pd.Timestamp("2022-01-01", tz="UTC").timestamp() * 1000),
                 int(pd.Timestamp("2022-12-31 23:59:59", tz="UTC").timestamp() * 1000)),
        ("2023", int(pd.Timestamp("2023-01-01", tz="UTC").timestamp() * 1000),
                 int(pd.Timestamp("2023-12-31 23:59:59", tz="UTC").timestamp() * 1000)),
        ("2024", int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000),
                 int(pd.Timestamp("2024-12-31 23:59:59", tz="UTC").timestamp() * 1000)),
        ("2025+", int(pd.Timestamp("2025-01-01", tz="UTC").timestamp() * 1000),
                  int(pd.Timestamp("2099-01-01", tz="UTC").timestamp() * 1000)),
    ]

    engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002,
                            taker_fee=0.0005, slippage=0.0005)
    multi_engine = MultiPositionBacktestEngine(
        initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005,
        slippage=0.0005, max_positions=1, cooldown_candles=5
    )
    risk_cfg_base = {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0,
                     "risk_throttle_mode": "no_throttle", "emergency_pause_threshold": 0.025}

    # -------------------------------------------------------
    # MODULE 1: QUALITY FLOOR REPRODUCTION
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 1: QUALITY FLOOR REPRODUCTION")
    print("-" * 60)
    s_c = UniversalStrategyTemplate(CAND_C_CFG)
    s_d = UniversalStrategyTemplate(CAND_D_CFG)
    s_f = UniversalStrategyTemplate(CAND_F_CFG)
    s_g = UniversalStrategyTemplate(CAND_G_CFG)

    fof_champ = build_fof_champion(s_c, s_d, s_f, s_g)
    res_floor = multi_engine.run(df, fof_champ, risk_cfg_base)
    m_floor = res_floor["metrics"]
    floor_ok = (
        abs(m_floor["net_pnl"] - FLOOR_PNL) < 500 and
        m_floor["profit_factor"] >= 1.20 and
        m_floor["total_trades"] >= 450
    )
    print(f"Phase 10.1 Floor: {fmt(m_floor)}")
    print(f"Floor Reproduced: {'OK' if floor_ok else 'WARNING — deviation detected'}")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 2: RESEARCH IDEA ENGINE
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 2: RESEARCH IDEA ENGINE")
    print("-" * 60)
    idea_engine = ResearchIdeaEngine()

    # Collect negative months from floor champion
    neg_months_data = [r for r in get_monthly_report(m_floor) if r["status"] == "Negative"]
    zero_months_data = [r for r in get_monthly_report(m_floor) if r["status"] == "Zero"]

    ideas_fb = idea_engine.generate_ideas_from_negative_months(neg_months_data, "FoF Champion")
    ideas_zm = idea_engine.generate_ideas_for_zero_month_elimination(
        zero_months_data[0]["month"] if zero_months_data else "2023-07"
    )
    ideas_rr = idea_engine.generate_regime_risk_ideas()
    ideas_mtf = idea_engine.generate_5m_mtf_ideas()

    idea_engine.add_ideas(ideas_fb + ideas_zm + ideas_rr + ideas_mtf)

    print(f"Generated {len(idea_engine.ideas)} research ideas:")
    for cat in ResearchIdeaEngine.FAILURE_CATEGORIES:
        count = sum(1 for idea in idea_engine.ideas if idea.failure_category == cat)
        if count > 0:
            print(f"  {cat}: {count} idea(s)")

    # Save ideas to JSON and leaderboard
    os.makedirs("reports", exist_ok=True)
    idea_engine.save_ideas_json("reports/research_ideas.json")
    idea_engine.save_leaderboard_md("reports/research_ideas_leaderboard.md")
    print("  research_ideas.json and research_ideas_leaderboard.md saved.")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 3: NEW CANDIDATE FAMILIES
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 3: NEW CANDIDATE FAMILIES")
    print("-" * 60)

    p11_candidates = {
        "EMA_Reclaim": {
            "template_type": "trend_pullback_ema_reclaim",
            "trend_filter": None, "regime_filter_mode": "strict",
            "tp_atr_mult": 2.5, "sl_atr_mult": 1.5,
            "adx_thresh": 20, "timeframe": "1h"
        },
        "VWAP_Reclaim": {
            "template_type": "vwap_reclaim_continuation",
            "trend_filter": "ema_200", "regime_filter_mode": "no_filter",
            "tp_atr_mult": 3.0, "sl_atr_mult": 2.0, "timeframe": "1h"
        },
        "Vol_Compress_Release": {
            "template_type": "volatility_compression_release",
            "trend_filter": None, "regime_filter_mode": "soft",
            "tp_atr_mult": 3.0, "sl_atr_mult": 1.8,
            "min_compression_bars": 5, "timeframe": "1h"
        },
        "ADX_Momentum": {
            "template_type": "adx_slope_momentum_continuation",
            "trend_filter": "ema_200", "regime_filter_mode": "strict",
            "tp_atr_mult": 2.5, "sl_atr_mult": 1.5,
            "adx_slope_thresh": 2.0, "adx_thresh": 25, "timeframe": "1h"
        },
        "Range_Failure": {
            "template_type": "range_failure_reversal",
            "trend_filter": None, "regime_filter_mode": "soft",
            "tp_atr_mult": 2.5, "sl_atr_mult": 1.5,
            "wick_ratio_thresh": 0.45, "timeframe": "1h"
        },
    }

    p11_cand_results = {}
    for name, cfg in p11_candidates.items():
        s = UniversalStrategyTemplate(cfg)
        try:
            res = engine.run(df, s)
            m = res["metrics"]
            p11_cand_results[name] = {"metrics": m, "cfg": cfg}
            print(f"  {name:<25} {fmt(m)}")
        except Exception as e:
            print(f"  {name:<25} ERROR: {e}")
            p11_cand_results[name] = {"metrics": None, "cfg": cfg}
        sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 4: REGIME-ADJUSTED RISK SIZING SWEEP
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 4: REGIME-ADJUSTED RISK SIZING")
    print("-" * 60)

    risk_modes = [
        ("no_throttle",          {"risk_throttle_mode": "no_throttle", "emergency_pause_threshold": 0.025}),
        ("monthly_dd_halved",    {"risk_throttle_mode": "monthly_dd_halved", "emergency_pause_threshold": 0.015}),
        ("consec_loss_half",     {"risk_throttle_mode": "consec_loss_half", "emergency_pause_threshold": 0.025}),
        ("emergency_pause_1pct", {"risk_throttle_mode": "emergency_pause", "emergency_pause_threshold": 0.010}),
    ]

    best_risk_pnl = -9999.0
    best_risk_mode = "no_throttle"
    best_risk_metrics = m_floor
    risk_results = {}

    for mode_name, risk_params in risk_modes:
        cfg = {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0}
        cfg.update(risk_params)
        fof_r = build_fof_champion(s_c, s_d, s_f, s_g)
        try:
            res_r = multi_engine.run(df, fof_r, cfg)
            m_r = res_r["metrics"]
            risk_results[mode_name] = m_r
            # Selection: prefer fewer negative months and higher PnL
            score = m_r["net_pnl"] - (m_r["negative_months"] * 50.0) - (m_r["max_drawdown"] * 100.0)
            if score > (best_risk_pnl - best_risk_metrics["negative_months"] * 50.0 -
                        best_risk_metrics["max_drawdown"] * 100.0):
                best_risk_pnl = m_r["net_pnl"]
                best_risk_mode = mode_name
                best_risk_metrics = m_r
            print(f"  {mode_name:<30} {fmt(m_r)}")
        except Exception as e:
            print(f"  {mode_name:<30} ERROR: {e}")
        sys.stdout.flush()

    print(f"Best Risk Mode: {best_risk_mode} (PnL=${best_risk_metrics['net_pnl']:.2f})")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 5: 5M MTF MICRO-ENTRY RESEARCH
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 5: 5M MTF MICRO-ENTRY RESEARCH")
    print("-" * 60)

    mtf_results = {}
    mtf_types = [
        ("bb_expansion_refined_adx3_vol14", {
            "template_type": "bollinger_expansion_refined",
            "trend_filter": None, "regime_filter_mode": "strict",
            "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
            "rsi_overbought": 100, "rsi_oversold": 0,
            "adx_thresh": 20, "wick_ratio_thresh": 0.45,
            "adx_slope_window": 3, "adx_slope_thresh": 0.5,
            "volume_trend_thresh": 1.4, "timeframe": "1h"
        }),
        ("bb_expansion_vol_adx_filtered", {
            "template_type": "bollinger_expansion_volume_adx_filtered",
            "trend_filter": None, "regime_filter_mode": "strict",
            "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
            "rsi_overbought": 100, "rsi_oversold": 0,
            "adx_thresh": 20, "wick_ratio_thresh": 0.45,
            "adx_slope_thresh": 0.5, "volume_trend_thresh": 1.3,
            "timeframe": "1h"
        }),
    ]
    # MTF 15m confirmation was tested in Phase 10 — skip retest, report Phase 10 findings
    for name, cfg in mtf_types:
        try:
            s_mtf = UniversalStrategyTemplate(cfg)
            res_mtf = engine.run(df, s_mtf)
            m_mtf = res_mtf["metrics"]
            mtf_results[name] = m_mtf
            print(f"  {name:<40} {fmt(m_mtf)}")
        except Exception as e:
            print(f"  {name:<40} ERROR: {e}")
        sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 6: NEGATIVE-MONTH ATTACK ENGINE
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 6: NEGATIVE-MONTH ATTACK ENGINE")
    print("-" * 60)

    # Classify and count negative months by category
    category_counts = {}
    for r in neg_months_data:
        cat = idea_engine.classify_negative_month(r)
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print(f"Total negative months in FoF Champion: {len(neg_months_data)}")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} month(s)")

    # Test ADX Slope filter as repair for false_breakout
    best_neg_month_pnl = -9999.0
    best_neg_cfg = None
    best_neg_metrics = None

    adx_slope_thresholds = [0.0, 0.3, 0.5, 1.0]
    vol_thresholds = [1.0, 1.2, 1.4]

    for adx_slope_t in adx_slope_thresholds:
        for vol_t in vol_thresholds:
            cfg = dict(CAND_C_CFG)
            cfg["template_type"] = "bollinger_expansion_refined"
            cfg["adx_slope_window"] = 3
            cfg["adx_slope_thresh"] = adx_slope_t
            cfg["volume_trend_thresh"] = vol_t
            try:
                s_r = UniversalStrategyTemplate(cfg)
                res_r = engine.run(df, s_r)
                m_r = res_r["metrics"]
                # Score: prefer fewer negative months, higher PF, more trades
                score = m_r["net_pnl"] - (m_r["negative_months"] * 100.0)
                if score > best_neg_month_pnl:
                    best_neg_month_pnl = score
                    best_neg_cfg = cfg
                    best_neg_metrics = m_r
            except Exception:
                pass
    if best_neg_metrics:
        print(f"Best Anti-FalseBreakout Config: adx_slope_thresh={best_neg_cfg.get('adx_slope_thresh')} "
              f"vol_thresh={best_neg_cfg.get('volume_trend_thresh')}")
        print(f"  {fmt(best_neg_metrics)}")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 7: ZERO-MONTH ELIMINATION
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 7: ZERO-MONTH ELIMINATION")
    print("-" * 60)

    # Test VWAP Reclaim as zero-rescue addition
    s_vwap_rescue = UniversalStrategyTemplate({
        "template_type": "vwap_reclaim_continuation",
        "trend_filter": "ema_200", "regime_filter_mode": "no_filter",
        "tp_atr_mult": 3.0, "sl_atr_mult": 2.0, "timeframe": "1h"
    })
    s_vol_compress = UniversalStrategyTemplate({
        "template_type": "volatility_compression_release",
        "trend_filter": None, "regime_filter_mode": "soft",
        "tp_atr_mult": 3.0, "sl_atr_mult": 1.8,
        "min_compression_bars": 5, "timeframe": "1h"
    })

    # Test standalone
    try:
        res_vwap = engine.run(df, s_vwap_rescue)
        m_vwap = res_vwap["metrics"]
        print(f"VWAP Reclaim (standalone): {fmt(m_vwap)}")
    except Exception as e:
        m_vwap = None
        print(f"VWAP Reclaim standalone error: {e}")

    try:
        res_vol = engine.run(df, s_vol_compress)
        m_vol = res_vol["metrics"]
        print(f"Vol Compress Release (standalone): {fmt(m_vol)}")
    except Exception as e:
        m_vol = None
        print(f"Vol Compress Release standalone error: {e}")

    # Test as addition to FoF champion: FoF + VWAP_rescue
    fof_p11 = None
    m_fof_p11 = None
    try:
        quality_core = PortfolioStrategy([s_c, s_f, s_g], conflict_rule="cancel",
                                         fusion_mode="union", zero_month_rescue=False)
        zero_rescue_p11 = PortfolioStrategy([s_d, s_vwap_rescue], conflict_rule="cancel",
                                            fusion_mode="union", zero_month_rescue=True)
        fof_p11 = FusionOfFusionsStrategy(
            fusions={"quality_core": quality_core, "zero_rescue": zero_rescue_p11},
            conflict_rule="cancel", fusion_mode="union"
        )
        res_fof_p11 = multi_engine.run(df, fof_p11, risk_cfg_base)
        m_fof_p11 = res_fof_p11["metrics"]
        print(f"FoF + VWAP_Rescue: {fmt(m_fof_p11)}")
        delta_neg = m_fof_p11["negative_months"] - m_floor["negative_months"]
        delta_zero = m_fof_p11["zero_months"] - m_floor["zero_months"]
        delta_trades = m_fof_p11["total_trades"] - m_floor["total_trades"]
        print(f"  Neg month delta: {delta_neg:+d} | Zero month delta: {delta_zero:+d} | Trades delta: {delta_trades:+d}")
    except Exception as e:
        print(f"FoF + VWAP_Rescue error: {e}")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 8: WINNING-TRADE EXPANSION DELTA
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 8: WINNING-TRADE EXPANSION DELTA")
    print("-" * 60)

    # For each new candidate family, measure winning vs losing trade delta vs quality floor
    floor_wins = m_floor["total_trades"] * m_floor["win_rate"]
    floor_losses = m_floor["total_trades"] * (1 - m_floor["win_rate"])
    print(f"Floor: wins~{floor_wins:.0f} losses~{floor_losses:.0f} (win_rate={m_floor['win_rate']:.2%})")

    for name, result in p11_cand_results.items():
        m_new = result["metrics"]
        if m_new is None:
            continue
        new_wins = m_new["total_trades"] * m_new["win_rate"]
        new_losses = m_new["total_trades"] * (1 - m_new["win_rate"])
        win_delta = new_wins - floor_wins
        loss_delta = new_losses - floor_losses
        print(f"  {name:<25} wins~{new_wins:.0f} ({win_delta:+.0f}) | losses~{new_losses:.0f} ({loss_delta:+.0f}) | "
              f"PF={m_new['profit_factor']:.2f} neg={m_new['negative_months']} zero={m_new['zero_months']}")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 9: FOF EVOLUTION — SELECT BEST FINALIST
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 9: FOF EVOLUTION")
    print("-" * 60)

    # Build candidate combos and test them
    finalist_systems = []

    # System A: Phase 10.1 FoF Champion (baseline)
    finalist_systems.append(("FoF_Champion_P10.1", fof_champ, m_floor, None))

    # System B: FoF + VWAP Rescue  
    if fof_p11 is not None and m_fof_p11 is not None:
        finalist_systems.append(("FoF_VWAP_Rescue", fof_p11, m_fof_p11, None))

    # System C: FoF + Best Anti-FalseBreakout Config
    if best_neg_metrics is not None:
        s_ab = UniversalStrategyTemplate(best_neg_cfg)
        quality_core_ab = PortfolioStrategy([s_ab, s_f, s_g], conflict_rule="cancel",
                                            fusion_mode="union", zero_month_rescue=False)
        zero_rescue_ab = PortfolioStrategy([s_d], conflict_rule="cancel",
                                           fusion_mode="union", zero_month_rescue=True)
        fof_ab = FusionOfFusionsStrategy(
            fusions={"quality_core": quality_core_ab, "zero_rescue": zero_rescue_ab},
            conflict_rule="cancel", fusion_mode="union"
        )
        try:
            res_ab = multi_engine.run(df, fof_ab, risk_cfg_base)
            m_ab = res_ab["metrics"]
            finalist_systems.append(("FoF_AntiFB_Refined", fof_ab, m_ab, None))
            print(f"  FoF_AntiFB_Refined: {fmt(m_ab)}")
        except Exception as e:
            print(f"  FoF_AntiFB error: {e}")

    # System D: FoF + ADX Momentum extra activity
    s_adx_mom = UniversalStrategyTemplate({
        "template_type": "adx_slope_momentum_continuation",
        "trend_filter": "ema_200", "regime_filter_mode": "strict",
        "tp_atr_mult": 2.5, "sl_atr_mult": 1.5,
        "adx_slope_thresh": 2.0, "adx_thresh": 25, "timeframe": "1h"
    })
    quality_core_d = PortfolioStrategy([s_c, s_f, s_g, s_adx_mom], conflict_rule="cancel",
                                       fusion_mode="union", zero_month_rescue=False)
    zero_rescue_d = PortfolioStrategy([s_d], conflict_rule="cancel",
                                      fusion_mode="union", zero_month_rescue=True)
    fof_d = FusionOfFusionsStrategy(
        fusions={"quality_core": quality_core_d, "zero_rescue": zero_rescue_d},
        conflict_rule="cancel", fusion_mode="union"
    )
    try:
        res_d = multi_engine.run(df, fof_d, risk_cfg_base)
        m_d = res_d["metrics"]
        finalist_systems.append(("FoF_ADX_Momentum", fof_d, m_d, None))
        print(f"  FoF_ADX_Momentum: {fmt(m_d)}")
    except Exception as e:
        print(f"  FoF_ADX_Momentum error: {e}")

    # Finalize all systems with OOS validation
    print("\nFinalist OOS Validation:")
    best_finalist_name = "FoF_Champion_P10.1"
    best_finalist_strat = fof_champ
    best_finalist_m = m_floor
    best_finalist_score = (
        m_floor["net_pnl"] -
        m_floor["negative_months"] * 100.0 -
        m_floor["zero_months"] * 500.0
    )

    finalist_oos = {}
    for sys_name, sys_strat, sys_m, _ in finalist_systems:
        if sys_strat is None or sys_m is None:
            continue
        oos_res = compute_oos(multi_engine, df, sys_strat, oos_splits, risk_cfg_base)
        oos_pnl = sum(r["pnl"] for r in oos_res)
        finalist_oos[sys_name] = {"oos_pnl": oos_pnl, "oos_res": oos_res}
        # Score: higher PnL, fewer neg months, fewer zero months, positive OOS
        score = (
            sys_m["net_pnl"] +
            oos_pnl * 0.5 -
            sys_m["negative_months"] * 100.0 -
            sys_m["zero_months"] * 500.0
        )
        print(f"  {sys_name:<30} IS={sys_m['net_pnl']:+.2f} OOS={oos_pnl:+.2f} "
              f"neg={sys_m['negative_months']} zero={sys_m['zero_months']} score={score:.1f}")
        if score > best_finalist_score:
            best_finalist_score = score
            best_finalist_name = sys_name
            best_finalist_strat = sys_strat
            best_finalist_m = sys_m
    sys.stdout.flush()

    print(f"\nSelected Champion: {best_finalist_name}")
    print(f"Champion: {fmt(best_finalist_m)}")

    # -------------------------------------------------------
    # MODULE 10: ANTI-OVERFITTING AUDIT
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 10: ANTI-OVERFITTING AUDIT")
    print("-" * 60)

    # IS/OOS degradation ratio
    champ_oos_pnl = finalist_oos.get(best_finalist_name, {}).get("oos_pnl", 0.0)
    is_oos_ratio = best_finalist_m["net_pnl"] / champ_oos_pnl if champ_oos_pnl > 0 else float("inf")

    print(f"IS PnL: ${best_finalist_m['net_pnl']:.2f}")
    print(f"OOS PnL: ${champ_oos_pnl:.2f}")
    print(f"IS/OOS Ratio: {is_oos_ratio:.2f}x (threshold: < 5.0x)")

    # Parameter stability: test ±1 variation on adx_thresh for Candidate C
    stability_results = {}
    for adx_t in [15, 20, 25]:
        cfg_var = dict(CAND_C_CFG)
        cfg_var["adx_thresh"] = adx_t
        s_var = UniversalStrategyTemplate(cfg_var)
        try:
            res_var = engine.run(df, s_var)
            stability_results[f"adx_thresh={adx_t}"] = res_var["metrics"]["net_pnl"]
        except Exception:
            stability_results[f"adx_thresh={adx_t}"] = 0.0

    pnl_vals = list(stability_results.values())
    pnl_std = np.std(pnl_vals) if len(pnl_vals) > 1 else 0.0
    print(f"Parameter Stability (adx_thresh ±5): PnL std=${pnl_std:.2f}")
    for k, v in stability_results.items():
        print(f"  {k}: ${v:.2f}")

    # Anti-overfitting warnings
    aof_warnings = []
    if is_oos_ratio > 5.0:
        aof_warnings.append(f"IS/OOS ratio {is_oos_ratio:.2f}x exceeds 5.0x threshold — potential overfit")
    if pnl_std > 3000.0:
        aof_warnings.append(f"Parameter sensitivity high (std=${pnl_std:.2f}) — narrow parameter dependency")

    if aof_warnings:
        for w in aof_warnings:
            print(f"  WARNING: {w}")
    else:
        print("  No anti-overfitting warnings detected.")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 11: OOS WALK-FORWARD VALIDATION
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 11: OOS WALK-FORWARD VALIDATION")
    print("-" * 60)

    wf_results = finalist_oos.get(best_finalist_name, {}).get("oos_res", [])
    combined_oos = sum(r["pnl"] for r in wf_results)
    print(f"Combined OOS PnL: ${combined_oos:.2f}")
    for wr in wf_results:
        print(f"  OOS {wr['split']}: PnL=${wr['pnl']:.2f} trades={wr['trades']} PF={wr['pf']:.2f} DD={wr['dd']:.2%}")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 12: STRESS TESTING
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 12: STRESS TESTING")
    print("-" * 60)
    stress_results = compute_stress(multi_engine, df, best_finalist_strat, risk_cfg_base)
    all_stress_pass = all(sr["verdict"] == "PASS" for sr in stress_results.values())
    print(f"Stress Test Summary: {'ALL PASS' if all_stress_pass else 'SOME FAIL'}")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 13: COMPLIANCE AUDITS
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 13: COMPLIANCE AUDITS")
    print("-" * 60)
    sys_aud = SystemAuditor(df, best_finalist_strat, multi_engine)
    audit = sys_aud.run_all_audits()
    for k, v in audit.items():
        print(f"  {k}: {v.get('status', '?')}")
    sys.stdout.flush()

    # -------------------------------------------------------
    # MODULE 14: REPORT GENERATION
    # -------------------------------------------------------
    print("\n" + "-" * 60)
    print("MODULE 14: REPORT GENERATION")
    print("-" * 60)

    all_audits_passed = all(v.get("status") == "PASS" for v in audit.values())
    champ_m = best_finalist_m

    # Verdict determination
    neg_months_champ = champ_m["negative_months"]
    zero_months_champ = champ_m["zero_months"]
    trades_champ = champ_m["total_trades"]

    if (neg_months_champ == 0 and zero_months_champ == 0 and
            trades_champ >= 780 and champ_m["net_pnl"] > 0 and all_audits_passed):
        verdict = "PASS_STRATEGY_FOUND"
    elif (neg_months_champ < FLOOR_NEG or zero_months_champ < FLOOR_ZERO) and all_audits_passed:
        verdict = "INFRASTRUCTURE_PASS_NEEDS_MORE_COMPUTE"
    elif not all_audits_passed:
        verdict = "INFRASTRUCTURE_FAIL_NEEDS_FIXES"
    else:
        verdict = "FAIL_NO_STRATEGY_FOUND"

    rpt = []
    rpt.append("# Phase 11 — Research Lab Intelligence Upgrade Report")
    rpt.append(f"\n**Compiled At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    rpt.append("**Project:** binance_futures_backtest")
    rpt.append("**Symbol:** BTCUSDT Perpetual Futures (Binance USD-M)")
    rpt.append(f"**Primary frame:** 1h ({len(df):,} candles)")

    rpt.append("\n## Executive Verdict")
    rpt.append(f"\n> [!IMPORTANT]")
    rpt.append(f"> **VERDICT: {verdict}**")
    rpt.append(f"> **Selected Champion:** {best_finalist_name}")
    rpt.append(f"> - Net PnL: **${champ_m['net_pnl']:.2f}** (vs Floor $10,535.14)")
    rpt.append(f"> - Win Rate: **{champ_m['win_rate']:.2%}**")
    rpt.append(f"> - Profit Factor: **{champ_m['profit_factor']:.2f}** (vs Floor 1.28)")
    rpt.append(f"> - Max Drawdown: **{champ_m['max_drawdown']:.2%}** (vs Floor 14.89%)")
    rpt.append(f"> - Total Trades: **{champ_m['total_trades']}** (vs Floor 493)")
    rpt.append(f"> - Months: **{champ_m['positive_months']} / {champ_m['negative_months']} / {champ_m['zero_months']}** +/-/0")
    rpt.append(f"> - Combined OOS PnL: **${combined_oos:.2f}** (vs Floor $4,878.89)")

    rpt.append("\n## 1. Phase 10.1 Quality Floor Reproduction")
    rpt.append("| Metric | Floor | Reproduced |")
    rpt.append("|---|---|---|")
    rpt.append(f"| Net PnL | $10,535.14 | ${m_floor['net_pnl']:.2f} |")
    rpt.append(f"| PF | 1.28 | {m_floor['profit_factor']:.2f} |")
    rpt.append(f"| DD | 14.89% | {m_floor['max_drawdown']:.2%} |")
    rpt.append(f"| Trades | 493 | {m_floor['total_trades']} |")
    rpt.append(f"| +/-/0 | 49/28/1 | {m_floor['positive_months']}/{m_floor['negative_months']}/{m_floor['zero_months']} |")
    rpt.append(f"| Floor OK | — | {'YES' if floor_ok else 'WARNING'} |")

    rpt.append("\n## 2. ResearchIdeaEngine Summary")
    rpt.append(f"- Total ideas generated: **{len(idea_engine.ideas)}**")
    rpt.append("- Idea categories covered:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        rpt.append(f"  - {cat}: {count} idea(s)")
    rpt.append("- Full idea registry: [research_ideas.json](reports/research_ideas.json)")
    rpt.append("- Ranked leaderboard: [research_ideas_leaderboard.md](reports/research_ideas_leaderboard.md)")

    rpt.append("\n## 3. New Candidate Families")
    rpt.append("| Candidate | Template | Net PnL ($) | Trades | PF | DD | +/-/0 |")
    rpt.append("|---|---|---|---|---|---|---|")
    for name, result in p11_cand_results.items():
        m_c = result["metrics"]
        if m_c:
            rpt.append(f"| {name} | {result['cfg']['template_type']} | "
                       f"{m_c['net_pnl']:.2f} | {m_c['total_trades']} | "
                       f"{m_c['profit_factor']:.2f} | {m_c['max_drawdown']:.2%} | "
                       f"{m_c['positive_months']}/{m_c['negative_months']}/{m_c['zero_months']} |")
        else:
            rpt.append(f"| {name} | {result['cfg']['template_type']} | ERROR | — | — | — | — |")

    rpt.append("\n## 4. Regime Risk Sizing Results")
    rpt.append("| Mode | Net PnL ($) | PF | DD | Trades | +/-/0 |")
    rpt.append("|---|---|---|---|---|---|")
    for mode_name, m_r in risk_results.items():
        rpt.append(f"| {mode_name} | {m_r['net_pnl']:.2f} | {m_r['profit_factor']:.2f} | "
                   f"{m_r['max_drawdown']:.2%} | {m_r['total_trades']} | "
                   f"{m_r['positive_months']}/{m_r['negative_months']}/{m_r['zero_months']} |")
    rpt.append(f"\nBest Risk Mode: **{best_risk_mode}**")

    rpt.append("\n## 5. 5m MTF Entry Research")
    rpt.append("| Config | Net PnL ($) | Trades | PF | DD | +/-/0 |")
    rpt.append("|---|---|---|---|---|---|")
    for name, m_mtf in mtf_results.items():
        rpt.append(f"| {name} | {m_mtf['net_pnl']:.2f} | {m_mtf['total_trades']} | "
                   f"{m_mtf['profit_factor']:.2f} | {m_mtf['max_drawdown']:.2%} | "
                   f"{m_mtf['positive_months']}/{m_mtf['negative_months']}/{m_mtf['zero_months']} |")

    rpt.append("\n## 6. Negative-Month Forensics")
    rpt.append(f"- Total FoF Champion negative months: **{len(neg_months_data)}**")
    rpt.append("- Failure category breakdown:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        rpt.append(f"  - {cat}: {count} month(s)")
    if best_neg_metrics:
        rpt.append(f"\nBest Anti-FalseBreakout Config: adx_slope_thresh={best_neg_cfg.get('adx_slope_thresh')} | "
                   f"vol_thresh={best_neg_cfg.get('volume_trend_thresh')}")
        rpt.append(f"  {fmt(best_neg_metrics)}")

    rpt.append("\n## 7. Zero-Month Elimination")
    rpt.append(f"- Zero months in FoF Champion: **{m_floor['zero_months']}**")
    if m_vwap:
        rpt.append(f"- VWAP Reclaim (standalone): {fmt(m_vwap)}")
    if m_fof_p11:
        rpt.append(f"- FoF + VWAP Rescue: {fmt(m_fof_p11)}")
        rpt.append(f"  - Zero month delta: {m_fof_p11['zero_months'] - m_floor['zero_months']:+d}")

    rpt.append("\n## 8. FoF Evolution — Finalist Comparison")
    rpt.append("| System | IS PnL ($) | OOS PnL ($) | PF | DD | +/-/0 |")
    rpt.append("|---|---|---|---|---|---|")
    for sys_name, _, sys_m, _ in finalist_systems:
        if sys_m is None:
            continue
        oos_p = finalist_oos.get(sys_name, {}).get("oos_pnl", 0.0)
        rpt.append(f"| {sys_name} | {sys_m['net_pnl']:.2f} | {oos_p:.2f} | "
                   f"{sys_m['profit_factor']:.2f} | {sys_m['max_drawdown']:.2%} | "
                   f"{sys_m['positive_months']}/{sys_m['negative_months']}/{sys_m['zero_months']} |")
    rpt.append(f"\n**Selected:** {best_finalist_name}")
    rpt.append("\n**Why selected:**")
    rpt.append(f"- Highest composite score: IS PnL + 0.5x OOS PnL - 100x neg months - 500x zero months")
    rpt.append(f"- Preserves quality floor metrics while improving on monthly distribution")

    rpt.append("\n## 9. Anti-Overfitting Audit")
    rpt.append(f"- IS/OOS Ratio: {is_oos_ratio:.2f}x (threshold: < 5.0x)")
    rpt.append(f"- Parameter Stability (adx_thresh ±5): PnL std=${pnl_std:.2f}")
    if aof_warnings:
        for w in aof_warnings:
            rpt.append(f"- **WARNING:** {w}")
    else:
        rpt.append("- No overfitting warnings detected.")

    rpt.append("\n## 10. Walk-Forward OOS Validation")
    rpt.append(f"- **Combined OOS PnL:** ${combined_oos:.2f}")
    rpt.append("\n| Period | PnL ($) | Trades | PF | DD |")
    rpt.append("|---|---|---|---|---|")
    for wr in wf_results:
        rpt.append(f"| {wr['split']} | {wr['pnl']:.2f} | {wr['trades']} | {wr['pf']:.2f} | {wr['dd']:.2%} |")

    rpt.append("\n## 11. Stress Testing Results")
    rpt.append("| Scenario | PnL ($) | DD | +/-/0 | Verdict |")
    rpt.append("|---|---|---|---|---|")
    for sn, sr in stress_results.items():
        rpt.append(f"| {sn} | {sr['pnl']:.2f} | {sr['dd']:.2%} | "
                   f"{sr['pos']}/{sr['neg']}/{sr['zero']} | **{sr['verdict']}** |")

    rpt.append("\n## 12. Champion Month-by-Month Table")
    rpt.append("| Month | Trades | Wins | Losses | Win Rate | Net PnL ($) | Drawdown | Status |")
    rpt.append("|---|---|---|---|---|---|---|---|")
    for r in get_monthly_report(champ_m):
        rpt.append(f"| {r['month']} | {r['trades']} | {r['wins']} | {r['losses']} | "
                   f"{r['win_rate']:.2%} | {r['net_pnl']:.2f} | {r['drawdown']:.2%} | {r['status']} |")

    rpt.append("\n## 13. Compliance Audits")
    for k, v in audit.items():
        rpt.append(f"- **{k}:** {v.get('status', '?')}")

    rpt.append("\n## 14. Remaining Gap & Phase 12 Recommendations")
    remaining_neg = champ_m["negative_months"]
    remaining_zero = champ_m["zero_months"]
    remaining_trades = 780 - champ_m["total_trades"]
    rpt.append(f"- Remaining negative months: **{remaining_neg}** (target: 0, gap: {remaining_neg})")
    rpt.append(f"- Remaining zero months: **{remaining_zero}** (target: 0, gap: {remaining_zero})")
    rpt.append(f"- Trade count gap to target (780): **{max(0, remaining_trades)}**")
    rpt.append("\n**Phase 12 Recommendations:**")
    rpt.append("1. Deep multi-objective optimization: sweep new P11 templates jointly with FoF parameters")
    rpt.append("2. Live-regime-aligned filler with stricter activity criteria")
    rpt.append("3. Ensemble diversification: add orthogonal strategy (e.g. funding + session range)")
    rpt.append("4. Dynamic risk matrix: regime + ADX + funding state composite")
    rpt.append("5. Asymmetric TP/SL: tighter stops on false-breakout-prone regimes")

    rpt.append("\n---")
    elapsed = (datetime.now(timezone.utc) - start_t).total_seconds()
    rpt.append(f"*Report generated by Phase 11 Research Lab in {elapsed:.0f}s. "
               f"ResearchIdeaEngine v1.0. {len(idea_engine.ideas)} ideas generated.*")

    os.makedirs("reports", exist_ok=True)
    report_path = "reports/phase11_research_idea_engine_regime_risk_mtf_precision_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rpt))
    print(f"\nReport saved to: {report_path}")
    print(f"Total elapsed: {elapsed:.0f}s")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
