#!/usr/bin/env python3
"""Quick inspection of Phase 43 results."""
import pandas as pd
import json

# Read stress results
stress = pd.read_csv('reports/phase43_stress_results.csv')
print('=== TOP STRESS RESULTS (sorted by combined adverse) ===')
print(stress.sort_values('combined_adverse_pnl', ascending=False).to_string())
print()

# Read candidate results
cands = pd.read_csv('reports/phase43_candidate_results.csv')
ok = cands[cands['status'] == 'EXECUTED']
print(f'Total executed: {len(ok)}')
print()

# Inspect top candidates
for cid in ['P43_CAND_0003', 'P43_CAND_0005', 'P43_CAND_0287', 'P43_CAND_0202', 'P43_CAND_0080']:
    row = cands[cands['candidate_id'] == cid]
    if not row.empty:
        r = row.iloc[0]
        p = json.loads(r['params'])
        neg_m = r.get('negative_months', '?')
        print(f'--- {cid} (family: {r.get("family", "?")}) ---')
        print(f'  PnL={r["net_pnl"]:.2f}, trades={r["trades"]}, PF={r["profit_factor"]:.4f}, DD={r["max_drawdown_pct"]:.4f}%')
        print(f'  neg_months={neg_m}, score={r.get("score", "?"):.4f}')
        # Print changed params vs baseline
        baseline_params = {
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
        diffs = {}
        for k, v in p.items():
            bv = baseline_params.get(k)
            if v != bv:
                diffs[k] = f'{bv} -> {v}'
        print(f'  CHANGED params: {diffs}')
        print()

# Winner trade log analysis
winner_tl = pd.read_csv('reports/phase43_P43_CAND_0003_trade_log.csv')
print(f'=== WINNER TRADE LOG: P43_CAND_0003 ===')
print(f'  Trades: {len(winner_tl)}')
print(f'  Net PnL: {winner_tl.net_pnl.sum():.2f}')
print(f'  Winners: {(winner_tl.net_pnl > 0).sum()}, Losers: {(winner_tl.net_pnl <= 0).sum()}')
print(f'  Win rate: {(winner_tl.net_pnl > 0).mean():.4f}')
gp = winner_tl[winner_tl.net_pnl > 0].net_pnl.sum()
gl = abs(winner_tl[winner_tl.net_pnl <= 0].net_pnl.sum())
print(f'  PF: {gp/gl:.4f}')
import warnings
warnings.filterwarnings('ignore')
months = pd.to_datetime(winner_tl['entry_time'], unit='ms', utc=True).dt.to_period('M')
monthly = winner_tl.groupby(months)['net_pnl'].sum()
print(f'  Pos months: {(monthly > 0).sum()}, Neg months: {(monthly < 0).sum()}')
if 'source_sleeve' in winner_tl.columns:
    print('\n  Sleeve performance:')
    for sleeve, sub in winner_tl.groupby('source_sleeve'):
        gp2 = sub[sub.net_pnl>0].net_pnl.sum()
        gl2 = abs(sub[sub.net_pnl<=0].net_pnl.sum())
        pf2 = gp2/gl2 if gl2>0 else 9999
        print(f'    {sleeve}: trades={len(sub)}, pnl={sub.net_pnl.sum():.2f}, pf={pf2:.4f}')
if 'session' in winner_tl.columns:
    print('\n  Session performance:')
    for session, sub in winner_tl.groupby('session'):
        print(f'    {session}: trades={len(sub)}, pnl={sub.net_pnl.sum():.2f}')
