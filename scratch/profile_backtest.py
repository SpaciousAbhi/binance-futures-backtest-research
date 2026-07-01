import sys
import os
sys.path.insert(0, r"C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest")

import time
import pandas as pd
import numpy as np
import yaml
from concurrent.futures import ProcessPoolExecutor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate

# Global variables for workers
_df_tf = None
_engine = None

def init_worker(df_tf_parent, costs_cfg_parent):
    global _df_tf, _engine
    _df_tf = df_tf_parent
    _engine = BacktestEngine(
        initial_capital=costs_cfg_parent.get("initial_capital", 10000.0),
        maker_fee=costs_cfg_parent.get("maker_fee", 0.0002),
        taker_fee=costs_cfg_parent.get("taker_fee", 0.0005),
        slippage=costs_cfg_parent.get("slippage", 0.0005)
    )

def run_backtest_task(config):
    strat = UniversalStrategyTemplate(config)
    res = _engine.run(_df_tf, strat)
    return config, res["metrics"]

if __name__ == "__main__":
    df_path = r"C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\data/processed/BTCUSDT_1h_processed.csv"
    costs_path = r"C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\configs/costs.yaml"
    
    # Load data for main thread
    df = pd.read_csv(df_path)
    df_tf = add_indicators(df)
    
    with open(costs_path, "r") as f:
        costs_cfg = yaml.safe_load(f)
        
    configs = [
        {
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
    ] * 100 # test 100 runs
    
    # Parallel run with pre-calculated df passed
    t0 = time.time()
    workers = max(1, os.cpu_count() - 1)
    print(f"Starting ProcessPoolExecutor with {workers} workers and precalc df...")
    
    par_results = []
    with ProcessPoolExecutor(max_workers=workers, initializer=init_worker, initargs=(df_tf, costs_cfg)) as executor:
        futures = [executor.submit(run_backtest_task, cfg) for cfg in configs]
        for f in futures:
            par_results.append(f.result()[1])
            
    t_par = time.time() - t0
    print(f"Parallel 100 runs took: {t_par:.2f}s ({t_par/100*1000:.2f} ms per run)")
