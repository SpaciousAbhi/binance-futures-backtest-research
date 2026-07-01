import sys, os
sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

# Load 1h data
df = pd.read_csv('data/processed/BTCUSDT_1h_processed.csv')
df = add_indicators(df)

# Strategy 1: Core Bollinger Expansion Breakout (optimized)
cfg_c = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 100, "rsi_oversold": 0, # No RSI filter
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}

# Strategy 2: ATR Volatility Expansion (optimized)
cfg_f = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "atr_volatility_expansion",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 3.0, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}

# Strategy 3: Funding Extreme Reversal (optimized)
cfg_g = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "funding_extreme_reversal",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.0, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}

# Strategy 4: Low-activity reversion filler
cfg_d = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "low_activity_filler",
    "trend_filter": "ema_200",
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 3.5, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 25,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}

s_c = UniversalStrategyTemplate(cfg_c)
s_f = UniversalStrategyTemplate(cfg_f)
s_g = UniversalStrategyTemplate(cfg_g)
s_d = UniversalStrategyTemplate(cfg_d)

# Run standalone first
engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)
for name, s in [("Cand C", s_c), ("Cand F", s_f), ("Cand G", s_g), ("Cand D", s_d)]:
    res = engine.run(df, s)
    m = res["metrics"]
    print(f"{name:<10} PnL=${m['net_pnl']:.2f} trades={m['total_trades']} +/-/0={m['positive_months']}/{m['negative_months']}/{m['zero_months']} PF={m['profit_factor']:.2f} DD={m['max_drawdown']:.2%}")

# Run Portfolio of 3 (No Filler)
print("\nPortfolio of 3 (C + F + G) Union:")
port_3 = PortfolioStrategy([s_c, s_f, s_g], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=False)
multi_engine = MultiPositionBacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005, max_positions=3, cooldown_candles=5)
port_base = {
    "monthly_risk_limit": 0.025, "risk_limit_pct": 1.0,
    "risk_throttle_mode": "no_throttle", "emergency_pause_threshold": 0.03,
}
res_port3 = multi_engine.run(df, port_3, port_base)
m_p3 = res_port3["metrics"]
print(f"  PnL=${m_p3['net_pnl']:.2f} trades={m_p3['total_trades']} +/-/0={m_p3['positive_months']}/{m_p3['negative_months']}/{m_p3['zero_months']} PF={m_p3['profit_factor']:.2f} DD={m_p3['max_drawdown']:.2%}")

# Run Portfolio of 4 (C + F + G + Filler)
print("\nPortfolio of 4 (C + F + G + Filler) Union (zero-rescue active):")
port_4 = PortfolioStrategy([s_c, s_f, s_g, s_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
res_port4 = multi_engine.run(df, port_4, port_base)
m_p4 = res_port4["metrics"]
print(f"  PnL=${m_p4['net_pnl']:.2f} trades={m_p4['total_trades']} +/-/0={m_p4['positive_months']}/{m_p4['negative_months']}/{m_p4['zero_months']} PF={m_p4['profit_factor']:.2f} DD={m_p4['max_drawdown']:.2%}")
