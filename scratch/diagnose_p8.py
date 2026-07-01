"""Diagnose Phase 8 baseline regression."""
import sys
sys.path.insert(0, '.')
import pandas as pd
from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

proc = DataProcessor('data/raw', 'data/processed')
datasets = {}
for tf in ['5m', '15m', '1h']:
    df = pd.read_csv(f'data/processed/BTCUSDT_{tf}_processed.csv')
    df = add_indicators(df)
    datasets[tf] = df
    bw_min = df['bb_width'].min()
    bw_max = df['bb_width'].max()
    bw_count = (df['bb_width'] > 0.06).sum()
    print(f'{tf}: {len(df)} rows  bb_width=[{bw_min:.5f},{bw_max:.5f}]  >0.06={bw_count}')

df_tf = proc.align_multitimeframe_data(datasets['5m'], datasets['15m'], datasets['1h'])

bb_cols = [c for c in df_tf.columns if 'bb' in c or 'ema' in c or 'rsi' in c or 'atr' in c]
print('Indicator cols in aligned frame:', bb_cols)
print('Aligned bb_width >0.06:', (df_tf['bb_width'] > 0.06).sum())
print('Aligned ema_200 nonNull:', df_tf['ema_200'].notna().sum())

# Run Phase 6 Baseline A exactly
p4s1_cfg = {
    'template_type': 'bollinger_expansion_breakout',
    'trend_filter': 'ema_200',
    'regime_filter_mode': 'no_filter',
    'tp_atr_mult': 2.5, 'sl_atr_mult': 1.8,
    'rsi_overbought': 75, 'rsi_oversold': 30,
    'adx_thresh': 20, 'wick_ratio_thresh': 0.45
}
p4s2_cfg = {
    'template_type': 'atr_volatility_expansion',
    'trend_filter': None,
    'regime_filter_mode': 'no_filter',
    'tp_atr_mult': 2.5, 'sl_atr_mult': 1.5,
    'rsi_overbought': 75, 'rsi_oversold': 30,
    'adx_thresh': 20, 'wick_ratio_thresh': 0.45
}
p5s_cfg = {
    'template_type': 'bollinger_expansion_breakout',
    'trend_filter': None,
    'regime_filter_mode': 'strict',
    'tp_atr_mult': 2.5, 'sl_atr_mult': 1.8,
    'rsi_overbought': 75, 'rsi_oversold': 30,
    'adx_thresh': 20, 'wick_ratio_thresh': 0.45
}

engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)
multi_engine = MultiPositionBacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005, max_positions=3, cooldown_candles=5)

# Test individual strategies
for name, cfg in [('BB Exp ema_200', p4s1_cfg), ('ATR Exp no-filter', p4s2_cfg), ('BB Exp strict', p5s_cfg)]:
    s = UniversalStrategyTemplate(cfg)
    res = engine.run(df_tf, s)
    m = res['metrics']
    print(f'{name}: PnL={m["net_pnl"]:.2f} trades={m["total_trades"]} '
          f'+/-/0={m["positive_months"]}/{m["negative_months"]}/{m["zero_months"]} PF={m["profit_factor"]:.2f}')

# Test Phase 6 Portfolio (Baseline A) via multi-engine
p6_port = PortfolioStrategy([
    UniversalStrategyTemplate(p5s_cfg),
    UniversalStrategyTemplate(p4s1_cfg),
    UniversalStrategyTemplate(p5s_cfg),  # third strat is same as strict
], conflict_rule='cancel')

port_cfg = {'monthly_risk_limit': 0.025, 'risk_limit_pct': 1.0, 'risk_throttle_mode': 'no_throttle', 'emergency_pause_threshold': 0.03}
res_p = multi_engine.run(df_tf, p6_port, port_cfg)
mp = res_p['metrics']
print(f'Phase 6 Portfolio via multi-engine: PnL={mp["net_pnl"]:.2f} trades={mp["total_trades"]} '
      f'+/-/0={mp["positive_months"]}/{mp["negative_months"]}/{mp["zero_months"]}')
