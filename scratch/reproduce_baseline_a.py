"""
Quick Baseline A reproduction test.
Uses EXACTLY the same code as runner.py Phase 7 baseline section.
"""
import sys, os
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
    print(f'{tf}: {len(df)} rows')

df_tf = proc.align_multitimeframe_data(datasets['5m'], datasets['15m'], datasets['1h'])
print(f'Aligned: {len(df_tf)} rows')

# Quick signal-level check: how many candles fire BB expansion?
p4s1_cfg = {
    'template_type': 'bollinger_expansion_breakout',
    'trend_filter': 'ema_200',
    'regime_filter_mode': 'no_filter',
    'tp_atr_mult': 2.5, 'sl_atr_mult': 1.8,
    'rsi_overbought': 75, 'rsi_oversold': 30,
    'adx_thresh': 20, 'wick_ratio_thresh': 0.45
}

# Count potential BB expansion signals directly from the data
bb_exp_long = (df_tf['bb_width'] > 0.06) & (df_tf['close'] > df_tf['bb_upper']) & (df_tf['close'] > df_tf['ema_200'])
bb_exp_short = (df_tf['bb_width'] > 0.06) & (df_tf['close'] < df_tf['bb_lower']) & (df_tf['close'] < df_tf['ema_200'])
print(f'Raw BB expansion signals: Long={bb_exp_long.sum()}, Short={bb_exp_short.sum()}, Total={bb_exp_long.sum()+bb_exp_short.sum()}')
print(f'bb_width >0.06: {(df_tf["bb_width"]>0.06).sum()}')
print(f'close > bb_upper: {(df_tf["close"]>df_tf["bb_upper"]).sum()}')
print(f'close > ema_200: {(df_tf["close"]>df_tf["ema_200"]).sum()}')
print(f'bb_width >0.06 AND close>bb_upper: {((df_tf["bb_width"]>0.06) & (df_tf["close"]>df_tf["bb_upper"])).sum()}')

# Monthly bb_width >0.06 counts 
df_tf['month'] = pd.to_datetime(df_tf['open_time'], unit='ms', utc=True).dt.to_period('M')
monthly_bw = df_tf[df_tf['bb_width']>0.06].groupby('month').size()
print("\nMonthly bb_width>0.06 counts (sample):")
print(monthly_bw.head(20).to_string())

# Now check what Phase 7 report said: 2021-01 had 55 trades, 2020-03 had 30 trades
# These are monthly trade counts that imply many more signals than 3671/78months ~ 47/month
# 47 candles/month with bb_width>0.06 on 5m is plausible for 5-10 actual completed trades

# Verify with engine run
engine = BacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005)
strat_a = UniversalStrategyTemplate(p4s1_cfg)
res = engine.run(df_tf, strat_a)
m = res['metrics']
print(f'\nBaseline A (BB exp ema_200): PnL={m["net_pnl"]:.2f} trades={m["total_trades"]} +/-/0={m["positive_months"]}/{m["negative_months"]}/{m["zero_months"]}')
print(f'Expected from Phase 7 report: PnL=~3915 trades=~181 (single strat, Phase 7 Baseline ran via multi-engine portfolio)')

# Actually in Phase 7, Baseline A is run via multi_engine with portfolio of 3 strategies
# Let's run via multi-engine with the correct portfolio
p5s_cfg = {
    'template_type': 'bollinger_expansion_breakout',
    'trend_filter': None,
    'regime_filter_mode': 'strict',
    'tp_atr_mult': 2.5, 'sl_atr_mult': 1.8,
    'rsi_overbought': 75, 'rsi_oversold': 30,
    'adx_thresh': 20, 'wick_ratio_thresh': 0.45
}
p6s3_cfg = {
    'template_type': 'bollinger_expansion_breakout',
    'trend_filter': None,
    'regime_filter_mode': 'no_filter',
    'tp_atr_mult': 2.5, 'sl_atr_mult': 1.8,
    'rsi_overbought': 75, 'rsi_oversold': 30,
    'adx_thresh': 20, 'wick_ratio_thresh': 0.45
}
multi_engine = MultiPositionBacktestEngine(initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005, max_positions=3, cooldown_candles=5)
port = PortfolioStrategy([
    UniversalStrategyTemplate(p5s_cfg),
    UniversalStrategyTemplate(p4s1_cfg),
    UniversalStrategyTemplate(p6s3_cfg),
], conflict_rule='cancel')
port_cfg = {'monthly_risk_limit': 0.025, 'risk_limit_pct': 1.0}
res_p = multi_engine.run(df_tf, port, port_cfg)
mp = res_p['metrics']
print(f'\nPhase 6 Portfolio (multi-engine): PnL={mp["net_pnl"]:.2f} trades={mp["total_trades"]} +/-/0={mp["positive_months"]}/{mp["negative_months"]}/{mp["zero_months"]}')
print(f'Phase 7 report expected: PnL=6577.32, trades=731, 33/37/8')
