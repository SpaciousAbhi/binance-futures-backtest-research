## 2026-06-30T05:00:24Z

You are teamwork_preview_worker.
Your coordination directory is C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\.agents\worker_m3_1.
Your task is to implement the Multi-Timeframe (MTF) alignment and precise execution engine, multi-candidate fusion, dynamic risk scaling/exits, and the bad-month conversion / zero-month rescue modules for Phase 8.

Specifically, perform the following:
1. **Data Pipeline Upgrade (`src/data/processor.py` & `src/research/runner.py`)**:
   - Compute technical indicators on 1h, 15m, and 5m timeframes independently before merging.
   - For all timeframes, compute a `close_time` column: `df['close_time'] = df['open_time'] + duration_ms` (5m: 300000 ms, 15m: 900000 ms, 1h: 3600000 ms).
   - Align 1h and 15m enriched datasets onto the 5m DataFrame using `pd.merge_asof` with `direction='backward'` on `close_time`. Add suffixes like `_15m` and `_1h` to all columns from those timeframes.
   - Ensure the alignment is 100% lookahead-free.

2. **Precision Execution Engine (`src/backtest/engine.py`)**:
   - Extend `MultiPositionBacktestEngine` to support trailing stops and breakeven stop levels bar-by-bar on the 5m timeframe.
   - Support exponential decay for loss-streak size throttling: e.g. `risk_pct = base_risk_pct * (0.5 ** (consecutive_losses // 3))`.
   - Implement rolling MTD drawdown monitoring: if the current month's capital drawdown (based on starting month capital) exceeds 2.5% (or 3%), halt new entries for the rest of that month.

3. **Strategy Upgrades (`src/strategies/candidates.py`)**:
   - Create or update strategy modules to utilize MTF inputs. Add an MTF breakout strategy that uses:
     - 1h regime filters (e.g. Trend or Volatility expansion).
     - 15m Bollinger bands or swing levels for setups.
     - 5m entry triggers with delayed confirmation: after a 15m breakout occurs, require N (e.g., 2) consecutive 5m candles closing above the breakout level to confirm entry.
     - Support failed breakout reversals: if breakout fails and price closes back inside with a rejection wick, trigger a reversal entry.
     - Support retests: entry on a pullback retest of the breakout level with a 5m confirmation hammer/rejection wick.
     - Support tighter 5m stop placement (e.g. swing low or `1.5 * atr_5m`).

4. **Multi-Candidate Fusion Models (`src/strategies/portfolio.py`)**:
   - Develop or extend the portfolio strategy to support dynamic signal fusion:
     - **Signal Union & Intersection**: requiring agreement or resolving conflicts priority-wise.
     - **Priority Routing & Regime-based Switching**: dynamically assigning active candidates to regimes.
     - **Month-to-Date (MTD) Adaptive Fusion**: checking MTD trade count and day-of-month to activate/deactivate filler strategies (rebuilt Bollinger reversion low-activity filler) for zero-month rescue.

5. **Unit Tests & Verification (`tests/test_phase8_verification.py`)**:
   - Write a new unit test suite checking:
     - MTF lookahead-free alignment (using truncation/leak check).
     - Closed-candle compliance.
     - Tighter stop-loss and trailing exit updates.
     - Zero-month rescue trigger logic.
   - Run pytest and ensure all tests pass.

6. **Generate Report & Handoff**:
   - Run a backtest using your new systems and document the results.
   - Write your handoff.md with verification commands and code diff summaries.
   - Send a message to the orchestrator (conversation ID: 018d8f91-6e1d-4f25-b39d-d45240058a42) with a summary.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
