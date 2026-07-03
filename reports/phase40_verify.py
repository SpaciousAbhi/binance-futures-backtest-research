import sys, os, json, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest'

print('=== PHASE 40 DELIVERABLE VERIFICATION ===')
print()

# 1. Required reading files
print('[1] Required reading files:')
required_reads = [
    'AGENTS.md', 'README.md',
    'project_memory/CURRENT_HANDOFF.md',
    'project_memory/MASTER_PROJECT_STATE.md',
    'project_memory/PROJECT_RULEBOOK.md',
    'project_memory/BENCHMARK_REGISTRY.csv',
    'reports/phase39_1_strategy1_2_truth_reconciliation_report.md',
    'reports/phase39_1_stress_harness_audit.md',
    'reports/phase39_strategy1_2_vault.md',
]
for f in required_reads:
    exists = os.path.exists(f'{ROOT}/{f}')
    print(f'  {"PASS" if exists else "FAIL"}: {f}')

print()
# 2. Phase 40 output files
print('[2] Phase 40 output artifacts:')
phase40_files = [
    'reports/phase40_sync_and_safety_audit.csv',
    'reports/phase40_bug_documentation.csv',
    'reports/phase40_stress_comparison_matrix.csv',
    'reports/phase40_strategy_summaries.csv',
    'reports/phase40_promotion_gate_audit.csv',
    'reports/phase40_harness_before_after.csv',
    'reports/phase40_strategy_1_fixed_stress.csv',
    'reports/phase40_strategy_1.1_fixed_stress.csv',
    'reports/phase40_strategy_1.2_fixed_stress.csv',
    'reports/phase40_strategy1_2_final_decision.csv',
    'reports/phase40_stress_harness_repair_and_strategy1_2_final_decision_report.md',
    'reports/phase40_audit_manifest.json',
    'scripts/phase40_stress_harness_repair.py',
]
for f in phase40_files:
    exists = os.path.exists(f'{ROOT}/{f}')
    sz = os.path.getsize(f'{ROOT}/{f}') if exists else 0
    print(f'  {"PASS" if exists else "FAIL"}: {f} ({sz} bytes)')

print()
# 3. Stress results
print('[3] Stress harness repair verification:')
df = pd.read_csv(f'{ROOT}/reports/phase40_strategy_summaries.csv')
for _, row in df.iterrows():
    strat = row['strategy']
    old_s = row['old_stress_pass']
    new_s = row['new_stress_pass']
    old_ca = row['old_combined_adverse']
    new_ca = row['new_combined_adverse']
    print(f'  {strat}:')
    print(f'    Old stress: {old_s}/15 | New stress: {new_s}/15')
    print(f'    Old CA: ${old_ca:.2f} | New CA: ${new_ca:.2f}')

print()
# 4. Promotion decision
print('[4] Strategy #1.2 final decision:')
dec = pd.read_csv(f'{ROOT}/reports/phase40_strategy1_2_final_decision.csv').iloc[0]
print(f'  Candidate: {dec["candidate_id"]}')
print(f'  PnL: ${dec["net_pnl"]:.2f}')
print(f'  Trades: {dec["trades"]}')
print(f'  PF: {dec["profit_factor"]:.4f}')
print(f'  DD: {dec["max_drawdown_pct"]:.4f}%')
print(f'  Old stress: {dec["old_stress_pass"]}/15')
print(f'  New stress: {dec["new_stress_pass"]}/15')
print(f'  Decision: {dec["decision"]}')
print(f'  Verdict: {dec["verdict"]}')
print(f'  New status: {dec["new_status"]}')

print()
# 5. Benchmark registry
print('[5] BENCHMARK_REGISTRY.csv Strategy #1.2:')
bench = pd.read_csv(f'{ROOT}/project_memory/BENCHMARK_REGISTRY.csv')
row_12 = bench[bench['benchmark_name'].str.contains('P39_CAND_0551', na=False)].iloc[0]
print(f'  Status: {row_12["status"]}')
print(f'  Source: {row_12["source_phase"]}')

print()
# 6. CURRENT_HANDOFF.md
print('[6] CURRENT_HANDOFF.md key phrases:')
with open(f'{ROOT}/project_memory/CURRENT_HANDOFF.md', encoding='utf-8') as f:
    handoff = f.read()
phrases = [
    'Phase 40', 'PHASE40_PASS_STRATEGY1_2_CONFIRMED_AND_LOCKED',
    'CONFIRMED_PROMOTED', '15/15', 'NOT_REAL_CAPITAL_READY',
    '359.59', 'PASS=7 / FAIL=8', 'No final fusion was promoted',
]
for p in phrases:
    print(f'  {"PASS" if p in handoff else "FAIL"}: "{p}"')

print()
# 7. NEXT_PHASE_PLAN.md
print('[7] NEXT_PHASE_PLAN.md key phrases:')
with open(f'{ROOT}/project_memory/NEXT_PHASE_PLAN.md', encoding='utf-8') as f:
    npp = f.read()
for p in ['Phase 41', 'NOT_REAL_CAPITAL_READY', 'Phase 38', 'Phase 40']:
    print(f'  {"PASS" if p in npp else "FAIL"}: "{p}"')

print()
# 8. Git
import subprocess
result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True, cwd=ROOT)
print('[8] Git log (last 3):')
for line in result.stdout.strip().split('\n'):
    print(f'  {line}')
result2 = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, cwd=ROOT)
print(f'  Working tree clean: {result2.stdout.strip() == ""}')

print()
# 9. Vault
print('[9] phase39_strategy1_2_vault.md:')
with open(f'{ROOT}/reports/phase39_strategy1_2_vault.md', encoding='utf-8') as f:
    vault = f.read()
print(f'  Contains PROVISIONAL: {"PROVISIONAL" in vault}')
print(f'  Contains Phase 39.1: {"Phase 39.1" in vault}')

print()
# 10. Open problems
print('[10] OPEN_PROBLEMS.md stress resolved:')
with open(f'{ROOT}/project_memory/OPEN_PROBLEMS.md', encoding='utf-8') as f:
    op = f.read()
print(f'  Problem 0 RESOLVED: {"RESOLVED" in op}')

print()
print('=== VERIFICATION COMPLETE ===')
