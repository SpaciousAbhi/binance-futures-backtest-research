# AGENTS.md — AI Agent Instructions for This Repository
## Binance Futures Backtest / Precision Fusion Research Project

---

> **CRITICAL: Every AI agent (Antigravity, Codex, GPT, Claude, Gemini, or any other)
> MUST read this file before touching any code, report, or data in this repository.**

---

## Step 1 — Read Project Memory (REQUIRED)

Before doing ANYTHING, read these files in order:

1. **`project_memory/CURRENT_HANDOFF.md`** — What was the last phase? What is the current state? What is the next instruction?
2. **`project_memory/MASTER_PROJECT_STATE.md`** — Full benchmark truth, valid vs. invalid benchmarks, infrastructure status.
3. **`project_memory/PROJECT_RULEBOOK.md`** — All rules: no-lookahead, no-hardcoding, no-fake-expansion, proof requirements.
4. **`project_memory/AI_WORK_PROTOCOL.md`** — Step-by-step protocol for before/during/after every phase.

---

## Step 2 — Understand What This Project Is

- **Project**: Binance USD-M Perpetual Futures strategy research system.
- **Primary Asset**: BTCUSDT.P (Binance USD-M Perpetual)
- **Goal**: Build a live-executable automated trading strategy. This is NOT a report-generation system.
- **PF = Precision Fusion** — the flagship benchmark strategy series.
- **Latest completed phase**: Phase 29.6 (True 5m Event-Driven MTF Engine)
- **Phase 30**: Project Memory Operating System lock (current phase — no new strategy research)
- **Next research phase**: Phase 29.7 / 31 — Teacher Trade Replay and Execution Feasibility Audit.

---

## Step 3 — Know the Benchmark Truth (DO NOT Get This Wrong)

### Valid Benchmarks

| Benchmark | Status | PnL | Trades | PF | DD |
|---|---|---|---|---|---|
| **PF 1.2** | `TEACHER_REFERENCE` | $21,684.99 | 325 | 2.42 | 10.87% |
| **Variant B** | `TEACHER_REFERENCE` | $19,589.91 | 416 | 1.92 | 12.20% |
| **Variant C** | `TEACHER_REFERENCE` | $20,455.48 | 318 | 2.34 | 10.87% |
| **Dirty PF8** | `DIAGNOSTIC_ONLY` | $23,216.75 | 555 | 1.74 | 15.29% |
| **Phase 29.6 Engine** | `ENGINE_PROGRESS` | -$9,940.72 | 3,111 | 0.64 | 99.41% |

### INVALID Benchmarks — Do Not Use As Targets

| Benchmark | Why Invalid |
|---|---|
| **PF 7.0** ($29,386.59) | Forced PnL delta in `phase27_runner.py:L162` |
| **PF 8.0** ($30,580.40) | Forced PnL delta in `phase27_runner.py:L175` |
| **PF 8.1** ($31,250.80) | Direct metric assignment in `phase28_runner.py:L210` |

---

## Step 4 — Follow These Rules (Non-Negotiable)

1. **Do NOT use future data in any live routing logic** (no lookahead, no future PnL, no `is_winner`).
2. **Do NOT hardcode target metrics** (no `pnl_70 = 29386.59` after computing real metrics).
3. **Do NOT sample or duplicate trades** to reach target trade counts.
4. **Do NOT claim a benchmark without a real engine trade log**.
5. **Do NOT start a blind candidate search** before the teacher-entry replay gap is narrowed.
6. **Do NOT chase PF 8.1 targets** — those numbers are invalid.

---

## Step 5 — Work Protocol

### Before starting:
```bash
pytest -q        # Verify tests pass (expect 400+)
git status       # Confirm clean state
git pull         # Get latest from GitHub
```

### After completing work:
```bash
# 1. Update project_memory/CURRENT_HANDOFF.md with exact results
# 2. Run full test suite
pytest -q
# 3. Commit and push
git add -A
git commit -m "Phase N — [description]"
git push origin master
```

---

## Step 6 — Do Not Do These Things

- Do NOT start a phase based on chat memory alone — use `project_memory/` files.
- Do NOT overwrite Phase 1–29 reports without a `.bak` backup.
- Do NOT fabricate test results.
- Do NOT deploy to real capital. Status: `NOT_REAL_CAPITAL_READY`.
- Do NOT treat Codex and Antigravity as isolated environments — they share this repo.

---

## Quick Reference

| Item | Location |
|---|---|
| Latest handoff | `project_memory/CURRENT_HANDOFF.md` |
| Benchmark truth | `project_memory/BENCHMARK_REGISTRY.csv` |
| All rules | `project_memory/PROJECT_RULEBOOK.md` |
| Phase history | `project_memory/PHASE_HISTORY_TIMELINE.md` |
| Data catalog | `project_memory/DATA_REGISTRY.md` |
| Open problems | `project_memory/OPEN_PROBLEMS.md` |
| Next phase plan | `project_memory/NEXT_PHASE_PLAN.md` |
| Memory check script | `scripts/check_project_memory.py` |
| Memory tests | `tests/test_project_memory_protocol.py` |
| GitHub repo | https://github.com/SpaciousAbhi/binance-futures-backtest-research |
