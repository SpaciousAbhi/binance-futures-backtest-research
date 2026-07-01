import sys, os
sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate

# Load 1h data
df = pd.read_csv('data/processed/BTCUSDT_1h_processed.csv')
df = add_indicators(df)

engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)

# 1. Optimize ATR Volatility Expansion
print("Optimizing ATR Volatility Expansion:")
atr_exp_configs = []
for trend in [None, "ema_200"]:
    for regime in ["no_filter", "soft", "strict"]:
        for tp in [1.5, 2.0, 2.5, 3.0]:
            for sl in [1.0, 1.5, 2.0]:
                cfg = {
                    "strategy_class": "UniversalStrategyTemplate",
                    "template_type": "atr_volatility_expansion",
                    "trend_filter": trend,
                    "regime_filter_mode": regime,
                    "tp_atr_mult": tp, "sl_atr_mult": sl,
                    "rsi_overbought": 75, "rsi_oversold": 30,
                    "adx_thresh": 20, "wick_ratio_thresh": 0.45
                }
                s = UniversalStrategyTemplate(cfg)
                res = engine.run(df, s)
                m = res["metrics"]
                if m["net_pnl"] > 0:
                    atr_exp_configs.append((trend, regime, tp, sl, m))
                    trend_str = str(trend)
                    print(f"  Trend={trend_str:<8} Regime={regime:<10} TP={tp} SL={sl} | PnL=${m['net_pnl']:.2f} trades={m['total_trades']} PF={m['profit_factor']:.2f} DD={m['max_drawdown']:.2%} +/-/0={m['positive_months']}/{m['negative_months']}/{m['zero_months']}")

# 2. Optimize Funding Extreme Reversal
print("\nOptimizing Funding Extreme Reversal:")
funding_rev_configs = []
for trend in [None, "ema_200"]:
    for regime in ["no_filter", "soft", "strict"]:
        for tp in [1.5, 2.0, 2.5, 3.0]:
            for sl in [1.0, 1.5, 2.0]:
                cfg = {
                    "strategy_class": "UniversalStrategyTemplate",
                    "template_type": "funding_extreme_reversal",
                    "trend_filter": trend,
                    "regime_filter_mode": regime,
                    "tp_atr_mult": tp, "sl_atr_mult": sl,
                    "rsi_overbought": 75, "rsi_oversold": 30,
                    "adx_thresh": 20, "wick_ratio_thresh": 0.45
                }
                s = UniversalStrategyTemplate(cfg)
                res = engine.run(df, s)
                m = res["metrics"]
                if m["net_pnl"] > -500: # Show even slightly negative or positive
                    funding_rev_configs.append((trend, regime, tp, sl, m))
                    trend_str = str(trend)
                    print(f"  Trend={trend_str:<8} Regime={regime:<10} TP={tp} SL={sl} | PnL=${m['net_pnl']:.2f} trades={m['total_trades']} PF={m['profit_factor']:.2f} DD={m['max_drawdown']:.2%} +/-/0={m['positive_months']}/{m['negative_months']}/{m['zero_months']}")
