# Prompt Evolution Log

This document tracks the evolution of instructions and strategy requirements across project phases.

## Phase 1: Infrastructure and Baseline Strategies
*   **Prompt Goals**: Setup project layout, downloader, backtest engine, and run baseline strategies.
*   **Outcome**: Baseline strategies failed. Identified execution, fee, and slippage issues. Verdict: **FAIL**.

## Phase 2: Vectorization and Staged Grid Search
*   **Prompt Goals**: Optimize backtester with vectorized caching (100x speedup), implement transaction costs (fees, slippage, funding), and run a 5,400 configuration parameter sweep.
*   **Outcome**: Discovered Bollinger Breakout + EMA200 strategy with +$4,967.98 Net PnL on training data but high out-of-sample drawdown. Verdict: **FAIL**.

## Phase 3: Regime Classification and Concurrency
*   **Prompt Goals**: Build a regime classification engine and concurrent multi-position backtesting engine. Scan 4,000 configurations.
*   **Outcome**: Extreme 5% global drawdown rule froze the portfolio permanently in Month 1. Zero strategies survived. Verdict: **FAIL**.

## Phase 4: Forensic Calibration and Discovery
*   **Prompt Goals**: Diagnose the Phase 3 freeze, replace the global drawdown rule with a Month-to-Date risk reset (2.5% per month), and run a sweep over 600 configurations.
*   **Outcome**: Discovered a multi-strategy breakout portfolio generating +$7,113.12 Net PnL and 22.57% Max DD. Verdict: **FAIL** (failed trades count and monthly consistency targets).

## Phase 5: Monthly Consistency and Stress Audits
*   **Prompt Goals**: Audit and fix the stress testing suite (delays, missed fills, stale skips), build lookahead-free consecutive loss risk scaling, implement a low-activity filler module, and run a grid sweep.
*   **Outcome**: Stress testing engine fully fixed and verified in unit tests. Optimized search sweep promoted Bollinger Breakout candidate yielding +$6,872.29 Net PnL, 1.35 PF, and 6.96% Max DD. Verdict: **FAIL** (33 negative months, highlighting the extreme difficulty of monthly positive targets).
