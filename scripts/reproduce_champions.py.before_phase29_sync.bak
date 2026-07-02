"""
scripts/reproduce_champions.py

Phase 11.1 Reproducibility Lockdown Harness

Runs:
  - Phase 10.1 original champion (Phase10_1_FoF_4Subportfolio)
  - Phase 11 reproduced champion (Phase11_FoF_2Subportfolio)

Prints hashes of: config, data, strategy, engine, trade log, and metrics.
Lists first 10 / last 10 trades and monthly summary.
Determines exact trade-level differences between them.
"""
import os
import sys
import hashlib
import json
import numpy as np
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy, FusionOfFusionsStrategy

# Configs
CAND_A_CFG = {
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None, "regime_filter_mode": "no_filter",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h"
}
CAND_C_CFG = {
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None, "regime_filter_mode": "strict",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 100, "rsi_oversold": 0,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h"
}
CAND_D_CFG = {
    "template_type": "low_activity_filler",
    "trend_filter": "ema_200", "regime_filter_mode": "no_filter",
    "tp_atr_mult": 3.5, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 25,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h"
}
CAND_F_CFG = {
    "template_type": "atr_volatility_expansion",
    "trend_filter": None, "regime_filter_mode": "strict",
    "tp_atr_mult": 3.0, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h"
}
CAND_G_CFG = {
    "template_type": "funding_extreme_reversal",
    "trend_filter": None, "regime_filter_mode": "strict",
    "tp_atr_mult": 2.0, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h"
}

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def build_p10_1_strategy():
    # Phase 10.1 FoF 4-Subportfolio configuration
    s_a = UniversalStrategyTemplate(CAND_A_CFG)
    s_c = UniversalStrategyTemplate(CAND_C_CFG)
    s_d = UniversalStrategyTemplate(CAND_D_CFG)
    s_f = UniversalStrategyTemplate(CAND_F_CFG)
    s_g = UniversalStrategyTemplate(CAND_G_CFG)
    
    fusion_quality_core = PortfolioStrategy([s_c, s_f, s_g, s_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
    fusion_activity = PortfolioStrategy([s_a, s_c, s_f], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=False)
    fusion_defensive = PortfolioStrategy([s_c, s_g, s_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
    fusion_zero_rescue = PortfolioStrategy([s_d, s_g], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
    
    fusions_dict = {
        "quality_core": fusion_quality_core,
        "activity": fusion_activity,
        "defensive": fusion_defensive,
        "zero_rescue": fusion_zero_rescue
    }
    return FusionOfFusionsStrategy(fusions_dict, conflict_rule="cancel")

def build_p11_strategy():
    # Phase 11 FoF 2-Subportfolio configuration
    s_c = UniversalStrategyTemplate(CAND_C_CFG)
    s_d = UniversalStrategyTemplate(CAND_D_CFG)
    s_f = UniversalStrategyTemplate(CAND_F_CFG)
    s_g = UniversalStrategyTemplate(CAND_G_CFG)
    
    quality_core = PortfolioStrategy([s_c, s_f, s_g], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=False)
    zero_rescue = PortfolioStrategy([s_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
    
    fusions_dict = {
        "quality_core": quality_core,
        "zero_rescue": zero_rescue
    }
    return FusionOfFusionsStrategy(fusions_dict, conflict_rule="cancel")

def format_metrics(m):
    return (f"PnL=${m['net_pnl']:.2f} trades={m['total_trades']} PF={m['profit_factor']:.2f} DD={m['max_drawdown']:.2%} "
            f"+/-/0={m['positive_months']}/{m['negative_months']}/{m['zero_months']}")

def run_reproduction():
    print("=" * 80)
    print("REPRODUCIBILITY LOCKDOWN HARNESS — PHASE 11.1")
    print("=" * 80)
    
    # 1. Load Data
    data_path = "data/processed/BTCUSDT_1h_processed.csv"
    if not os.path.exists(data_path):
        print(f"ERROR: Data file {data_path} not found.")
        sys.exit(1)
        
    df = pd.read_csv(data_path)
    df = add_indicators(df)
    
    data_csv = df.to_csv(index=False)
    data_hash = get_hash(data_csv)
    print(f"Data File: {data_path} | Rows: {len(df)} | Hash: {data_hash}")
    
    # Engine Settings
    engine_settings = {
        "initial_capital": 10000.0,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slippage": 0.0005,
        "max_positions": 1,
        "cooldown_candles": 5
    }
    engine_hash = get_hash(json.dumps(engine_settings, sort_keys=True))
    print(f"Engine Class: MultiPositionBacktestEngine | Hash: {engine_hash}")
    
    risk_cfg = {
        "monthly_risk_limit": 0.025,
        "risk_limit_pct": 1.0,
        "risk_throttle_mode": "no_throttle",
        "emergency_pause_threshold": 0.025
    }
    config_hash = get_hash(json.dumps(risk_cfg, sort_keys=True))
    print(f"Risk Config: {risk_cfg} | Hash: {config_hash}")
    print("-" * 80)
    
    systems = [
        ("Phase10_1_FoF_4Subportfolio", build_p10_1_strategy()),
        ("Phase11_FoF_2Subportfolio", build_p11_strategy())
    ]
    
    results = {}
    
    for name, strat in systems:
        print(f"\nRUNNING SYSTEM: {name} ...")
        strat_str = strat.__class__.__name__ + "_" + "_".join(strat.fusions.keys())
        strat_hash = get_hash(strat_str)
        
        engine = MultiPositionBacktestEngine(**engine_settings)
        res = engine.run(df, strat, risk_cfg)
        m = res["metrics"]
        trades_df = res["trades"]
        
        # Trade log hash (use key columns: entry_time, exit_time, side, size, exit_price, net_pnl)
        if not trades_df.empty:
            trade_sub = trades_df[["entry_time", "exit_time", "side", "size", "exit_price", "net_pnl"]].copy()
            # Round numeric columns to float precision to avoid formatting mismatch
            trade_sub["size"] = trade_sub["size"].round(3)
            trade_sub["exit_price"] = trade_sub["exit_price"].round(1)
            trade_sub["net_pnl"] = trade_sub["net_pnl"].round(2)
            trade_log_hash = get_hash(trade_sub.to_csv(index=False))
        else:
            trade_log_hash = get_hash("empty_trade_log")
            
        metrics_hash = get_hash(json.dumps({k: v for k, v in m.items() if k != "monthly_report"}, sort_keys=True, default=str))
        
        results[name] = {
            "metrics": m,
            "trades": trades_df,
            "strat_hash": strat_hash,
            "trade_log_hash": trade_log_hash,
            "metrics_hash": metrics_hash
        }
        
        print(f"  Strategy Hash:  {strat_hash}")
        print(f"  Trade Log Hash: {trade_log_hash}")
        print(f"  Metrics Hash:   {metrics_hash}")
        print(f"  Metrics:        {format_metrics(m)}")
        
        # First 10 / Last 10 trades
        if not trades_df.empty:
            print("\n  FIRST 10 TRADES:")
            sub_first = trades_df[["strategy", "entry_datetime", "exit_datetime", "side", "entry_price", "exit_price", "net_pnl", "slippage"]].head(10)
            print(sub_first.to_string(index=False))
            
            print("\n  LAST 10 TRADES:")
            sub_last = trades_df[["strategy", "entry_datetime", "exit_datetime", "side", "entry_price", "exit_price", "net_pnl", "slippage"]].tail(10)
            print(sub_last.to_string(index=False))
        else:
            print("  No trades executed.")
            
        # Monthly Summary Table
        print("\n  MONTHLY SUMMARY:")
        print(f"  {'Month':<10} | {'Trades':<6} | {'Wins':<4} | {'Losses':<6} | {'Win Rate':<8} | {'Net PnL':<10} | {'Status':<8}")
        print(f"  {'-'*75}")
        for mr in m["monthly_report"][:12]: # Show first 12 months for brevity
            print(f"  {mr['month']:<10} | {mr['trades']:<6} | {mr['wins']:<4} | {mr['losses']:<6} | {mr['win_rate']:<8.2%} | ${mr['net_pnl']:<9.2f} | {mr['status']:<8}")
        if len(m["monthly_report"]) > 12:
            print(f"  ... and {len(m['monthly_report'])-12} more months.")
        print("-" * 80)
        
    # Trade Difference Analysis
    print("\n" + "=" * 80)
    print("TRADE LOG COMPARISON & DIFF")
    print("=" * 80)
    
    t1 = results["Phase10_1_FoF_4Subportfolio"]["trades"]
    t2 = results["Phase11_FoF_2Subportfolio"]["trades"]
    
    print(f"Phase10_1_FoF_4Subportfolio trade count: {len(t1)}")
    print(f"Phase11_FoF_2Subportfolio trade count:   {len(t2)}")
    
    if len(t1) == len(t2) and results["Phase10_1_FoF_4Subportfolio"]["trade_log_hash"] == results["Phase11_FoF_2Subportfolio"]["trade_log_hash"]:
        print("\nSUCCESS: Both champions are identical!")
    else:
        print("\nDIFFERENCE DETECTED: Reviewing trade diff...")
        # Compare trade-by-trade
        max_idx = max(len(t1), len(t2))
        diffs = 0
        for i in range(max_idx):
            if i >= len(t1):
                print(f"Trade #{i}: Extra trade in Phase 11: {t2.iloc[i]['entry_datetime']} {t2.iloc[i]['side']} entry={t2.iloc[i]['entry_price']} exit={t2.iloc[i]['exit_price']} net={t2.iloc[i]['net_pnl']:.2f}")
                diffs += 1
            elif i >= len(t2):
                print(f"Trade #{i}: Missing trade in Phase 11: {t1.iloc[i]['entry_datetime']} {t1.iloc[i]['side']} entry={t1.iloc[i]['entry_price']} exit={t1.iloc[i]['exit_price']} net={t1.iloc[i]['net_pnl']:.2f}")
                diffs += 1
            else:
                r1 = t1.iloc[i]
                r2 = t2.iloc[i]
                diff_fields = []
                if r1["entry_time"] != r2["entry_time"]:
                    diff_fields.append("entry_time")
                if r1["exit_time"] != r2["exit_time"]:
                    diff_fields.append("exit_time")
                if r1["side"] != r2["side"]:
                    diff_fields.append("side")
                if abs(r1["net_pnl"] - r2["net_pnl"]) > 0.01:
                    diff_fields.append(f"net_pnl({r1['net_pnl']:.2f} vs {r2['net_pnl']:.2f})")
                if abs(r1["entry_price"] - r2["entry_price"]) > 0.01:
                    diff_fields.append(f"entry_price({r1['entry_price']} vs {r2['entry_price']})")
                if abs(r1["exit_price"] - r2["exit_price"]) > 0.01:
                    diff_fields.append(f"exit_price({r1['exit_price']} vs {r2['exit_price']})")
                if r1["strategy"] != r2["strategy"]:
                    diff_fields.append(f"strategy({r1['strategy']} vs {r2['strategy']})")
                    
                if diff_fields:
                    print(f"Trade #{i} mismatch on {', '.join(diff_fields)}")
                    diffs += 1
                    if diffs >= 20:
                        print("Truncating trade diff list at 20 mismatches.")
                        break
        print(f"Total trade-level discrepancies found: {diffs}")

if __name__ == "__main__":
    run_reproduction()
