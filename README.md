# Binance USD-M Futures Strategy Research — Precision Fusion Project

> **For new AI agents and developers: Read `AGENTS.md` and `project_memory/CURRENT_HANDOFF.md` first.**

A professional, research-focused Python framework for BTCUSDT USD-M Perpetual Futures strategy
research. This is a **real-money research system** — not a live bot, not a demo, not a paper
backtest dashboard. Every rule, every metric, and every result is held to live-execution standards.

---

## Project Status (as of 2026-07-02)

| Item | Status |
|---|---|
| Latest completed phase | **Phase 39** — Strategy #1.2 Candidate Discovery & Promotion |
| Next research phase | **Phase 40** — Cross-Asset Validation & Shadow Trading Design |
| Live capital status | **NOT_REAL_CAPITAL_READY** |
| Primary benchmark | **PF 1.2 (Teacher Reference)** — $21,684.99 / 325 trades / PF 2.42 |
| Invalid benchmarks | PF 7.0, PF 8.0, PF 8.1 (forced metrics — see AGENTS.md) |
| Test suite | 400+ tests passing |


---

## Critical Warning

> **PF 7.0 ($29,386.59), PF 8.0 ($30,580.40), and PF 8.1 ($31,250.80) are INVALID.**
> They were constructed using hardcoded PnL deltas and direct metric assignment.
> They cannot be reproduced by running the strategy through the backtest engine.
> Do NOT use them as targets. See `project_memory/MASTER_PROJECT_STATE.md`.

---

## Quick Start for AI Agents

```bash
# 1. Read project context first
cat AGENTS.md
cat project_memory/CURRENT_HANDOFF.md

# 2. Install and verify
pip install -e .
pytest -q                   # Expect 400+ passing

# 3. Use the Research Lab CLI Control Panel
python scripts/research_lab.py status          # Check latest handoff and phase status
python scripts/research_lab.py memory-check    # Run full project memory audit
python scripts/research_lab.py audit           # Run code audit for lookahead/hardcoding
python scripts/research_lab.py next-phase      # Get next research objectives spec

# 4. Reproduce PF 1.2 teacher benchmark (only valid executable benchmark)
python src/research/phase12_runner.py
# Expected: Net PnL=$21,684.99, Trades=325, PF=2.42, DD=10.87%
```

---

## Benchmark Registry Summary

| Benchmark | Status | PnL | Trades | PF | Max DD |
|---|---|---|---|---|---|
| PF 1.2 | `TEACHER_REFERENCE` | $21,684.99 | 325 | 2.42 | 10.87% |
| Variant B | `TEACHER_REFERENCE` | $19,589.91 | 416 | 1.92 | 12.20% |
| Variant C | `TEACHER_REFERENCE` | $20,455.48 | 318 | 2.34 | 10.87% |
| Dirty PF8 | `DIAGNOSTIC_ONLY` | $23,216.75 | 555 | 1.74 | 15.29% |
| Phase 29.6 Engine | `ENGINE_PROGRESS` | -$9,940.72 | 3,111 | 0.64 | 99.41% |
| PF 7.0 | **`INVALID_FORCED_METRIC`** | — | — | — | — |
| PF 8.0 | **`INVALID_FORCED_METRIC`** | — | — | — | — |
| PF 8.1 | **`INVALID_FORCED_METRIC`** | — | — | — | — |

Full registry: `project_memory/BENCHMARK_REGISTRY.csv`

---

## Repository Structure

```
binance_futures_backtest/
├── AGENTS.md                    <- READ FIRST (AI entry point)
├── project_memory/              <- Shared AI continuity layer
│   ├── CURRENT_HANDOFF.md       <- Latest phase result + next instruction
│   ├── MASTER_PROJECT_STATE.md  <- Full benchmark truth
│   ├── PROJECT_RULEBOOK.md      <- All rules (lookahead, hardcoding, etc.)
│   ├── AI_WORK_PROTOCOL.md      <- Step-by-step work protocol
│   ├── PHASE_HISTORY_TIMELINE.md <- Phase 1 to present
│   ├── BENCHMARK_REGISTRY.csv   <- Machine-readable benchmark table
│   ├── DATA_REGISTRY.md         <- Data assets catalog
│   ├── OPEN_PROBLEMS.md         <- Current open research problems
│   ├── NEXT_PHASE_PLAN.md       <- Next phase specification
│   └── MEMORY_INDEX.md          <- Guide to all memory files
├── src/
│   ├── backtest/engine.py       <- Core backtest engine
│   ├── strategies/candidates.py <- Strategy templates
│   ├── features/indicators.py   <- ATR, VWAP, BB, RSI indicators
│   ├── data/downloader.py       <- Binance API data downloader
│   └── research/                <- Phase runner scripts (phase12_runner.py etc.)
├── scripts/                     <- Phase execution scripts (phase29_X etc.)
├── tests/                       <- Test suite (400+ tests)
├── reports/                     <- All phase proof files and manifests
├── data/
│   ├── processed/               <- Processed 1h + 15m OHLCV + funding (in git)
│   └── raw/                     <- Raw Binance downloads (gitignored)
└── configs/                     <- Strategy parameter configs
```

---

## How to Read Project Memory

Read files in this order:

1. `project_memory/CURRENT_HANDOFF.md` — Current state + next action
2. `project_memory/MASTER_PROJECT_STATE.md` — Full context
3. `project_memory/PROJECT_RULEBOOK.md` — All rules
4. `project_memory/PHASE_HISTORY_TIMELINE.md` — History (if needed)

After completing any phase, update `CURRENT_HANDOFF.md` and push to GitHub.

---

## Running Tests

```bash
# Full test suite
pytest -q

# Phase 30 memory protocol tests only
pytest tests/test_project_memory_protocol.py -v

# Memory check script
python scripts/check_project_memory.py
```

---

## Key Phase Reports

| Phase | Report | Key Result |
|---|---|---|
| Phase 29 | `reports/phase29_absolute_truth_audit_full_project_report.md` | AUDIT_FAIL: PF8.1 rejected |
| Phase 29.1 | `reports/phase29_1_truth_first_pf8_recovery_report.md` | PF1.2 truth re-locked |
| Phase 29.6 | `reports/phase29_6_true_5m_event_driven_mtf_engine_report.md` | 5m engine built, not yet converging |
| Phase 30 | `reports/phase30_project_memory_operating_system_report.md` | Memory OS locked |

---

## Data Coverage

| Asset | Timeframes | Rows | Range |
|---|---|---|---|
| BTCUSDT | 1h, 15m, 5m | 56,929 / 227,521 / 682,561 | 2020-01 — 2026-06 |
| ETHUSDT | 1h | 56,929 | 2020-01 — 2026-06 |
| BNBUSDT | 1h | 55,961 | 2020-02 — 2026-06 |
| SOLUSDT | 1h | 50,754 | 2020-09 — 2026-06 |

Re-download via: `python scripts/phase29_download_binance_data.py`

---

## GitHub Repository

**https://github.com/SpaciousAbhi/binance-futures-backtest-research**

This repo is the shared source of truth between Antigravity and Codex AI environments.
Both AI systems must push their work here and read `project_memory/` before starting.

---

## Installation

```bash
pip install -e .
```

Dependencies: `pandas`, `numpy`, `pytest`, `requests`
Python: 3.13+

---

## Live Trading Status

> **NOT_REAL_CAPITAL_READY**
>
> Shadow mode paper trading has not been completed.
> Exchange API integration has not been tested.
> Do not deploy real capital.
