# README FOR NEXT AI — Read This First

**This is the shared continuity layer between Antigravity and Codex.**

Before you do anything else in this project, read these two files:

1. `project_memory/CURRENT_HANDOFF.md` — Exact state of the last completed phase and what to do next.
2. `project_memory/MASTER_PROJECT_STATE.md` — Full project context, benchmark truth, and rules.

---

## Why This Folder Exists

This project has been worked on across multiple AI environments (Antigravity and Codex). Each environment has separate context windows that reset. This folder is the **persistent shared memory** that prevents context loss, benchmark confusion, and repeated mistakes.

## Files in This Folder

| File | Purpose |
|---|---|
| `CURRENT_HANDOFF.md` | **Read first every session.** Latest phase result + next instruction. |
| `MASTER_PROJECT_STATE.md` | Full project goal, benchmark truth, engine status, and rules. |
| `PHASE_HISTORY_TIMELINE.md` | Complete phase-by-phase history from Phase 1 to Phase 29.6. |
| `BENCHMARK_REGISTRY.csv` | Machine-readable table of all benchmarks and their validation status. |
| `AI_WORK_PROTOCOL.md` | Rules every AI must follow before claiming metrics or completing a phase. |

## Quick Project Facts

- **Project**: Binance USD-M Futures automated trading strategy research
- **Asset**: BTCUSDT (primary), with ETH/BNB/SOL validation data available
- **Latest completed phase**: Phase 29.6
- **Only valid benchmark**: PF 1.2 (teacher reference, not live-capital ready)
- **GitHub repo**: https://github.com/SpaciousAbhi/binance-futures-backtest-research
- **Local project root**: `C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest`
- **Live capital status**: NOT_REAL_CAPITAL_READY

## Critical Constraint

> **Do not claim any metric unless you computed it from a real trade log.**
> PF 7.0, PF 8.0, and PF 8.1 are INVALID. They contain hardcoded/forced values.
> See `MASTER_PROJECT_STATE.md` for full details.
