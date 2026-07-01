# Milestone 1 Handoff Report: Exploration & Design Analysis

## 1. Observation

Based on a thorough investigation of the codebase under `src` and `tests`, the following items were observed:

### A. Backtesting Engine (`src/backtest/engine.py`)
- **Single Active Position Limitation:** The current backtester loop (Lines 37-39, 61-110) handles only a single concurrent active position (`self.active_position = None` or `dict`). This limits the system from simulating a real multi-strategy portfolio where sub-strategies hold concurrent positions.
- **Simplified Monthly Metrics:** Monthly metrics calculation (Lines 432-443) only aggregates `net_pnl` and does not track monthly trades, wins, losses, win rates, gross PnL, fees, slippage, funding costs, active modules, or market regimes:
  ```python
  # Monthly aggregation
  trades_df["exit_datetime_parsed"] = pd.to_datetime(trades_df["exit_datetime"]).dt.tz_localize(None)
  trades_df["month"] = trades_df["exit_datetime_parsed"].dt.to_period("M")
  monthly_groups = trades_df.groupby("month")["net_pnl"].sum()
  # Reindex to contain ALL tested months (zero-trade months filled with 0.0)
  monthly_groups = monthly_groups.reindex(all_months, fill_value=0.0)
  ```

### B. Reporting Framework (`src/reporting/reporter.py`)
- **Leaderboard Duplication:** Leaderboard entries (Lines 62-70) are formatted directly from the candidate list without deduplication checks.
- **Simplistic Monthly Table:** The month-by-month table (Lines 97-104) is limited to `Month`, `Net PnL ($)`, and `Status` fields:
  ```python
  # Month-by-Month report for selected system
  content.append("\n### Month-by-Month Performance Table")
  content.append("| Month | Net PnL ($) | Status |")
  content.append("|---|---|---|")
  ```

### C. Candidate Search & Optimization (`src/research/runner.py`)
- **Leaderboard Appending Bug:** Line 220-223 appends candidates to the leaderboard on every run without checking for duplicates:
  ```python
  for config, metrics in passed_candidates[:10]:
      leaderboard.append({
          "config": config,
          "metrics": metrics
      })
  ```
- **Shallow Search Space:** The parameter grid (Lines 144-154) generates only 5,400 permutations, which is far below the target 1,000,000 configurations.
- **Stage 3 Pruning Logic:** Stage 3 pruning (Lines 204-208) checks only training drawdown and does not evaluate monthly consistency as required (pruning if negative months count > limit, or zero-trade months appear).
- **Simple Walk-Forward Optimization:** Walk-forward splits (Lines 268-287) search a very narrow local space (9 permutations) around the best global config instead of running a full candidate search on each training split.

### D. Portfolio Strategy (`src/strategies/portfolio.py`)
- **Lack of Advanced Risk Controls:** The current implementation (Lines 25-59) consolidates signals and resolves simple conflicts (cancel/long/short priority) but does not implement loss-streak cooldowns, position limits, or caps on open risk.
- **Lack of Feedback Loop:** There is no mechanism in `engine.py` to notify `PortfolioStrategy` when trades are closed, preventing it from tracking sub-strategy performance or consecutive loss counts.

### E. Existing Unit Tests (`tests/test_backtest.py`)
- Running `pytest` confirms that all 10 unit tests pass successfully.

---

## 2. Logic Chain

From the observations above, we deduce the following:
1. **R1 Upgrades (Engine & Reporting):**
   - **Deduplication:** We must filter candidates in `runner.py` based on `config_hash` or metrics signature before writing to the checkpoint or leaderboard.
   - **Monthly metrics:** `_calculate_metrics` in `engine.py` needs to return a dictionary of rich monthly stats, which requires passing the full `df` to extract regime labels.
   - **Monthly report:** `reporter.py` must print a table with all 15 columns requested in R1.
2. **R2 Upgrades (Regime Engine):**
   - We must classify each bar `i` using only data up to `i`. We can vectorize this in `src/features/indicators.py` using `np.select` for high efficiency, adding a `"regime"` column to `df`.
3. **R3 Upgrades (Candidate Diversity & Scale):**
   - We need to expand `UniversalStrategyTemplate` and `grid_params` in `runner.py` to support 7 distinct families (Trend, Breakout, Sweep, Mean Reversion, Session, Funding, and Risk Controls).
   - To make 1,000,000 configuration sweeps computationally feasible, we must implement parallel processing using `ProcessPoolExecutor` and apply aggressive Stage 1 subperiod pruning.
4. **R4 Upgrades (Walk-Forward & Portfolio Optimization):**
   - For walk-forward validation, the search should sweep a representative grid on the train range of each split and apply OOS test data.
   - For portfolio risk controls, `engine.py` must notify the strategy of closed trades (using an `on_trade_closed(trade)` hook) so the strategy can track consecutive losses and trigger cooldowns.
   - To support concurrent positions, `engine.py` must track a list of `active_positions = []` and manage SL/TP and margins for each separately.
5. **R5 Upgrades (Verification & Audits):**
   - `SystemAuditor` must be updated to run and report all audits (data, signal, trade, funding, cost, walk-forward, portfolio, no-fake static audit checking lookahead/leakage).
6. **R6 Upgrades (Final Report):**
   - We must export all results, staged pruning numbers, and final verdicts (`PASS_STRATEGY_FOUND` or `FAIL_NO_STRATEGY_FOUND`) to `reports/phase3_regime_adaptive_strategy_research_report.md`.

---

## 3. Caveats

- **Computation Limit:** A full 1,000,000 configurations sweep may take significant time depending on CPU power. The implementer must tune the Stage 1 subperiod size (e.g. first 6 months of data) and prune unviable parameter combinations before running them.
- **Multiple Positions Risk Sizing:** Concurrently open positions increase risk. Total leverage must be capped at 5x of current capital to prevent immediate bankruptcy.

---

## 4. Conclusion

The current codebase is functional and passes all tests, but contains key limitations (single position execution, narrow search space, missing monthly statistics, lack of true regime adaptation, and missing portfolio risk controls). 
To achieve Phase 3 requirements:
1. Upgrade `engine.py` to support multiple concurrent positions and rich monthly metrics.
2. Implement a `RegimeDetector` in `indicators.py` using lookahead-free rules.
3. Expand strategy families and grid parameters in `candidates.py` and `runner.py` to support 1M configurations with multiprocessing.
4. Add an `on_trade_closed` feedback hook to trigger loss-streak cooldowns and portfolio risk limits.
5. Generate the Phase 3 Markdown report with strict acceptance criteria matching.

---

## 5. Verification Method

To verify the implementation of the proposed changes:
1. Run `pytest tests/` to confirm that all existing unit tests still pass.
2. Add new unit tests in `tests/test_backtest.py` to verify:
   - Concurrent position handling in `BacktestEngine`.
   - Multi-strategy loss-streak cooldown trigger.
   - Non-leaking property of the regime detection engine.
3. Execute the full search and pipeline script `python -m src.research.runner` and verify:
   - Checkpoint creation and resumability.
   - Output of `reports/phase3_regime_adaptive_strategy_research_report.md` with complete month-by-month table and a clear `PASS_STRATEGY_FOUND` or `FAIL_NO_STRATEGY_FOUND` verdict.
