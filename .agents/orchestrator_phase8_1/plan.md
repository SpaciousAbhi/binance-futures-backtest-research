# Phase 8 Orchestration Plan

## Mission
Implement Phase 8 of the BTCUSDT perpetual futures research project in demo integrity mode.

## Milestones

### Milestone 1: Exploration, Audit & Handoff Verification
- **Objectives:**
  - Verify the existing codebase.
  - Review Phase 6/7 findings, baseline configurations, data files, and existing verification tests.
  - Setup test framework, verify the baseline metrics of Candidate A, B, C, D, E.
- **Verification:**
  - Unit tests run and pass.
  - Verification reports showing baseline stats for the 5 candidates.

### Milestone 2: Alpha Distillation & Feature/Regime Profiling
- **Objectives:**
  - Standardize metrics for Candidate A, B, C, D, E.
  - Produce overlap, monthly complement, and regime complement matrices.
  - Deliver `reports/distillation_matrices.json` and a markdown summary.

### Milestone 3: Multi-Timeframe (MTF) Data & Precise Execution Engine
- **Objectives:**
  - Extend the data processor to load and align 15m and 5m candle data with 1h candles without lookahead.
  - Modify or extend the backtest engine to support MTF execution: 1h regime, 15m setups, 5m precision entries/exits.
  - Implement delayed confirmation logic.
- **Verification:**
  - Unit tests verifying lookahead-free MTF alignment.

### Milestone 4: Multi-Candidate Fusion & Dynamic Exits/Risk Controls
- **Objectives:**
  - Implement looking-free fusion models: Signal Union/Intersection, Priority Routing, Regime-based switching, MTD Adaptive risk scaling, Candidate Voting Ensembles.
  - Implement dynamic exits (ATR/swing based limits) and risk controls (cooldowns, loss-streak throttles).
- **Verification:**
  - Tests checking fusion logic and risk limits.

### Milestone 5: Bad-Month Conversion & Zero-Month Rescue Modules
- **Objectives:**
  - Analyze and target negative/zero months of Candidates A and B.
  - Build universal, lookahead-free bad-month conversion and rescue modules.
  - Integrate these modules into the fusion system.
- **Verification:**
  - Verification that monthly metrics show improved positive month ratio and zero negative/zero months (or best possible).

### Milestone 6: High-Performance Lab Upgrades & Full Walk-Forward
- **Objectives:**
  - Implement caching, multiprocessing, and loop checkpointing/resume.
  - Run rolling out-of-sample walk-forward validation.
  - Run 14-scenario stress testing.

### Milestone 7: Compliance Audit & Comprehensive Final Report
- **Objectives:**
  - Run signal/trade/no-fake audits.
  - Compile the final report at `reports/phase8_alpha_distillation_mtf_fusion_report.md`.
  - Claim victory to Sentinel.
