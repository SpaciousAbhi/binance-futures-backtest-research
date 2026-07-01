"""Check what the R column means and inspect a real result."""
import os, sys, json, csv
sys.path.insert(0, '.')
from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
import pandas as pd

df = add_indicators(pd.read_csv('data/processed/BTCUSDT_1h_processed.csv'))
settings  = {'initial_capital': 10000.0, 'maker_fee': 0.0002, 'taker_fee': 0.0005,
             'slippage': 0.0005, 'max_positions': 1, 'cooldown_candles': 5}
base_risk = {'risk_limit_pct': 1.0, 'monthly_risk_limit': 0.025,
             'risk_throttle_mode': 'no_throttle', 'emergency_pause_threshold': 0.025}
engine = MultiPositionBacktestEngine(**settings)

with open('reports/phase21_candidate_registry.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

c = rows[0]
params = json.loads(c['parameters_json'])
strat  = UniversalStrategyTemplate(params)
result = engine.run(df, strat, base_risk)
trades = result.get('trades')
print("Columns:", list(trades.columns))
print("R stats:", trades['R'].describe() if 'R' in trades.columns else "NO R COLUMN")
print("net_pnl stats:", trades['net_pnl'].describe())
print("win_rate:", (trades['net_pnl'] > 0).mean())
pf_val = trades[trades['net_pnl']>0]['net_pnl'].sum() / abs(trades[trades['net_pnl']<=0]['net_pnl'].sum())
print("profit_factor:", pf_val)
print("total_pnl:", trades['net_pnl'].sum())
print("\nFirst 5 trades R column:")
print(trades[['entry_time','side','net_pnl','R','entry_price','stop_loss','take_profit']].head(5).to_string())
