## 2026-06-30T12:00:30Z
You are teamwork_preview_worker.
Your coordination directory is C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\.agents\worker_m3_3.
Your task is to fix the timeframe resolution mismatch in the strategy backtests.

Specifically, perform the following:
1. **Upgrades to `UniversalStrategyTemplate` in `src/strategies/candidates.py`**:
   - Add support for a `"timeframe"` parameter in the strategy config (e.g. self.params.get("timeframe")).
   - In `get_signal`, if the strategy has `"timeframe": "1h"` (or if `close_1h` is in `df.columns` and the template type is not `"mtf_breakout"`), map all technical indicator inputs to their `_1h` suffixed versions in the DataFrame (e.g. `self._close = df["close_1h"].values`, `self._bb_upper = df["bb_upper_1h"].values`, `self._rsi_14 = df["rsi_14_1h"].values`, `self._atr_14 = df["atr_14_1h"].values`, etc.).
   - Make sure that when running a 1h strategy on a 5m DataFrame, signals are only checked at the first 5m candle of each hour (i.e. `open_time % 3600000 == 0`). If it is not the start of the hour, return `None` immediately.

2. **Upgrades to `runner.py` in `src/research/runner.py`**:
   - Evaluate the locked baseline comparisons (A, B, C, D, E) on `datasets["1h"]` instead of `df_tf` so that their backtests are run on the original 1h data and yield their correct positive historical returns.
   - Update the report filename to write the final Phase 8 report to `reports/phase8_alpha_distillation_mtf_fusion_report.md` instead of `phase7_ultradeep_monthly_consistency_research_report.md`.
   - Update the report content to say "Phase 8 Alpha Distillation, MTF Fusion and Monthly Consistency Report" and "Compiled by Antigravity Phase 8 Strategy Research Agent."
   - For portfolios constructed from the grid search leaderboard or baseline configurations, set the `"timeframe"` parameter of their sub-strategies to `"1h"` if they are evaluated on the 5m aligned DataFrame `df_tf`, ensuring they correctly map to the 1h indicators while running at 5m resolution with trailing and breakeven stops.

3. **Verify and Rerun**:
   - Write a unit test in `tests/test_phase8_verification.py` to verify that `"timeframe": "1h"` works lookahead-free on a 5m DataFrame.
   - Run `pytest` to ensure all tests pass.
   - Run `python -m src.research.runner` to execute the pipeline and generate the Phase 8 report.
   - Verify that the final report has positive baseline metrics and the chosen system passes the compliance audits.
   - Write your handoff.md and send a completion message to the orchestrator (conversation ID: 018d8f91-6e1d-4f25-b39d-d45240058a42).
