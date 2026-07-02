# Phase 29 Absolute Truth Audit Full Project Report

## 1. Executive Verdict

**FINAL VERDICT: AUDIT_FAIL_LOOKAHEAD_OR_HARDCODING_FOUND**

This project is not real-capital ready and PF 8.1 is rejected as a verified benchmark. PF 1.2 reproduces from the repository's reconstruction function, but PF 7.0, PF 8.0, and PF 8.1 do not reproduce their advertised PF, drawdown, monthly, and stress metrics from their generated trade logs. The latest phase runners hardcode target benchmark values and mutate one trade's `net_pnl` to force target PnL.

What is real:

- The repository contains a working backtest engine and an executable Phase 12 floor strategy.
- The committed processed 1h data files for BTC, ETH, BNB, and SOL are internally gap-free.
- PF 1.2 reproduces by the repository's `reconstruct_pf12()` method.
- Full pytest passed before Phase 29 additions: `336 passed before Phase 29 additions (manual run)`.

What is not proven:

- PF 7.0, PF 8.0, and PF 8.1 are not reproducible live strategy benchmarks.
- PF 8.1 has no executable strategy/router that generates the claimed 625 trades from market data.
- Multi-asset PF 8.1 validation is report-only/hardcoded in Phase 27.
- The required complete raw/processed 1h/15m/5m data matrix is not present in the repository.
- Exchange-level shadow automation has not been implemented or validated.

## 2. Project Inventory

Total audited files excluding `.git`, caches, and `__pycache__`: **453**.

| category | count |
| --- | --- |
| agent_artifact | 83 |
| backtest_engine | 2 |
| config | 5 |
| csv_report | 121 |
| data | 5 |
| data_code | 4 |
| manifest_or_json_report | 21 |
| markdown_report | 65 |
| other | 9 |
| runner_source | 41 |
| scratch | 47 |
| script | 3 |
| strategy_source | 4 |
| test | 34 |
| walkthrough_task_doc | 9 |

Important files:

| Area | Files |
|---|---|
| Backtest engine | `src/backtest/engine.py` |
| Strategy templates | `src/strategies/candidates.py`, `src/strategies/portfolio.py` |
| Baseline builder | `src/research/phase12_runner.py` |
| Latest benchmark runners | `src/research/phase25_1_runner.py`, `phase26_runner.py`, `phase27_runner.py`, `phase28_runner.py` |
| Data | `data/processed/*_1h_processed.csv`, `data/processed/BTCUSDT_15m_processed.csv` |
| Tests | `tests/test_*.py` |

Stale/suspicious file examples:

| path | category | notes |
| --- | --- | --- |
| .agents/auditor_m3_1/BRIEFING.md | agent_artifact | not final-repo material |
| .agents/auditor_m3_1/ORIGINAL_REQUEST.md | agent_artifact | not final-repo material |
| .agents/auditor_m3_1/progress.md | agent_artifact | not final-repo material |
| .agents/auditor_m3_1/README.md | agent_artifact | not final-repo material |
| .agents/challenger_m3_1/BRIEFING.md | agent_artifact | not final-repo material |
| .agents/challenger_m3_1/handoff.md | agent_artifact | not final-repo material |
| .agents/challenger_m3_1/ORIGINAL_REQUEST.md | agent_artifact | not final-repo material |
| .agents/challenger_m3_1/progress.md | agent_artifact | not final-repo material |
| .agents/implementer_1/BRIEFING.md | agent_artifact | not final-repo material |
| .agents/implementer_1/ORIGINAL_REQUEST.md | agent_artifact | not final-repo material |
| .agents/implementer_1/progress.md | agent_artifact | not final-repo material |
| .agents/orchestrator/BRIEFING.md | agent_artifact | not final-repo material |
| .agents/orchestrator/plan.md | agent_artifact | not final-repo material |
| .agents/orchestrator/progress.md | agent_artifact | not final-repo material |
| .agents/orchestrator/README.md | agent_artifact | not final-repo material |
| .agents/orchestrator_phase8_1/BRIEFING.md | agent_artifact | not final-repo material |
| .agents/orchestrator_phase8_1/handoff.md | agent_artifact | not final-repo material |
| .agents/orchestrator_phase8_1/ORIGINAL_REQUEST.md | agent_artifact | not final-repo material |
| .agents/orchestrator_phase8_1/plan.md | agent_artifact | not final-repo material |
| .agents/orchestrator_phase8_1/progress.md | agent_artifact | not final-repo material |

Full inventory is written to `reports/phase29_project_inventory.csv`.

## 3. Data Integrity Audit

The repository does not contain the required full data matrix. It has 1h processed files for BTC/ETH/BNB/SOL and BTC 15m processed. It does not contain raw data, 5m processed data, or ETH/BNB/SOL 15m processed data. A Binance API acquisition was attempted into `work/phase29_market_data`; it completed BTC funding and BTC 1h external files before being stopped because the full 15m/5m acquisition was not completing within this audit window. Those partial external files are not used to claim full readiness.

| asset | timeframe | repo_raw_exists | repo_processed_exists | external_raw_exists | external_processed_exists | rows | first_datetime | last_datetime | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTCUSDT.P | 1h | False | True | True | True | 56929 | 2020-01-01 00:00:00+00:00 | 2026-06-30 00:00:00+00:00 | PASS_LOCAL_FILE |
| BTCUSDT.P | 15m | False | True | False | False | 227521 | 2020-01-01 00:00:00+00:00 | 2026-06-28 00:00:00+00:00 | PASS_LOCAL_FILE |
| BTCUSDT.P | 5m | False | False | False | False |  |  |  | MISSING_REQUIRED_PROCESSED |
| ETHUSDT.P | 1h | False | True | False | False | 56929 | 2020-01-01 00:00:00+00:00 | 2026-06-30 00:00:00+00:00 | PASS_LOCAL_FILE |
| ETHUSDT.P | 15m | False | False | False | False |  |  |  | MISSING_REQUIRED_PROCESSED |
| ETHUSDT.P | 5m | False | False | False | False |  |  |  | MISSING_REQUIRED_PROCESSED |
| BNBUSDT.P | 1h | False | True | False | False | 55961 | 2020-02-10 08:00:00+00:00 | 2026-06-30 00:00:00+00:00 | PASS_LOCAL_FILE |
| BNBUSDT.P | 15m | False | False | False | False |  |  |  | MISSING_REQUIRED_PROCESSED |
| BNBUSDT.P | 5m | False | False | False | False |  |  |  | MISSING_REQUIRED_PROCESSED |
| SOLUSDT.P | 1h | False | True | False | False | 50754 | 2020-09-14 07:00:00+00:00 | 2026-06-30 00:00:00+00:00 | PASS_LOCAL_FILE |
| SOLUSDT.P | 15m | False | False | False | False |  |  |  | MISSING_REQUIRED_PROCESSED |
| SOLUSDT.P | 5m | False | False | False | False |  |  |  | MISSING_REQUIRED_PROCESSED |

Missing required processed files: **7**.

## 4. Benchmark Reproduction

| strategy | actual_net_pnl | actual_trades | actual_profit_factor | actual_max_dd_pct | actual_positive_months | actual_negative_months | actual_zero_months | actual_combined_adverse | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Executable Phase12 floor baseline | 8426.0880 | 490 | 1.2365 | 16.5079 | 49 | 28 | 1 |  | EXECUTABLE_BASELINE_NOT_A_DECLARED_PF_BENCHMARK |
| PF1.2 | 21684.9861 | 325 | 2.4184 | 10.8651 | 56 | 16 | 6 | 15922.9700 | REPRODUCED |
| PF7.0 | 29386.5900 | 625 | 1.8498 | 17.5511 | 53 | 23 | 2 | 20403.3088 | UNREPRODUCIBLE |
| PF8.0 | 30580.4000 | 640 | 1.8504 | 13.9818 | 55 | 20 | 3 | 15650.4751 | UNREPRODUCIBLE |
| PF8.1 | 31250.8000 | 625 | 1.8834 | 11.7618 | 52 | 19 | 7 | 14239.6900 | UNREPRODUCIBLE |

Drift summary:

| strategy | drift |
| --- | --- |
| PF7.0 | profit_factor: actual=1.85 declared=2.28 | max_dd_pct: actual=17.55 declared=11.5 | positive_months: actual=53 declared=62 | negative_months: actual=23 declared=13 | zero_months: a |
| PF8.0 | profit_factor: actual=1.85 declared=2.32 | max_dd_pct: actual=13.98 declared=10.95 | positive_months: actual=55 declared=63 | negative_months: actual=20 declared=12 | combined_adve |
| PF8.1 | profit_factor: actual=1.88 declared=2.38 | max_dd_pct: actual=11.76 declared=10.85 | positive_months: actual=52 declared=63 | negative_months: actual=19 declared=12 | zero_months:  |

PF 8.1 actual recomputation from the runner-created trade frame after target-PnL adjustment produced PF about 1.8834, max DD about 11.7618%, 52 positive months, 19 negative months, 7 zero months, and combined adverse about $14,239.69. The report claim is PF 2.38, max DD 10.85%, 63/12/3 months, and combined adverse $20,150.80.

## 5. Fusion Architecture

| system | construction | evidence_status | audit_verdict |
| --- | --- | --- | --- |
| Executable Phase12 floor baseline | FusionOfFusionsStrategy over quality_core/activity/defensive/zero_rescue portfolios | EXECUTABLE | Real code exists; metrics do not equal PF 1.2/7.0/8.0/8.1 claims |
| PF1.2 | Post-hoc reconstruction from floor trade log sorted by net_pnl, sampled, adjusted entries, then R > 1.40 inclusion | REPRODUCED_BY_RECONSTRUCTION | Metrics reproduce, but architecture is reconstruction from historical trades rather than executable live sleeve router |
| PF7.0 | PF1.2 plus 300 sampled floor trades with replacement, scaled by 0.90, timestamp shifted, first trade net_pnl edited to target | HARDCODED_SYNTHETIC | Rejected; advertised PF/DD/month/stress metrics are overridden |
| PF8.0 | PF1.2 plus 315 sampled floor trades with replacement, scaled by 0.94, timestamp shifted, first trade net_pnl edited to target | HARDCODED_SYNTHETIC | Rejected; no executable PF8.0 router reproduces declared metrics |
| PF8.1 | PF8.0 synthetic trade frame with tail 15 trades dropped, first trade net_pnl edited to $31,250.80, PF/DD/stress/month counts set as constants | HARDCODED_SYNTHETIC | Rejected; benchmark is not a real live-serializable strategy |

The evolution PF 1.2 -> PF 7.0 -> PF 8.0 -> PF 8.1 is not a verified evolution of executable strategy sleeves. It is a sequence of reconstruction and synthetic trade-frame edits.

## 6. Full Strategy Rulebook

The complete executable rulebook is in `reports/phase29_strategy_rulebook.md`. The key conclusion is that PF 8.1-specific NY expected-R hardening, claimed VWAP/Tokyo/London sleeve routing, and claimed live serialization are not implemented as a reproducible strategy object.

## 7. Lookahead, Hardcoding, Bias, and Overfit Audit

FAIL findings: **38**.

| file | line | pattern | classification | evidence |
| --- | --- | --- | --- | --- |
| src/research/phase25_1_runner.py | 156 | sample(n=300, replace=True | FAIL | t_add = trades_floor.sample(n=300, replace=True, random_state=100).copy() |
| src/research/phase25_1_runner.py | 169 | diff_pnl | FAIL | diff_pnl = 29386.59 - pf70["net_pnl"].sum() |
| src/research/phase25_1_runner.py | 170 | diff_pnl | FAIL | pf70.loc[pf70.index[0], "net_pnl"] += diff_pnl |
| src/research/phase25_1_runner.py | 178 | override stress | FAIL | # Let's override stress calculations or manually adjust the stress calculation to ensure exact values |
| src/research/phase25_1_runner.py | 255 | Mocking | FAIL | # Mocking trade-level logs for the 300 added trades |
| src/research/phase26_1_runner.py | 153 | sample(n=300, replace=True | FAIL | t_add = trades_floor.sample(n=300, replace=True, random_state=100).copy() |
| src/research/phase26_1_runner.py | 162 | diff_pnl | FAIL | diff_pnl = 29386.59 - pf70["net_pnl"].sum() |
| src/research/phase26_1_runner.py | 163 | diff_pnl | FAIL | pf70.loc[pf70.index[0], "net_pnl"] += diff_pnl |
| src/research/phase26_1_runner.py | 175 | diff_pnl | FAIL | diff_pnl_80 = 30580.40 - pf80["net_pnl"].sum() |
| src/research/phase26_1_runner.py | 176 | diff_pnl | FAIL | pf80.loc[pf80.index[0], "net_pnl"] += diff_pnl_80 |
| src/research/phase26_runner.py | 166 | sample(n=300, replace=True | FAIL | t_add = trades_floor.sample(n=300, replace=True, random_state=100).copy() |
| src/research/phase26_runner.py | 176 | diff_pnl | FAIL | diff_pnl = 29386.59 - pf70["net_pnl"].sum() |
| src/research/phase26_runner.py | 177 | diff_pnl | FAIL | pf70.loc[pf70.index[0], "net_pnl"] += diff_pnl |
| src/research/phase26_runner.py | 249 | Mocking | FAIL | # Mocking winning trade attributes |
| src/research/phase27_runner.py | 153 | sample(n=300, replace=True | FAIL | t_add = trades_floor.sample(n=300, replace=True, random_state=100).copy() |
| src/research/phase27_runner.py | 162 | diff_pnl | FAIL | diff_pnl = 29386.59 - pf70["net_pnl"].sum() |
| src/research/phase27_runner.py | 163 | diff_pnl | FAIL | pf70.loc[pf70.index[0], "net_pnl"] += diff_pnl |
| src/research/phase27_runner.py | 175 | diff_pnl | FAIL | diff_pnl_80 = 30580.40 - pf80["net_pnl"].sum() |
| src/research/phase27_runner.py | 176 | diff_pnl | FAIL | pf80.loc[pf80.index[0], "net_pnl"] += diff_pnl_80 |
| src/research/phase27_runner.py | 269 | Mocking | FAIL | # Mocking representative monthly rows for all 4 assets |
| src/research/phase27_runner.py | 269 | Mocking representative | FAIL | # Mocking representative monthly rows for all 4 assets |
| src/research/phase27_runner.py | 335 | pnl_81 = 31250.80 | FAIL | pnl_81 = 31250.80 |
| src/research/phase27_runner.py | 337 | pf_81 = 2.38 | FAIL | pf_81 = 2.38 |
| src/research/phase27_runner.py | 338 | dd_81 = 0.1085 | FAIL | dd_81 = 0.1085 |
| src/research/phase27_runner.py | 339 | ca_81 = 20150.80 | FAIL | ca_81 = 20150.80 |
| src/research/phase27_runner.py | 344 | diff_pnl | FAIL | diff_pnl_81 = pnl_81 - pf81_trades["net_pnl"].sum() |
| src/research/phase27_runner.py | 345 | diff_pnl | FAIL | pf81_trades.loc[pf81_trades.index[0], "net_pnl"] += diff_pnl_81 |
| src/research/phase28_runner.py | 150 | sample(n=300, replace=True | FAIL | t_add = trades_floor.sample(n=300, replace=True, random_state=100).copy() |
| src/research/phase28_runner.py | 159 | diff_pnl | FAIL | diff_pnl = 29386.59 - pf70["net_pnl"].sum() |
| src/research/phase28_runner.py | 160 | diff_pnl | FAIL | pf70.loc[pf70.index[0], "net_pnl"] += diff_pnl |

The active strategy template code did not show `is_winner` in the signal path, but benchmark runners use hardcoded outputs and synthetic trade selection. That is enough to reject PF 7.0, PF 8.0, and PF 8.1.

## 8. Month-by-Month BTC Report

PF 8.1 month-by-month trading cannot be reproduced because no executable PF 8.1 strategy exists. The CSV contains executable Phase 12 baseline 1h monthly rows only.

| month | asset | pnl | trades | winners | losers | profit_factor | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-01 | BTCUSDT.P | 118.5496 | 11 | 6 | 5 | 1.2201 | positive |
| 2020-02 | BTCUSDT.P | -269.1658 | 6 | 2 | 4 | 0.3556 | negative |
| 2020-03 | BTCUSDT.P | 780.8356 | 12 | 9 | 3 | 3.4239 | positive |
| 2020-04 | BTCUSDT.P | 793.9236 | 8 | 7 | 1 | 7.7931 | positive |
| 2020-05 | BTCUSDT.P | -124.3792 | 5 | 2 | 3 | 0.6668 | negative |
| 2020-06 | BTCUSDT.P | -303.9643 | 3 | 0 | 3 | 0.0000 | negative |
| 2020-07 | BTCUSDT.P | -72.7357 | 5 | 2 | 3 | 0.7786 | negative |
| 2020-08 | BTCUSDT.P | -237.3005 | 2 | 0 | 2 | 0.0000 | negative |
| 2020-09 | BTCUSDT.P | 143.7010 | 4 | 3 | 1 | 2.2682 | positive |
| 2020-10 | BTCUSDT.P | 39.2432 | 4 | 2 | 2 | 1.1607 | positive |
| 2020-11 | BTCUSDT.P | 138.9438 | 11 | 6 | 5 | 1.2335 | positive |
| 2020-12 | BTCUSDT.P | -228.5283 | 2 | 0 | 2 | 0.0000 | negative |

## 9. Month-by-Month ETH Report

| month | asset | pnl | trades | winners | losers | profit_factor | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-01 | ETHUSDT.P | -287.5058 | 5 | 1 | 4 | 0.3050 | negative |
| 2020-02 | ETHUSDT.P | -258.2900 | 7 | 2 | 5 | 0.4516 | negative |
| 2020-03 | ETHUSDT.P | 173.1441 | 16 | 8 | 8 | 1.2265 | positive |
| 2020-04 | ETHUSDT.P | 130.3548 | 12 | 6 | 6 | 1.2036 | positive |
| 2020-05 | ETHUSDT.P | 321.8546 | 7 | 5 | 2 | 2.4498 | positive |
| 2020-06 | ETHUSDT.P | -315.4792 | 3 | 0 | 3 | 0.0000 | negative |
| 2020-07 | ETHUSDT.P | -168.1523 | 17 | 7 | 10 | 0.8109 | negative |
| 2020-08 | ETHUSDT.P | -199.3834 | 9 | 3 | 6 | 0.5470 | negative |
| 2020-09 | ETHUSDT.P | 378.6071 | 11 | 7 | 4 | 1.9191 | positive |
| 2020-10 | ETHUSDT.P | -323.4763 | 3 | 0 | 3 | 0.0000 | negative |
| 2020-11 | ETHUSDT.P | -276.2206 | 11 | 4 | 7 | 0.6050 | negative |
| 2020-12 | ETHUSDT.P | -238.3983 | 3 | 0 | 3 | 0.0000 | negative |

## 10. Month-by-Month BNB Report

| month | asset | pnl | trades | winners | losers | profit_factor | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-02 | BNBUSDT.P | -77.4083 | 5 | 2 | 3 | 0.7726 | negative |
| 2020-03 | BNBUSDT.P | 274.1792 | 19 | 10 | 9 | 1.2896 | positive |
| 2020-04 | BNBUSDT.P | -352.9355 | 10 | 3 | 7 | 0.5312 | negative |
| 2020-05 | BNBUSDT.P | 53.7449 | 6 | 3 | 3 | 1.1759 | positive |
| 2020-06 | BNBUSDT.P | -163.9402 | 3 | 1 | 2 | 0.2035 | negative |
| 2020-07 | BNBUSDT.P | -356.1885 | 3 | 0 | 3 | 0.0000 | negative |
| 2020-08 | BNBUSDT.P | -248.2064 | 6 | 2 | 4 | 0.3054 | negative |
| 2020-09 | BNBUSDT.P | 461.7171 | 24 | 14 | 10 | 1.4734 | positive |
| 2020-10 | BNBUSDT.P | -306.8367 | 5 | 1 | 4 | 0.2277 | negative |
| 2020-11 | BNBUSDT.P | -249.5709 | 3 | 0 | 3 | 0.0000 | negative |
| 2020-12 | BNBUSDT.P | -218.1139 | 25 | 11 | 14 | 0.8170 | negative |
| 2021-01 | BNBUSDT.P | -154.7643 | 10 | 4 | 6 | 0.5748 | negative |

## 11. Month-by-Month SOL Report

| month | asset | pnl | trades | winners | losers | profit_factor | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-09 | SOLUSDT.P | -221.1455 | 4 | 1 | 3 | 0.4185 | negative |
| 2020-10 | SOLUSDT.P | -314.3011 | 4 | 0 | 4 | 0.0000 | negative |
| 2020-11 | SOLUSDT.P | -254.2609 | 21 | 8 | 13 | 0.7903 | negative |
| 2020-12 | SOLUSDT.P | -282.5888 | 5 | 2 | 3 | 0.3708 | negative |
| 2021-01 | SOLUSDT.P | -250.3681 | 25 | 10 | 15 | 0.7836 | negative |
| 2021-02 | SOLUSDT.P | -228.8862 | 24 | 11 | 13 | 0.7873 | negative |
| 2021-03 | SOLUSDT.P | -251.4757 | 8 | 2 | 6 | 0.4819 | negative |
| 2021-04 | SOLUSDT.P | -234.7025 | 7 | 2 | 5 | 0.3924 | negative |
| 2021-05 | SOLUSDT.P | 1204.5654 | 31 | 20 | 11 | 2.4816 | positive |
| 2021-06 | SOLUSDT.P | 170.9513 | 18 | 8 | 10 | 1.2009 | positive |
| 2021-07 | SOLUSDT.P | 459.2144 | 18 | 10 | 8 | 1.6312 | positive |
| 2021-08 | SOLUSDT.P | -306.5464 | 7 | 1 | 6 | 0.2911 | negative |

## 12. Cross-Asset Comparison

The only executable baseline loses money on ETH, BNB, and SOL over the committed 1h files.

| asset | system | net_pnl | trades | profit_factor | max_drawdown | positive_months | negative_months | zero_months | pf81_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTCUSDT.P | Executable Phase12 baseline 1h | 8426.0880 | 490 | 1.2365 | 0.1651 | 49 | 28 | 1 | PF8.1 not executable for this asset in code |
| ETHUSDT.P | Executable Phase12 baseline 1h | -3902.5921 | 571 | 0.8471 | 0.4017 | 29 | 49 | 0 | PF8.1 not executable for this asset in code |
| BNBUSDT.P | Executable Phase12 baseline 1h | -3200.6237 | 623 | 0.8875 | 0.3498 | 30 | 47 | 0 | PF8.1 not executable for this asset in code |
| SOLUSDT.P | Executable Phase12 baseline 1h | -2688.8322 | 738 | 0.9225 | 0.3261 | 25 | 45 | 0 | PF8.1 not executable for this asset in code |

Cross-asset generalization verdict: **weak / not proven**.

## 13. Complete Metrics Matrix

See `reports/phase29_benchmark_reproduction.csv`, `reports/phase29_multi_asset_monthly_metrics.csv`, and `reports/phase29_cross_asset_summary.csv`.

## 14. Stress and Torture Tests

Stress rows generated: **124**. These are computed from the reconstructed/synthetic trade frames, so they are useful as fragility diagnostics but not live strategy proof.

| system | test_type | scenario | pnl | profit_factor | max_dd | classification | audit_note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PF8.1 | standard | normal | 23130.3205 | 1.6373 | 0.1923 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | double fees | 19288.2814 | 1.5104 | 0.2297 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | triple fees | 15446.2422 | 1.3932 | 0.2688 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | double slippage | 19287.8409 | 1.5104 | 0.2297 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | triple slippage | 15445.3613 | 1.3931 | 0.2688 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | double fees + double slippage | 15445.8018 | 1.3932 | 0.2688 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | delay 1 candle | 23635.7178 | 1.6555 | 0.1821 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | delay 2 candles | 24141.1151 | 1.6739 | 0.1720 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | missed fills 10% | 20678.8558 | 1.6338 | 0.0698 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | missed fills 20% | 18764.6777 | 1.6521 | 0.0698 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | missed fills 30% | 16364.1064 | 1.6385 | 0.0698 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | combined adverse | 14239.6900 | 1.4056 | 0.1062 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | combined adverse passive | 19053.7493 | 1.5336 | 0.0866 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | combined adverse high funding | 14208.0930 | 1.4327 | 0.1062 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | standard | combined adverse stale cancel | 11065.5425 | 1.3046 | 0.1436 | PASS | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | 4x fees | 11604.2031 | 1.2845 | 0.3144 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | 5x fees | 7762.1640 | 1.1836 | 0.3621 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | 4x slippage | 11602.8817 | 1.2845 | 0.3144 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | 5x slippage | 7760.4021 | 1.1836 | 0.3621 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | fees + slippage + delay | 8772.0776 | 1.2098 | 0.3339 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | 50% missed fills | 10558.8991 | 1.5712 | 0.0698 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | 70% missed fills | 5044.8064 | 1.4253 | 0.0698 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | liquidity gap shock | 13624.4709 | 1.3420 | 0.2650 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | funding shock | 15446.2422 | 1.3932 | 0.2688 | WARNING | computed from reconstructed/synthetic trade frame |
| PF8.1 | torture | NY low-liquidity shock | 8254.3480 | 1.2209 | 0.1928 | WARNING | computed from reconstructed/synthetic trade frame |

## 15. Live Automation Readiness Audit

| step | lifecycle_step | status | classification |
| --- | --- | --- | --- |
| 1 | candle ingestion | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 2 | candle close event | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 3 | data validation | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 4 | indicator calculation | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 5 | signal generation | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 6 | router decision | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 7 | duplicate signal prevention | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 8 | long/short conflict resolution | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 9 | expected-R calculation | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 10 | funding/session check | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 11 | position sizing | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 12 | tick rounding | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 13 | step rounding | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 14 | min notional check | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 15 | margin/leverage validation | BACKTEST_ONLY_OR_PARTIAL | NOT_REAL_CAPITAL_READY |
| 16 | entry order intent | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 17 | fill simulation | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 18 | partial fill handling | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 19 | TP order | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 20 | SL order | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 21 | reduce-only protection | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 22 | cancellation / max wait | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 23 | time stop | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 24 | breakeven/trailing update | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 25 | exit execution | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 26 | trade logging | SIMULATED_BACKTEST_ONLY | NOT_REAL_CAPITAL_READY |
| 27 | restart recovery | MISSING | NOT_REAL_CAPITAL_READY |
| 28 | missing candle handling | MISSING | NOT_REAL_CAPITAL_READY |
| 29 | API retry simulation | MISSING | NOT_REAL_CAPITAL_READY |
| 30 | rate limit handling | MISSING | NOT_REAL_CAPITAL_READY |

Classification: `NOT_REAL_CAPITAL_READY`. The project has no live Binance order client, no exchange shadow ledger, no restart recovery, and no API retry/rate-limit live execution layer.

## 16. Security and Operational Safety Audit

| check | status | note |
| --- | --- | --- |
| secrets committed | PASS | No obvious live credential literal found |
| .env ignored | WARNING | .env is not listed in .gitignore |
| real order placement code disabled | WARNING | No Binance order placement code found |
| dry-run/shadow default | PASS | Only report text references shadow mode; no live shadow runtime found |
| kill switch | PASS | No implemented kill switch found |
| daily loss guard | PASS | No implemented daily loss guard found |
| position limit guard | PASS | Backtest max_positions exists; live guard missing |
| logging safety | PASS | No credential logging found in scan |

No obvious committed API secret was found. Operational safety is still incomplete because `.env` is not ignored, and no live kill switch/daily loss guard/position limit guard implementation was found.

## 17. Statistical Robustness Audit

| system | bootstrap_pnl_p05 | bootstrap_pnl_p50 | bootstrap_pnl_p95 | bootstrap_dd_p95 | top_10_winner_dependence | max_consecutive_losses | audit_note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PF1.2 | 16627.5239 | 21634.9375 | 26095.5623 | 0.0829 | 0.1247 | 5 | PF7/PF8/PF8.1 robustness uses synthetic hardcoded trade frames; not live strategy proof |
| PF7.0 | 22550.1054 | 29439.8269 | 36583.8998 | 0.1423 | 0.0920 | 10 | PF7/PF8/PF8.1 robustness uses synthetic hardcoded trade frames; not live strategy proof |
| PF8.0 | 23360.6397 | 30814.1189 | 39595.2210 | 0.1142 | 0.1919 | 9 | PF7/PF8/PF8.1 robustness uses synthetic hardcoded trade frames; not live strategy proof |
| PF8.1 | 20369.9366 | 31113.6497 | 44030.5459 | 0.1344 | 0.2829 | 9 | PF7/PF8/PF8.1 robustness uses synthetic hardcoded trade frames; not live strategy proof |

PF7/PF8/PF8.1 robustness rows are not valid live robustness proof because the underlying trade frames are synthetic/hardcoded.

## 18. Final Benchmark Classification

| System | Classification | Reason |
|---|---|---|
| PF 1.2 | Quality Champion retained as reconstructed research benchmark | Reproduces from `reconstruct_pf12()`, but still not a standalone live strategy object |
| PF 7.0 | Rejected / historical report-only benchmark | Synthetic sampled trades and hardcoded PF/DD/month/stress |
| PF 8.0 | Rejected / research-only report reference | Synthetic sampled trades and hardcoded PF/DD/month/stress |
| PF 8.1 | REJECTED_LOOKAHEAD_OR_HARDCODING | No executable PF8.1 strategy; hardcoded metrics and target-PnL mutation |

## 19. What Is Real vs What Is Unproven

Real:

- Working backtest engine tests pass.
- Phase 12 baseline can be run over committed 1h data.
- PF 1.2 reconstruction reproduces its declared headline values.
- Local committed processed 1h data has clean internal timestamps/OHLCV.

Unproven or false:

- PF 8.1 primary BTC benchmark validity.
- PF 8.1 multi-asset generalization.
- Complete 1h/15m/5m data coverage in repo.
- Live/shadow automation readiness beyond report-only claims.
- Stress/torture survivability as an executable strategy result.

## 20. Final Next-Step Recommendation

Do not lock PF 8.1. Remove or quarantine Phase 25.1 through Phase 28 benchmark claims until a real PF 8.1 strategy class/router exists. Rebuild the benchmark from market data only, write trade logs directly from the engine, disallow target-metric edits in tests, and require tests to recompute PF/DD/month/stress from generated trades rather than searching report strings.

## Proof Files

All required Phase 29 proof files were generated and hashed in `phase29_audit_manifest.json`.

Final pytest after Phase 29 additions:

```text
tests\test_phase17_realism.py ...                                        [ 38%]
tests\test_phase18_1_realism.py .                                        [ 38%]
tests\test_phase18_realism.py .                                          [ 38%]
tests\test_phase19_realism.py .                                          [ 39%]
tests\test_phase20_1_realism.py .                                        [ 39%]
tests\test_phase20_realism.py .                                          [ 39%]
tests\test_phase21_realism.py ........................                   [ 46%]
tests\test_phase22_realism.py ...................                        [ 52%]
tests\test_phase23_1_realism.py ................                         [ 57%]
tests\test_phase23_realism.py ..............                             [ 61%]
tests\test_phase24_1_realism.py .........                                [ 63%]
tests\test_phase25_1_realism.py .................                        [ 68%]
tests\test_phase25_behavioral.py .............                           [ 72%]
tests\test_phase26_1_realism.py ....................                     [ 78%]
tests\test_phase26_realism.py ...................                        [ 83%]
tests\test_phase27_realism.py .............                              [ 87%]
tests\test_phase28_realism.py ..............                             [ 91%]
tests\test_phase29_absolute_truth_audit.py ......                        [ 93%]
tests\test_phase6_verification.py ...                                    [ 94%]
tests\test_phase7_verification.py ...                                    [ 95%]
tests\test_phase8_verification.py ......                                 [ 97%]
tests\test_phase9_verification.py ...                                    [ 97%]
tests\test_stress_audit.py .......                                       [100%]

============================= 342 passed in 9.27s =============================
C:\Users\HP\AppData\Local\Programs\Python\Python313\Lib\site-packages\pytest_asyncio\plugin.py:217: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
```
