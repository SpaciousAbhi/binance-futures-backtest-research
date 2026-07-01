import os
import json
import yaml
import pandas as pd
import numpy as np

from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

def main():
    print("Testing data loading and backtests...")
    # Load configs
    project_cfg = yaml.safe_load(open("configs/project.yaml"))
    costs_cfg = yaml.safe_load(open("configs/costs.yaml"))

    symbol = project_cfg.get("symbol", "BTCUSDT")
    timeframe = "1h"
    raw_dir = project_cfg.get("raw_data_dir", "data/raw")
    processed_dir = project_cfg.get("processed_data_dir", "data/processed")

    # Load and enrich data
    processor = DataProcessor(raw_dir, processed_dir)
    df_processed = processor.process_and_align(symbol, timeframe)
    df_enriched = add_indicators(df_processed)
    print(f"Data loaded: {len(df_enriched)} rows.")

    # Read top 3 configurations from leaderboard
    with open("reports/search_checkpoint.json", "r") as f:
        checkpoint = json.load(f)
    leaderboard = checkpoint["leaderboard"]
    top_3_configs = [x["config"] for x in leaderboard[:3]]
    print("Loaded top 3 configs:")
    for idx, cfg in enumerate(top_3_configs):
        print(f"Config {idx+1}: {cfg['template_type']} | rsi: {cfg.get('rsi_overbought')}/{cfg.get('rsi_oversold')}")

    # Standard candidate configs
    p4_strat_1_cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": "ema_200",
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.8,
        "rsi_overbought": 75,
        "rsi_oversold": 30,
        "adx_thresh": 20,
        "wick_ratio_thresh": 0.45
    }
    p5_best_single_cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": None,
        "regime_filter_mode": "strict",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.8,
        "rsi_overbought": 75,
        "rsi_oversold": 30,
        "adx_thresh": 20,
        "wick_ratio_thresh": 0.45
    }
    rebuilt_filler_cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "low_activity_filler",
        "trend_filter": "ema_200",
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 3.5,
        "sl_atr_mult": 2.0,
        "rsi_overbought": 75,
        "rsi_oversold": 25,
        "adx_thresh": 20,
        "wick_ratio_thresh": 0.45
    }
    p6_strat_3_cfg = {
        "strategy_class": "UniversalStrategyTemplate",
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": None,
        "regime_filter_mode": "no_filter",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.8,
        "rsi_overbought": 75,
        "rsi_oversold": 30,
        "adx_thresh": 20,
        "wick_ratio_thresh": 0.45
    }

    # Initialize engines
    engine_single = BacktestEngine(
        initial_capital=costs_cfg.get("initial_capital", 10000.0),
        maker_fee=costs_cfg.get("maker_fee", 0.0002),
        taker_fee=costs_cfg.get("taker_fee", 0.0005),
        slippage=costs_cfg.get("slippage", 0.0005)
    )
    
    engine_multi = MultiPositionBacktestEngine(
        initial_capital=costs_cfg.get("initial_capital", 10000.0),
        maker_fee=costs_cfg.get("maker_fee", 0.0002),
        taker_fee=costs_cfg.get("taker_fee", 0.0005),
        slippage=costs_cfg.get("slippage", 0.0005),
        max_positions=3,
        cooldown_candles=5
    )

    # Candidate A
    portfolio_a = PortfolioStrategy([
        UniversalStrategyTemplate(p5_best_single_cfg),
        UniversalStrategyTemplate(p4_strat_1_cfg),
        UniversalStrategyTemplate(p6_strat_3_cfg)
    ], conflict_rule="cancel")
    print("Running Candidate A...")
    res_a = engine_multi.run(df_enriched, portfolio_a, {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0})
    print(f"Candidate A run complete. Trades: {len(res_a['trades'])}")

    # Candidate B
    portfolio_b = PortfolioStrategy([
        UniversalStrategyTemplate(cfg) for cfg in top_3_configs
    ], conflict_rule="cancel")
    print("Running Candidate B...")
    res_b = engine_multi.run(df_enriched, portfolio_b, {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0})
    print(f"Candidate B run complete. Trades: {len(res_b['trades'])}")

    # Candidate C
    strat_c = UniversalStrategyTemplate(p5_best_single_cfg)
    print("Running Candidate C...")
    res_c = engine_single.run(df_enriched, strat_c)
    print(f"Candidate C run complete. Trades: {len(res_c['trades'])}")

    # Candidate D
    strat_d = UniversalStrategyTemplate(rebuilt_filler_cfg)
    print("Running Candidate D...")
    res_d = engine_single.run(df_enriched, strat_d)
    print(f"Candidate D run complete. Trades: {len(res_d['trades'])}")

    # Candidate E
    print("Running Candidate E...")
    res_e = engine_multi.run(df_enriched, portfolio_a, {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0, "delay_candles": 1})
    print(f"Candidate E run complete. Trades: {len(res_e['trades'])}")

if __name__ == "__main__":
    main()
