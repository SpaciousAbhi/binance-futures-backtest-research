# Phase 30.1 — Research Lab Architecture Audit

## 1. Directory Structure Map
The project directory is structured as follows:

```
binance_futures_backtest/
├── AGENTS.md                  <- Short instruction file for AI agents
├── README.md                  <- Main repository overview
├── PROJECT.md                 <- Historical high-level project goals
├── project_memory/            <- Shared AI continuity directory
│   ├── CURRENT_HANDOFF.md
│   ├── MASTER_PROJECT_STATE.md
│   ├── PROJECT_RULEBOOK.md
│   ├── AI_WORK_PROTOCOL.md
│   ├── PHASE_HISTORY_TIMELINE.md
│   ├── BENCHMARK_REGISTRY.csv
│   └── MEMORY_INDEX.md
├── src/                       <- Core strategy and backtest modules
│   ├── backtest/              <- MultiPositionBacktestEngine and execution loop
│   ├── strategies/            <- Candidates strategy template library
│   ├── features/              <- Indicator computation library
│   └── research/              <- Historical phase runners (phase10 to phase28)
├── scripts/                   <- Execution utility scripts
├── tests/                     <- Pytest unit and integration test suite
├── reports/                   <- Historical phase reports, manifests, and CSVs
├── outputs/                   <- Cached trade logs and temporary run files
├── configs/                   <- Hardcoded configurations/parameter settings
└── scratch/                   <- Temporary files and development experiments
```

---

## 2. Analysis of the Current State

### What Works Well
1. **Core Backtest Engine (`src/backtest/engine.py`)**: Genuinely robust, handles transaction costs (maker/taker fees), slippage, contract/price rounding rules, margin parameters, and position limits.
2. **Pytest Integration**: Extremely detailed tests (400+ passed) that verify engine execution steps, no-lookahead features, and strategy logic.
3. **Data Processors**: Processed data is gap-free and covers high-fidelity data periods from 2020-01 to 2026-06.

### What is Slow or Inefficient
1. **Runner Duplication**: Each phase has had its own dedicated runner script (e.g. `phase25_runner.py`, `phase26_runner.py`, `phase27_runner.py`). These scripts copy-paste 90% of their logic for loading data, setting up the backtest engine, iterating candidates, running stress tests, and formatting markdown outputs.
2. **Large-scale Parameter Search**: Grid search loop inside the runners is single-threaded, and there is no unified checkpointing queue. Running a new parameter sweep requires writing a custom loop.
3. **Verification is Manual**: Validating that reports contain correct tables, verdicts, or that code contains no lookahead bugs has been done manually or with ad-hoc scripts.

### Bottlenecks and Duplications
- **Logic Duplication**: The boilerplate for running `MultiPositionBacktestEngine` exists in at least 15 separate runner scripts.
- **Reporting Inconsistencies**: Some phases produce manifests, while others do not. Some outputs are written to `reports/`, some to `outputs/`, and some are hardcoded in the script printouts.
- **Vulnerability to Forced Metrics**: Because runners printed reports and developers copy-pasted results, it was easy to force PnL metrics by patching code downstream of actual backtests.

---

## 3. Vulnerability to Lookahead/Hardcoding
Without a static analysis engine (Audit Engine) running in the E2E verification loop, future work is susceptible to:
- Using outcomes (`is_winner`) from completed trades to size future positions.
- Direct override of computed trade lists or PnL summaries in runners.
- Future leakage across candle timeframes in multi-timeframe strategies.

---

## 4. Recommended Architecture
To solve these issues, Phase 30.1 implements:
1. **Unified Research CLI (`scripts/research_lab.py`)**: A single control panel to run, test, and audit.
2. **Automated Audit Engine (`scripts/audit_engine.py`)**: Scans repository code to catch forbidden lookahead or forced metric patterns.
3. **Candidate Compiler (`src/research/candidate_template_compiler.py`)**: Standardizes how strategy parameters are registered.
4. **Execution Queue (`scripts/candidate_execution_queue.py`)**: Introduces checkpointing, batch execution, and hash-locking.
5. **Report Validator (`scripts/report_validator.py`)**: Automatically scans phase reports to ensure compliance before commits.
