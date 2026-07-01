# Binance USD-M Futures Strategy Research and Backtester

A professional, research-focused Python framework for BTCUSDT perpetual futures (`BTCUSDT.P`). This is NOT a live trading bot, but a real-money research environment designed to build, test, and audit strategy candidates from 2020-01-01 to present.

---

## 1. Project Scope & Seriousness
* **Real-Money Seriousness**: No fake metrics, no repainting, no lookahead bias, and no outcome-based filtering.
* **Exchange Scope**: Designed specifically for Binance USD-M Perpetual Futures (using real fees, slippage, and cumulative funding rate costs).
* **Exchange Limits**: Incorporates minimum notional filters ($100 USDT) and contract size/price precision rounding rules to ensure live-automation compatibility.

---

## 2. Strict Acceptance Criteria
A strategy passes only if it achieves:
1. **0 negative months** and **0 zero months** (100% positive months from 2020-01 to present).
2. **780+ total trades minimum** (preferably 1,000+).
3. **Meaningfully positive Net PnL** after fees, slippage, and funding rate deductions.
4. **Controlled drawdown** and positive expectancy.
5. **Robustness** under Walk-Forward Validation and Stress Testing.

---

## 3. Command Usage Guide

### 3.1. Installation
Install project dependencies in editable mode:
```bash
pip install -e .
```

### 3.2. Run Unit Tests
```bash
pytest tests/
```

### 3.3. Run Strategy Research & Audits
Run the complete staged candidate search, walk-forward validation, stress testing, and auditing pipeline:
```bash
python -m src.research.runner
```

### 3.4. Read Final Reports
The pipeline generates:
* **Checkpoints**: `reports/search_checkpoint.json` containing leaderboards and tested hashes.
* **Phase 2 Report**: `reports/phase2_strategy_research_report.md` detailing the verdict, bug fixes, leaderboard, stress test matrix, and compliance status.
