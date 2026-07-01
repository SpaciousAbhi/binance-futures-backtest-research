# Phase 3 Project Execution Plan

## Objective
Implement a regime-adaptive trading strategy system and portfolio optimizer, resolving Phase 2 limitations (shallow search, duplicate candidates, weak month-consistency filter, transaction cost issues, incomplete reports) and passing all verification, stress testing, and audits.

## Dual-Track Architecture
We will run two tracks in parallel/sequence:
1. **E2E Testing Track**: Build the E2E test infra, design 4 tiers of test cases (~11 * N + max(5, N/2)), and publish `TEST_READY.md`.
2. **Implementation Track**: Upgrades to engine/reporting, implementation of regime engine, candidates expansion, walk-forward + portfolio optimizer, and stress testing/auditing.

## Detailed Plan & Milestones

### Milestone 1: Exploration and Codebase Audit
- **Goal**: Analyze the codebase, current strategies, reporting, and verify existing unit tests pass.
- **Verification**: Run `pytest tests/` via an Explorer/Worker to confirm baseline passes.

### Milestone 2: E2E Test Suite Design & Infrastructure (E2E Track)
- **Goal**: Create `TEST_INFRA.md` and implement the comprehensive E2E test suite covering:
  - Tier 1: Feature coverage (>=5 tests per feature).
  - Tier 2: Boundary and corner cases (>=5 tests per feature).
  - Tier 3: Cross-feature combinations (pairwise coverage).
  - Tier 4: Real-world application scenarios.
- **Verification**: Run the test runner, publish `TEST_READY.md` when 100% of test cases are ready.

### Milestone 3: Engine & Reporting Upgrades (Implementation Track)
- **Goal**: Resolve leaderboard duplicate entries, enhance monthly reports with all required fields (win rate, gross PnL, fees, slippage, funding, net PnL, max drawdown, status, active modules, regime/weak-month notes), and strengthen Stage 3 consistency filtering.
- **Verification**: Run unit tests on upgraded modules.

### Milestone 4: Regime Detection Engine & Candidates Expansion (Implementation Track)
- **Goal**:
  - Implement a robust, non-leaking regime engine using past/closed data.
  - Expand candidates in `candidates.py` to support Trend continuation, Breakout, Failed breakout/sweep, Mean reversion, Session range, Funding-aware, and Risk-control modules.
  - Set up parameter search grid and prune strategy.
- **Verification**: Strategy runner runs without lookahead or leakage.

### Milestone 5: Walk-Forward & Portfolio Optimization (Implementation Track)
- **Goal**:
  - Implement 4-split walk-forward optimization.
  - Build portfolio optimizer with position limits, loss-streak cooldowns, and open risk cap.
- **Verification**: Verify portfolio output has diverse, non-correlated candidates.

### Milestone 6: Verification, Stress Testing, and Audits (Implementation Track)
- **Goal**:
  - Run stress tests (adverse fee, slippage, delay, missed fills, etc.).
  - Run data, signal, trade, funding, cost, walk-forward, portfolio, and no-fake static audits.
- **Verification**: Forensic auditor clean report, all tests pass.

### Milestone 7: Final Synthesis and Reporting
- **Goal**: Synthesize results, check pass/fail criteria (0 negative months, 0 zero months, >=780 total trades to PASS, else FAIL_NO_STRATEGY_FOUND), and write `reports/phase3_regime_adaptive_strategy_research_report.md`.
- **Verification**: Check report presence, format, and accuracy.
