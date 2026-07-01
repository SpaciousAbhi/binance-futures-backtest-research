"""Quick diagnostic: why did all 200 cheap scan candidates fail?"""
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

print("=== CHEAP SCAN DIAGNOSTIC ===")
rejection_reasons = {}
for c in rows[:20]:
    params = json.loads(c['parameters_json'])
    try:
        strat  = UniversalStrategyTemplate(params)
        result = engine.run(df, strat, base_risk)
        trades = result.get('trades')
        n      = len(trades) if trades is not None and not trades.empty else 0
        avg_r  = float(trades['R'].mean()) if n > 0 and 'R' in trades.columns else 0.0
        reason = "OK" if n >= 10 else f"too_few_trades ({n})"
        if n >= 10 and avg_r < 0.8:
            reason = f"poor_avg_R ({avg_r:.2f})"
        rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        print(f"  family={c['family'][:25]:25s}  template={params['template_type'][:28]:28s}  trades={n:4d}  avg_r={avg_r:.2f}  reason={reason}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nRejection reason summary:", rejection_reasons)
