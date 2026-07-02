# Phase 38 — Research Lab Upgrade Report

This document reports the technical details of the Research Lab CLI control panel upgrades, including command expansion, hardcode auditing, and automation validations.

---

## 1. Upgraded Subcommands

We implemented 14 new subcommands in [scripts/research_lab.py](file:///C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest/scripts/research_lab.py):

- **`preflight`**: Aggregates data, memory, and code scans into one command.
- **`postflight`**: Validates report schemas and lock manifestations.
- **`candidate-dashboard`**: Displays candidate sweep statistics.
- **`validate-candidate-schema`**: Checks candidate registry CSV formats.
- **`validate-trade-schema`**: Audits strategy trade log columns.
- **`validate-reproduction`**: Compares strategy execution against reproduction locks.
- **`run-stress`**: Runs 12 stress scenarios in backtests.
- **`leaderboard`**: Ranks candidates based on PnL, profit factor, and drawdown.
- **`analyze-trades`**: Invokes the trade-by-trade analytics engine.
- **`checkpoint-resume`**: Restores the candidate queue from interruption.
- **`lock-artifacts`**: Generates SHA-256 hash manifest.

---

## 2. Code Audit Upgrades

We improved [scripts/audit_engine.py](file:///C:/Users/HP/.gemini/antigravity/scratch/binance_futures_backtest/scripts/audit_engine.py) to add hard gates. The script now fails with exit code 1 if it discovers:
- Direct PnL or Profit Factor assignment constants.
- Future lookahead variables (`future_pnl`, `is_winner`).
- Duplicated candidate configurations.
