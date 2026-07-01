# Project: binance_futures_backtest

## Architecture
- Module/package boundaries, data flow, shared interfaces:
  - `src/data/`: handles downloading (`downloader.py`), processing and merging (`processor.py`), and auditing (`auditor.py`).
  - `src/features/`: calculates technical indicators (`indicators.py`).
  - `src/strategies/`: base classes (`base.py`), strategies templates (`candidates.py`), and portfolio strategy (`portfolio.py`).
  - `src/backtest/`: core backtesting logic (`engine.py`).
  - `src/research/`: sweeps parameters, splits walk-forward, runs stress tests and audits (`runner.py`).
  - `src/audit/`: runs verification check for lookahead/leakage (`system_auditor.py`).
  - `src/reporting/`: formats/exports monthly reports (`reporter.py`).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Audit | Verify baseline code and tests. | None | DONE |
| 2 | E2E Test Suite | Build comprehensive E2E tests and publish TEST_READY.md. | M1 | IN_PROGRESS |
| 3 | Engine & Reporting | Deduplicate leaderboard, enhance monthly reports, and strengthen consistency filter. | M2 | PLANNED |
| 4 | Regime Engine & Strategy Expansion | Implement regime engine and expand strategy candidates. | M3 | PLANNED |
| 5 | Walk-Forward & Portfolio | Implement 4-split walk-forward and portfolio optimizer. | M4 | PLANNED |
| 6 | Verification, Stress & Audit | Run stress tests and compliance audits. | M5 | PLANNED |
| 7 | Synthesis & Final Report | Compile report and check PASS criteria. | M6 | PLANNED |

## Interface Contracts
- `RegimeEngine`: Class or function returning regime label for bar `i` using only past data.
- `UniversalStrategyTemplate`: Receives config, produces signals.
- `PortfolioStrategy`: Combines strategies, resolves conflicts, and applies cooldowns.

## Code Layout
- Root directory: `C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest`
