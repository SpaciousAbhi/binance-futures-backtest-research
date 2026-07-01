# Original User Request

## Initial Request — 2026-06-29T07:59:55Z

Build a regime-adaptive trading strategy system and portfolio optimizer for BTCUSDT Binance USD-M perpetual futures from 2020-01-01 to present, resolving Phase 2 limitations and executing a large-scale candidate search.

Working directory: C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest
Integrity mode: development

## Requirements

### R1. Backtesting Engine & Reporting Upgrades
Upgrade engine.py and reporter.py to:
- Resolve duplicate leaderboard entries and ensure complete candidate deduplication.
- Ensure monthly reports include: month, trades, wins, losses, win rate, gross PnL, fees, slippage, funding, net PnL, max drawdown, status (positive/negative/zero), active modules, regime notes, and weak-month notes.
- Strengthen Stage 3 month-consistency filtering.

### R2. Regime Detection Engine
Implement a robust, non-leaking regime engine using past/closed data only to classify market states (e.g., bull trend, bear trend, sideways range, high-vol trend, low-vol compression, chop/noise, liquidity sweep zone, funding extreme, session transition).

### R3. Candidate Diversity Search & Optimization
- Expand candidate search templates in candidates.py to support diverse families (Trend continuation, Breakout and breakout-retest, Failed breakout / liquidity sweep reversal, Mean reversion, Session range modules, Funding-aware modules, and Risk-control modules).
- Run a large-scale parameter search (up to 1,000,000 configurations or computationally feasible scale) with smart pruning, checkpointing, and resumability.

### R4. Walk-Forward Selection & Multi-Strategy Portfolio Optimization
- Implement a 4-split walk-forward optimization.
- Build a portfolio optimizer that combines diverse strategies (different regimes/logic, low overlap/correlation) with risk controls (position limits, loss-streak cooldowns, cap on open risk).

### R5. Verification, Stress Testing & Compliance Audits
- Run a stress-testing suite (normal, double/triple fees/slippage, execution delay, stale signals, missed fills, combined adverse).
- Execute audits (data, signal, trade, funding, cost, walk-forward, portfolio, no-fake static audit checking lookahead/leakage).

### R6. Comprehensive Final Report
Generate a single detailed Phase 3 report at reports/phase3_regime_adaptive_strategy_research_report.md with executive verdict, bug fixes, search scale, staged pruning table, top candidate leaderboard, rejected reasons, portfolio combination, month-by-month table, walk-forward results, stress tests, audits, and final verdict.

## Acceptance Criteria

### Strategy Search and Execution
- No hardcoded dates, months, or trade/signal IDs in strategy logic.
- Clean backtesting engine execution with 0 lookahead, 0 future leakage, and correct next-candle open execution.
- Clean reindexed monthly reporting including zero-trade months.

### Quality and Verdict Criteria
- Portfolio/system must satisfy target criteria: 0 negative months, 0 zero months, and >= 780 total trades to PASS; otherwise output FAIL_NO_STRATEGY_FOUND cleanly.
- All unit tests in tests/test_backtest.py pass.

==================================================
PHASE 3 CONTEXT & BACKGROUND
==================================================
Critical Phase 2 problems to fix:
1. Search was too shallow: only 5,400 configs, not enough.
2. Leaderboard had duplicate candidates.
3. Portfolio was not a real multi-strategy portfolio.
4. Stage 3 month-consistency filter was weak or ineffective.
5. Strategy selection was biased toward 2020-2021 bull market.
6. Best training profit factor was only 1.11, too weak.
7. Transaction costs destroyed edge.
8. Monthly report still did not include all required fields.
9. No true regime-adaptive strategy system was discovered.

==================================================
REGIME ENGINE DETAILS
==================================================
Classify every bar using only past/closed data into regimes. Labels must be live-known and non-leaking. Possible features: EMA slope, EMA50/EMA200, ADX, ATR percentile, BB width percentile, realized volatility, range compression/expansion, swing structure, distance from VWAP, wick/body ratio, funding percentile, session timing, previous session range, recent false breakout rate, recent strategy performance.

==================================================
STAGED FILTERING PIPELINE DETAILS
==================================================
Stage 0: Data and audit pass.
Stage 1: Candidate sanity (expectancy > 0, PF threshold, min trade count).
Stage 2: Multi-regime survival (separate performance checks on 2020-2021, 2022, 2023, 2024, 2025-present).
Stage 3: Monthly consistency (prune if negative months count > limit, or zero-trade months appear).
Stage 4: Walk-forward validation (Train 2020-2021/Test 2022, etc.).
Stage 5: Stress testing.
Stage 6: Portfolio construction (combine diverse, non-correlated candidates).
Stage 7: Final no-fake audit.

## Follow-up — 2026-06-30T04:40:20Z

Implement Phase 8 of the BTCUSDT perpetual futures research project, focusing on alpha distillation of champion candidates, multi-candidate fusion, multi-timeframe (MTF) execution, dynamic exits/risk limits, and bad-month conversion modules.

Working directory: C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest
Integrity mode: demo

## Requirements

### R1. Locked Champion Candidate Bank & Alpha Distillation
Evaluate and rerun the following candidates under the unified engine to extract core trade logs and metrics (trade counts, win rate, profit factor, average winner/loser, holding times, MFE/MAE, and performance by market regime):
- **Candidate A (Activity Champion):** Phase 6 Portfolio / Baseline A (731 trades, +$6,577.32 PnL)
- **Candidate B (PnL Quality Champion):** Top 3 Portfolio (619 trades, +$10,228.85 PnL)
- **Candidate C (PF/DD Champion):** Phase 5 Best Single Candidate (295 trades, +$6,872.29 PnL)
- **Candidate D (Positive Filler):** Rebuilt range reclaim filler
- **Candidate E (Confirmation Variant):** Delay-1-candle stress variant of Baseline A (778 trades, +$7,536.96 PnL)

Produce the following analysis matrices:
1. Trade-overlap matrix (unique vs. shared trades).
2. Monthly complement matrix (showing which candidates perform well during other candidates' losing months).
3. Regime complement matrix (attributing performance to specific market states).
4. Strengths & weaknesses analysis tables.

### R2. Multi-Candidate Fusion Models
Develop and test lookahead-free fusion systems to combine signals from the Candidate Bank:
- **Signal Union & Intersection:** Combining signals when conflicts are resolved or requiring agreement.
- **Priority Routing:** Selecting the signal with the highest OOS expectancy, regime confidence, or lower risk.
- **Regime-Based Switching:** Dynamically assigning candidates to market regimes (e.g. Candidate A in ranges, Candidate B in trend expansion, Candidate D for zero-month rescue).
- **Month-to-Date (MTD) Adaptive Fusion:** Using only closed-month trade count and PnL metrics to adjust risk or activate filler strategies.
- **Candidate Voting & Risk Allocation Ensembles:** Allocating risk or voting weights dynamically.

### R3. Multi-Timeframe (MTF) Execution & Precision Entry
Extend the execution logic to utilize lower timeframe data (15m and 5m candles) without lookahead bias (closed candles only):
- **MTF Setup-Trigger:** Aligning 1h regimes with 15m setups (retests, reclaims, breakouts) and triggering entries on 5m candles.
- **Delayed Confirmation Rules:** Designing live-compatible entries that wait for confirmation candle close to avoid immediate false breakout rejections.
- **Breakout Retests & Failed Breakout Reversals:** Entering on pullback reclaims or trading reversals when breakouts fail.
- **5m Precision Entry:** Triggering stops/targets on 5m candles to reduce stop distance and improve position sizing reward-to-risk.

### R4. Dynamic Exits & Risk Controls
Research and integrate dynamic, regime-dependent exits and risk scaling:
- Dynamic ATR or swing-based SL and TP bounds.
- Tighter stops on 5m entry confirmation.
- Risk halving after loss streaks, reduced risk in chop, and Month-to-Date capital limits.

### R5. Bad-Month Conversion Engine
Examine the specific negative and zero months of Candidates A and B. Build lookahead-free, universal rule-based repair modules targeting failure categories (e.g., false breakouts, cost erosion, low activity) to turn losing months positive or rescue zero months without overfitting.

### R6. High-Performance Research Lab Upgrades
Optimize research loop speed and capacity:
- Cache indicator values and MTF-aligned arrays.
- Support safe multiprocessing and deduplicate configuration/signal signatures.
- Implement 60-second checkpointing and search loop resume functionality.

### R7. Walk-Forward Validation & Stress Testing
Verify selected configurations under:
- Rolling out-of-sample walk-forward validation (Train 2020-21/Test 2022, Train 2020-22/Test 2023, Train 2020-23/Test 2024, Train 2020-24/Test 2025-present).
- The 14-scenario stress-testing suite (fees, slippage, delay, missed fills, combined adverse).

## Acceptance Criteria

### Verification & Compliance Audits
- Distillation matrices (trade overlap, monthly complement, regime complement) produced.
- Unit tests pass in tests/ covering MTF no-lookahead alignment, closed-candle rules, dynamic risk/exits correctness, and zero-month rescue no-lookahead.
- No future lookahead or cheating in risk throttle and filler activation (audited via signal and trade audits: "No obvious violation detected by current audit system").
- Selected system survives stress testing, maintaining positive net PnL in combined adverse.
- Main report generated at reports/phase8_alpha_distillation_mtf_fusion_report.md.

### Quality Metrics (Target System)
- 0 negative months (target)
- 0 zero months (target)
- 780+ total trades
- Higher profit factor and expectancy compared to Baseline A.
- If targets cannot be met, report the best possible audited system and fail honestly.

