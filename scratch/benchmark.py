import time
import pandas as pd
import numpy as np
from src.backtest.engine import BacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.features.indicators import add_indicators

def main():
    print("Loading data...")
    df = pd.read_csv("data/processed/BTCUSDT_1h_processed.csv")
    print(f"Loaded {len(df)} rows.")
    
    print("Calculating indicators...")
    df = add_indicators(df)
    
    df_sub = df.iloc[:8760].reset_index(drop=True)
    
    engine = BacktestEngine(initial_capital=10000.0)
    
    config = {
        "template_type": "trend",
        "trend_filter": "ema_200",
        "volatility_filter": "atr_low",
        "rsi_filter": "overbought_oversold",
        "wick_filter": "large_wick",
        "funding_filter": "extreme",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.5,
        "atr_pct_thresh": 0.03,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "wick_ratio_thresh": 0.5,
        "funding_threshold": 0.0005,
        "adx_thresh": 25
    }
    
    strat = UniversalStrategyTemplate(config)
    
    print("Running warm-up backtest...")
    engine.run(df_sub, strat)
    
    print("Benchmarking 100 runs...")
    start_time = time.time()
    for _ in range(100):
        # We must create a new strategy instance each time, like in the grid search
        strat_new = UniversalStrategyTemplate(config)
        engine.run(df_sub, strat_new)
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Elapsed time: {elapsed:.4f} seconds for 100 runs.")
    print(f"Average time per run: {elapsed/100 * 1000:.2f} ms")
    print(f"Runs per second: {100/elapsed:.2f}")

if __name__ == "__main__":
    main()
