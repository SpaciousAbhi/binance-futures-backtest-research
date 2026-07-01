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

# Setup candidate C
P5_BEST_CFG = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45
}
strat_c = UniversalStrategyTemplate(P5_BEST_CFG)
engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)
res_c = engine.run(df, strat_c)
met_c = res_c["metrics"]
trd_c = res_c["trades"]

# Setup F-E
P4S1_CFG = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": "ema_200",
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45,
}
P6S3_CFG = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
    "rsi_overbought": 75, "rsi_oversold": 30,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45,
}
FILLER_CFG = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "low_activity_filler",
    "trend_filter": "ema_200",
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 3.5, "sl_atr_mult": 2.0,
    "rsi_overbought": 75, "rsi_oversold": 25,
    "adx_thresh": 20, "wick_ratio_thresh": 0.45,
}
strats_a = [UniversalStrategyTemplate(P5_BEST_CFG), UniversalStrategyTemplate(P4S1_CFG), UniversalStrategyTemplate(P6S3_CFG)]
strat_d = UniversalStrategyTemplate(FILLER_CFG)

best_port = PortfolioStrategy(strats_a + [strat_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
multi_engine = MultiPositionBacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005, max_positions=3, cooldown_candles=5)
port_base = {
    "monthly_risk_limit": 0.025, "risk_limit_pct": 1.0,
    "risk_throttle_mode": "no_throttle", "emergency_pause_threshold": 0.03,
}
res_fe = multi_engine.run(df, best_port, port_base)
met_fe = res_fe["metrics"]
trd_fe = res_fe["trades"]

# Extract negative months
neg_c = [r for r in met_c["monthly_report"] if r["net_pnl"] < 0]
neg_fe = [r for r in met_fe["monthly_report"] if r["net_pnl"] < 0]

print(f"Candidate C: {len(neg_c)} negative months")
print(f"F-E: {len(neg_fe)} negative months")

# Print top 10 most negative months for F-E
neg_fe_sorted = sorted(neg_fe, key=lambda x: x["net_pnl"])
print("\nTop 10 Negative Months for F-E:")
for r in neg_fe_sorted[:10]:
    print(f"Month: {r['month']}  PnL=${r['net_pnl']:.2f}  trades={r['trades']}  win_rate={r['win_rate']:.2%}")

# Let's inspect the trades of the worst month for F-E (e.g. index 0)
worst_month = neg_fe_sorted[0]["month"]
print(f"\nTrades in the worst month ({worst_month}):")
df_trd_fe = pd.DataFrame(trd_fe)
df_trd_fe["month"] = pd.to_datetime(df_trd_fe["exit_datetime"]).dt.to_period("M").astype(str)
month_trades = df_trd_fe[df_trd_fe["month"] == worst_month]
for _, t in month_trades.iterrows():
    print(f"  Entry: {t['entry_datetime'][:16]} Exit: {t['exit_datetime'][:16]} PnL=${t['net_pnl']:.2f} Strategy: {t['strategy']} Reason: {t['reason']}")
