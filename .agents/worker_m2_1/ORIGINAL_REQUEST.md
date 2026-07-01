## 2026-06-30T04:46:10Z (UTC)

You are teamwork_preview_worker.
Your coordination directory is C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\.agents\worker_m2_1.
Your task is to implement the alpha distillation for Milestone 2.

Steps to perform:
1. Initialize your BRIEFING.md and progress.md.
2. Read the top 3 configurations from the "leaderboard" key of C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\reports\search_checkpoint.json. These three configurations will form the portfolio for Candidate B (PnL Quality Champion).
3. Write a python script to run backtests on the BTCUSDT 1h data (which can be loaded/enriched using the functions in `src/research/runner.py`) for all five candidates:
   - **Candidate A:** Portfolio of p5_best_single_cfg, p4_strat_1_cfg, p6_strat_3_cfg. Run under MultiPositionBacktestEngine with max_positions=3, cooldown_candles=5.
   - **Candidate B:** Portfolio of the top 3 configurations from search_checkpoint.json. Run under MultiPositionBacktestEngine with max_positions=3, cooldown_candles=5.
   - **Candidate C:** Single strategy of p5_best_single_cfg. Run under BacktestEngine.
   - **Candidate D:** Single strategy of rebuilt_filler_cfg. Run under BacktestEngine.
   - **Candidate E:** Portfolio Candidate A run under MultiPositionBacktestEngine with delay_candles=1 passed to run().
4. In the script, for each candidate, extract the trade logs (exit_time/entry_time, side, net_pnl, etc.) and calculate:
   - Trade count, win rate, profit factor, average winner, average loser, average holding time (in candles), max MFE, max MAE.
   - Attributing performance (net PnL and trade counts) by market regime columns (e.g. regime_bull_trend, regime_bear_trend, regime_sideways_range, etc. active at trade entry index).
5. Compute the three matrices:
   - **Trade-overlap matrix**: For each pair of candidates, compute the percentage of shared trades (trades entering at the same timestamp).
   - **Monthly complement matrix**: For each candidate, identify its losing/zero months. Then for each pair of candidates (C1, C2), calculate the net PnL of C2 during C1's losing/zero months.
   - **Regime complement matrix**: Attribute net PnL of each candidate across each of the 7 regimes.
6. Write the resulting matrices and metrics to C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\reports\distillation_matrices.json.
7. Generate strengths & weaknesses analysis tables.
8. Document all findings and tables in C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\.agents\worker_m2_1\handoff.md and report completion to the orchestrator (conversation ID: 018d8f91-6e1d-4f25-b39d-d45240058a42).

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
