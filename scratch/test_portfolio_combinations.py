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

# Define candidates
cand_c_opt = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 100, "rsi_oversold": 0, # No RSI filter
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}

cand_d_exact = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "low_activity_filler",
    "trend_filter": "ema_200",
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 3.5, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 25,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}

# Run them standalone
engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)

s_c = UniversalStrategyTemplate(cand_c_opt)
res_c = engine.run(df, s_c)
m_c = res_c["metrics"]
print(f"Cand C (Opt) Standalone: PnL=${m_c['net_pnl']:.2f} trades={m_c['total_trades']} +/-/0={m_c['positive_months']}/{m_c['negative_months']}/{m_c['zero_months']} PF={m_c['profit_factor']:.2f} DD={m_c['max_drawdown']:.2%}")

s_d = UniversalStrategyTemplate(cand_d_exact)
res_d = engine.run(df, s_d)
m_d = res_d["metrics"]
print(f"Cand D (Filler) Standalone: PnL=${m_d['net_pnl']:.2f} trades={m_d['total_trades']} +/-/0={m_d['positive_months']}/{m_d['negative_months']}/{m_d['zero_months']} PF={m_d['profit_factor']:.2f} DD={m_d['max_drawdown']:.2%}")

# Let's check overlap of signals
sig_c = []
sig_d = []
for i in range(len(df)):
    if s_c.get_signal(df, i) is not None:
        sig_c.append(i)
    if s_d.get_signal(df, i) is not None:
        sig_d.append(i)
        
overlap = set(sig_c) & set(sig_d)
print(f"Cand C signal bars: {len(sig_c)}")
print(f"Cand D signal bars: {len(sig_d)}")
print(f"Overlap signal bars: {len(overlap)}")

# Build Portfolio: C + D
# We want to test union mode
port = PortfolioStrategy([s_c, s_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
multi_engine = MultiPositionBacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005, max_positions=3, cooldown_candles=5)
port_base = {
    "monthly_risk_limit": 0.025, "risk_limit_pct": 1.0,
    "risk_throttle_mode": "no_throttle", "emergency_pause_threshold": 0.03,
}
res_port = multi_engine.run(df, port, port_base)
m_port = res_port["metrics"]
print(f"Portfolio C + D: PnL=${m_port['net_pnl']:.2f} trades={m_port['total_trades']} +/-/0={m_port['positive_months']}/{m_port['negative_months']}/{m_port['zero_months']} PF={m_port['profit_factor']:.2f} DD={m_port['max_drawdown']:.2%}")
