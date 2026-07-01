# Test Infrastructure & Specification (TEST_INFRA.md)

This document details the testing framework, philosophy, and test tier architecture for the Binance Futures Backtesting and Research Pipeline.

---

## 1. Test Philosophy

To guarantee the reliability and integrity of the quantitative trading strategy pipeline, the test suite adheres to three core tenets:

1. **Opaque-Box Testing**: Core engine and optimization components are evaluated through their public API interfaces. We assert behavior and numerical outcomes rather than checking implementation details, allowing internal refactorings without breaking tests.
2. **Requirement-Driven Verification**: Every test aligns with mathematical, functional, and trading constraints specified by the system design. These include exact fee/slippage drag, risk limit enforcement, and capital boundaries.
3. **Lookahead-Free Enforcement**: Lookahead bias is the primary cause of backtest out-of-sample failure. The test framework implements active lookahead audits, verifying that at any bar index `i`, no component (indicators, signals, regime filters, splits) accesses data at index `j > i`.

---

## 2. Inventory of the 6 Core Features

The test suite validates six core pipeline capabilities:

### Feature 1: Leaderboard & Deduplication / Month Metrics Reporting
- **Deduplication**: Ensures that the strategy leaderboard only stores unique parameter configurations. Submitting duplicate configurations must either be ignored or update existing entries rather than creating duplicate ranks.
- **Monthly Reporting**: Verifies that monthly metrics are calculated on a complete calendar basis. Zero-trade months must be correctly identified and factored into positive/zero/negative month aggregates (preventing omission biases).

### Feature 2: Regime Engine (Lookahead-Free Market States)
- **Regime Labeling**: Classifies market states (e.g., Trending-Long, Trending-Short, Mean-Reverting, Volatile) dynamically.
- **Lookahead-Free Verification**: Asserts that regime classification at index `i` is identical whether run on the full dataset or a truncated dataset ending at `i`.

### Feature 3: Candidate Search Parameter Sweep with Pruning and Checkpointing
- **Staged Pruning**: Evaluates parameter configurations through successive stages (Stage 1: subperiod sanity check; Stage 2: full training consistency; Stage 3: drawdown/expectancy checks) to prune poor configurations early.
- **Checkpointing**: Periodically dumps state (tested hashes and current leaderboard) to JSON. If interrupted, the search must successfully resume and skip already evaluated parameter hashes.

### Feature 4: 4-Split Walk-Forward Optimization
- **Split Ranges**: Partitions data into 4 non-overlapping train/test validation periods.
- **Out-of-Sample Isolation**: Verifies that the training phase of split `k` cannot access testing data of split `k`, and test performance is evaluated purely on unseen out-of-sample data.

### Feature 5: Multi-Position Portfolio Execution with Risk Limits and Cooldowns
- **Concurrent Positions Cap**: Enforces limits on the maximum number of active positions held simultaneously.
- **Risk Limits**: Restricts position sizes or entry signals based on portfolio drawdown or equity risk limits.
- **Cooldowns**: Prevents new entries for a strategy or the entire portfolio for a specified duration (cooldown period) after a loss or specific exit.

### Feature 6: Stress Testing and Multi-Level Auditing
- **Stress Tests**: Simulates adverse execution environments, including high maker/taker fees, extreme slippage, execution delay, and missed fills.
- **Multi-Level Auditing**: Evaluates both structural code integrity (static "No-Fake" audit searching for hardcoded dates/trade IDs) and dynamic logic consistency (signal/trade execution audits).

---

## 3. Test Architecture & Coverage Requirements

Tests are partitioned into 4 distinct Tiers to separate unit correctness from E2E integration and adversarial safety.

| Tier | Focus | Target Count |
|---|---|---|
| **Tier 1** | Unit & Component Verification (individual functions/classes) | >= 30 |
| **Tier 2** | Feature Integration & Flow (multi-component pipelines) | >= 30 |
| **Tier 3** | End-to-End System Workflows (complete run executions) | >= 6 |
| **Tier 4** | Adversarial, Stress & Audit Verifications (extreme scenarios) | >= 5 |
| **Total** | **Comprehensive E2E Phase 3 Suite** | **>= 71** |

### Tier 1: Unit & Component Verification (>=30 Tests)
T1.1 - T1.5: Leaderboard Deduplication (uniqueness of strategy configs, sorting, capacity limits).
T1.6 - T1.10: Monthly Metrics Aggregation (zero-trade months, full-period reindexing, status grouping).
T1.11 - T1.15: Regime Engine (lookahead-free label outputs, historical state dependency, state change triggers).
T1.16 - T1.20: Parameter Sweep Pruning (Stage 1 prune, Stage 2 prune, Stage 3 prune, parameter hashing).
T1.21 - T1.25: Walk-Forward Splits (split count, range boundaries, overlapping checks, train/test ratio).
T1.26 - T1.30: Portfolio & Cooldown Limits (concurrency limits, cooldown periods, single-strategy risk caps).

### Tier 2: Feature Integration & Flow (>=30 Tests)
T2.1 - T2.5: Integrated Regime Engine & Signal Filtering.
T2.6 - T2.10: Parameter Sweep Checkpoint Saving & Resuming.
T2.11 - T2.15: Multi-Position Backtest Engine Risk Limits (Drawdown limits, margin limits).
T2.16 - T2.20: Integrated Portfolio Strategy with cancel/priority rules.
T2.21 - T2.25: Integrated Walk-Forward Splits over 4 periods.
T2.26 - T2.30: Dynamic Indicator calculations under varying lengths.

### Tier 3: End-to-End System Workflows (>=6 Tests)
T3.1: Full Candidate Search E2E Pipeline (Sweep -> Pruning -> Checkpoint Dump -> Leaderboard).
T3.2: Complete 4-Split Walk-Forward E2E Pipeline with OOS parameter selection.
T3.3: Multi-Strategy Portfolio Backtest E2E with concurrent execution and risk limit triggers.
T3.4: Staged Parameter Sweep Checkpoint Restore & Continue E2E.
T3.5: Full Pipeline Integration (Data Audit -> Sweep -> Portfolio Comb -> E2E Run -> Report).
T3.6: Multi-period Regime Engine & Portfolio Strategy coordination E2E.

### Tier 4: Adversarial, Stress & Audit Verifications (>=5 Tests)
T4.1: Adversarial Fee & Slippage Stress Test.
T4.2: Missing Fills & Execution Delay Stress Test.
T4.3: Lookahead Auditor Validation (verifying that lookahead auditor correctly catches lookahead strategies).
T4.4: Static "No-Fake" Audit Verification (verifying auditor catches hardcoded dates/IDs).
T4.5: Account Liquidation & Bankruptcy Stop test.
