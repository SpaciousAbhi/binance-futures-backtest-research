#!/usr/bin/env python3
"""Deep comparison of top Phase 43 candidates vs baseline."""
import pandas as pd
import json
import sys
import warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from scripts.phase36_strategy1_decomposition_repair import load_market, compute_metrics, enrich_trade_log
from scripts.phase37_strategy1_1_second_stage_optimization import BASE_RISK, ENGINE_SETTINGS, CachedSignalStrategy, CandidateConfig, build_signal_cache, stable_hash
from scripts.phase40_stress_harness_repair import combined_adverse_pnl, pass_count, run_stress
from src.backtest.engine import MultiPositionBacktestEngine

df = load_market()
cache = build_signal_cache(df)

# Load candidate params
cands = pd.read_csv('reports/phase43_candidate_results.csv')

# Top candidates to compare
compare_ids = ['P43_CAND_0005', 'P43_CAND_0003', 'P43_CAND_0287', 'P43_CAND_0291']

STRAT_1_2_PARAMS = {
    'allowed_sessions': ['LONDON', 'NEW_YORK'],
    'allowed_sources': None,
    'disallowed_sources': ['Low-Activity Filler Long'],
    'max_abs_funding': 0.0015,
    'max_cost_to_risk': 0.15,
    'min_adx': 15,
    'min_atr_pct': 0.3,
    'min_bb_width': 0.03,
    'min_expected_R': 0.0,
    'min_projected_net_R': 0.85,
    'min_stop_atr': 0.0,
    'off_hours_min_expected_R': 0.0,
    'sl_atr_mult': 1.8,
    'tp_atr_mult': 3.0
}

for cid in compare_ids:
    row = cands[cands['candidate_id'] == cid]
    if row.empty:
        continue
    params = json.loads(row.iloc[0]['params'])
    config = CandidateConfig(cid, params, stable_hash(params), 'phase43')
    engine = MultiPositionBacktestEngine(**ENGINE_SETTINGS)
    result = engine.run(df, CachedSignalStrategy(config, cache), dict(BASE_RISK))
    trades = enrich_trade_log(result['trades'].copy())
    m = compute_metrics(trades)

    months = pd.to_datetime(trades['entry_time'], unit='ms', utc=True).dt.to_period('M')
    monthly = trades.groupby(months)['net_pnl'].sum()
    years = pd.to_datetime(trades['entry_time'], unit='ms', utc=True).dt.year
    yearly = trades.groupby(years)['net_pnl'].sum()

    stress_rows = run_stress(cid, trades, harness='FIXED')
    pc = pass_count(stress_rows)
    cadv = combined_adverse_pnl(stress_rows)

    changed = {}
    for k, v in params.items():
        bv = STRAT_1_2_PARAMS.get(k)
        if v != bv:
            changed[k] = f'{bv} -> {v}'

    print(f'=== {cid} ===')
    print(f'  Changed params: {changed}')
    print(f'  PnL: ${m["net_pnl"]:.2f}  | PF: {m["profit_factor"]:.4f} | DD: {m["max_drawdown_pct"]:.4f}%')
    print(f'  Trades: {m["trades"]} | Win rate: {m["win_rate"]:.4f}')
    print(f'  Pos months: {m["positive_months"]} | Neg months: {m["negative_months"]}')
    print(f'  Stress: {pc}/15 | Combined adverse: ${cadv:.2f}')
    print(f'  Avg win: ${m["avg_win"]:.2f} | Avg loss: ${m["avg_loss"]:.2f}')
    print(f'  Largest win: ${m["largest_win"]:.2f} | Largest loss: ${m["largest_loss"]:.2f}')
    print(f'  Expectancy: ${m["expectancy"]:.4f}')
    print(f'  Yearly PnL:')
    for y, pnl in yearly.items():
        print(f'    {y}: ${pnl:.2f}')
    print()

print('=== BASELINE (Strategy #1.2 P39_CAND_0551) ===')
btc_tl = pd.read_csv('reports/phase41_BTCUSDT_strategy1_2_trade_log.csv')
months = pd.to_datetime(btc_tl['entry_time'], unit='ms', utc=True).dt.to_period('M')
monthly = btc_tl.groupby(months)['net_pnl'].sum()
years = pd.to_datetime(btc_tl['entry_time'], unit='ms', utc=True).dt.year
yearly = btc_tl.groupby(years)['net_pnl'].sum()
print(f'  PnL: $11431.41 | PF: 1.4998 | DD: 7.9380%')
print(f'  Trades: 340 | Pos months: 46 | Neg months: 25')
print(f'  Stress: 15/15 | Combined adverse: $4323.12')
print(f'  Yearly PnL:')
for y, pnl in yearly.items():
    print(f'    {y}: ${pnl:.2f}')
