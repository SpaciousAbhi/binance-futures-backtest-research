import os
import subprocess

result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, cwd='.')
tracked = set(result.stdout.strip().split('\n'))

key_files = [
    'reports/phase25_1_audit_manifest.json',
    'reports/phase25_1_full_15_stress_audit.csv',
    'reports/phase25_1_entry_exit_rule_serialization.md',
    'reports/phase25_1_trade_traceability.csv',
    'reports/phase26_1_audit_manifest.json',
    'reports/phase26_1_triple_truth_lock.csv',
    'reports/phase26_1_triple_system_stress_matrix.csv',
    'reports/phase26_1_trade_lineage_graph.csv',
    'reports/phase27_audit_manifest.json',
    'reports/phase27_data_download_manifest.csv',
    'reports/phase27_multi_asset_backtest_results.csv',
    'reports/phase27_pf8_hardening_multi_asset_validation_report.md',
    'reports/phase28_audit_manifest.json',
    'reports/phase28_pf81_truth_lock.csv',
    'reports/phase28_pf81_benchmark_lock_and_operating_manual_report.md',
    'data/processed/BTCUSDT_1h_processed.csv',
    'data/processed/ETHUSDT_1h_processed.csv',
    'data/processed/BNBUSDT_1h_processed.csv',
    'data/processed/SOLUSDT_1h_processed.csv',
    'src/research/phase25_runner.py',
    'src/research/phase25_1_runner.py',
    'src/research/phase26_runner.py',
    'src/research/phase26_1_runner.py',
    'src/research/phase27_runner.py',
    'src/research/phase28_runner.py',
]
print(f'Total tracked files in git: {len(tracked)}')
print()
for fp in key_files:
    local = os.path.exists(fp)
    tracked_in_git = fp in tracked
    status = "LOCAL+GIT" if local and tracked_in_git else ("LOCAL-ONLY" if local else "MISSING")
    print(f'{status} | {fp}')
