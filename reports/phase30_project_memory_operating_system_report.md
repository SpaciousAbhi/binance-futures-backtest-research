# Phase 30 — Project Memory Operating System Report
## Binance Futures Backtest / Precision Fusion Research Project
## Date: 2026-07-02

---

## Executive Verdict

**`PHASE30_PASS_PROJECT_MEMORY_OS_LOCKED`**

Phase 30 successfully created a permanent Project Memory Operating System for the Binance Futures
Backtest / Precision Fusion research project. This system ensures that Antigravity, Codex, and
any future AI working from this GitHub repository will:

1. Always start from a correct, up-to-date understanding of project state.
2. Never confuse teacher benchmarks with executable benchmarks.
3. Never confuse invalid/forced benchmarks with real engine results.
4. Always follow strict no-lookahead, no-hardcoding, and no-fake-expansion rules.
5. Always update shared memory after every phase and push to GitHub.

---

## What Was Created / Updated

### New Files Created (11 files)

| File | Purpose |
|---|---|
| `AGENTS.md` | Root-level AI entry point — benchmarks, rules summary, workflow |
| `project_memory/PROJECT_RULEBOOK.md` | Permanent 16-section AI rulebook (largest new file) |
| `project_memory/MEMORY_INDEX.md` | Guide to all memory files and how to use them |
| `project_memory/DATA_REGISTRY.md` | Data assets catalog with integrity requirements |
| `project_memory/ARTIFACT_REGISTRY.csv` | Key proof files catalog with validation status |
| `project_memory/OPEN_PROBLEMS.md` | 5 open research problems with root causes |
| `project_memory/NEXT_PHASE_PLAN.md` | Phase 29.7 detailed specification |
| `scripts/check_project_memory.py` | Validation script — 49 checks, 0 failures |
| `tests/test_project_memory_protocol.py` | 55 protocol tests — 55 passing |
| `reports/phase30_project_memory_operating_system_report.md` | This report |
| `reports/phase30_audit_manifest.json` | Phase 30 audit manifest |

### Upgraded Files (6 files)

| File | What Changed |
|---|---|
| `README.md` | Full rewrite — 5-minute project overview for any AI/developer |
| `project_memory/CURRENT_HANDOFF.md` | Phase 30 complete; Phase 29.6 exact PnL; session checklist; NOT_REAL_CAPITAL_READY |
| `project_memory/MASTER_PROJECT_STATE.md` | Full current state, engine status, open problem reference |
| `project_memory/BENCHMARK_REGISTRY.csv` | Added Variant B/C metrics; Dirty PF8 real metrics; Phase 29.6 engine result |
| `project_memory/AI_WORK_PROTOCOL.md` | Pre-existing; confirmed current content passes all checks |
| `project_memory/PHASE_HISTORY_TIMELINE.md` | Pre-existing; covers Phase 1 to Phase 29.6 |

---

## PROJECT_RULEBOOK.md Summary

The rulebook contains 16 sections covering:

| Section | Topic | Key Prohibition |
|---|---|---|
| 1 | Project Identity | Not a report-generation system |
| 2 | Core Strategy Goals | Trade count only if quality survives |
| 3 | Benchmark Classification | 8 valid labels, every system must use one |
| 4 | No-Lookahead Rules | Future MFE/MAE/PnL/is_winner forbidden |
| 5 | No-Hardcoding Rules | Forced PnL deltas forbidden |
| 6 | No-Fake-Expansion Rules | `.sample(replace=True)` forbidden |
| 7 | Metric Calculation | All metrics must compute from trade logs |
| 8 | Teacher Set Rules | Teacher labels cannot be routing inputs |
| 9 | MTF Rules | 1h setup must close before 5m trigger |
| 10 | Execution Model Rules | SL/TP/fees/slippage all required |
| 11 | Stress Testing Rules | 12-scenario stress matrix required |
| 12 | Candidate Search Rules | Unique hashes; no fake completion |
| 13 | Report Rules | One main report + manifest per phase |
| 14 | Git / Sync Rules | Push after every phase; read memory before starting |
| 15 | Live Trading Safety | NOT_REAL_CAPITAL_READY until all 8 requirements met |
| 16 | Conflict Resolution | Trade log > memory file > prose |

Two historical violation appendices document exactly how PF7/8/8.1 were corrupted.

---

## Antigravity / Codex / GitHub Continuity Architecture

```
GitHub Repository (Source of Truth)
    |
    |── AGENTS.md                  <- Every AI reads this first
    |── project_memory/
    |   |── CURRENT_HANDOFF.md     <- Mandatory update after every phase
    |   |── MASTER_PROJECT_STATE.md <- Full benchmark truth
    |   |── PROJECT_RULEBOOK.md    <- 16-section rules
    |   |── AI_WORK_PROTOCOL.md    <- Step-by-step protocol
    |   |── PHASE_HISTORY_TIMELINE.md
    |   |── BENCHMARK_REGISTRY.csv
    |   |── DATA_REGISTRY.md
    |   |── ARTIFACT_REGISTRY.csv
    |   |── OPEN_PROBLEMS.md
    |   |── NEXT_PHASE_PLAN.md
    |   |── MEMORY_INDEX.md
    |   `── README_FOR_NEXT_AI.md
    |
    |── scripts/check_project_memory.py  <- Run before starting any phase
    `── tests/test_project_memory_protocol.py <- 55 protocol tests
```

**Switching between AI environments:**
1. Finishing AI: update `CURRENT_HANDOFF.md` → `git commit -am "Phase N"` → `git push`
2. Starting AI: `git pull` → read `AGENTS.md` → read `CURRENT_HANDOFF.md` → `pytest -q` → `python scripts/check_project_memory.py`

---

## Benchmark Truth Preserved

All benchmark truth from Phase 29 audit is preserved and locked:

| Benchmark | PnL | Trades | PF | DD | Status |
|---|---|---|---|---|---|
| PF 1.2 (Teacher) | $21,684.99 | 325 | 2.42 | 10.87% | `TEACHER_REFERENCE` |
| Variant B | $19,589.91 | 416 | 1.92 | 12.20% | `TEACHER_REFERENCE` |
| Variant C | $20,455.48 | 318 | 2.34 | 10.87% | `TEACHER_REFERENCE` |
| Dirty PF8 | $23,216.75 | 555 | 1.74 | 15.29% | `DIAGNOSTIC_ONLY` |
| Phase 29.6 Engine | -$9,940.72 | 3,111 | 0.64 | 99.41% | `ENGINE_PROGRESS` |
| PF 7.0 | ~~$29,386.59~~ | — | — | — | **`INVALID_FORCED_METRIC`** |
| PF 8.0 | ~~$30,580.40~~ | — | — | — | **`INVALID_FORCED_METRIC`** |
| PF 8.1 | ~~$31,250.80~~ | — | — | — | **`INVALID_FORCED_METRIC`** |

---

## Validation Results

### check_project_memory.py
```
PASS : 49
WARN : 1  (report not yet written at check time — resolved)
FAIL : 0
Result: MEMORY_INTEGRITY_PASS
```

### pytest tests/test_project_memory_protocol.py
```
55 passed in 0.48s
(After Phase 30 report creation)
```

### Full Test Suite
```
400+ passed
```

---

## What Every Future AI Must Read First

```
1. AGENTS.md                           (root — FIRST FILE)
2. project_memory/CURRENT_HANDOFF.md   (current state)
3. project_memory/MASTER_PROJECT_STATE.md (full context)
4. project_memory/PROJECT_RULEBOOK.md  (all rules)
```

Do NOT start work from chat memory alone.
Do NOT assume continuity from chat history.
Use `project_memory/` as the source of truth.

---

## Next Phase

**Phase 29.7 — Teacher Trade Replay and Execution Feasibility Audit**

Full specification: `project_memory/NEXT_PHASE_PLAN.md`

Key objectives:
1. Replay all 325 PF1.2 teacher trades through the 5m engine at their exact timestamps.
2. Determine which survive at 5m SL/TP resolution.
3. Identify root cause of the teacher-to-engine gap.
4. Produce binary feasibility verdict.

Key input files:
- `reports/phase29_6_pf12_mtf_trade_log.csv` (5m engine trace)
- `reports/phase29_4_teacher_distilled_rules.csv` (325 teacher rules)

**Rules:** No new candidate searches. No new benchmark claims. No hardcoded metrics.

---

## Files NOT Changed in Phase 30

- `src/backtest/engine.py` — Not modified (no strategy logic changes)
- `src/strategies/candidates.py` — Not modified
- `src/features/indicators.py` — Not modified
- All Phase 1–29.6 report files — Not modified (only new files added)
- All Phase 29 trade logs — Not modified

---

## Live Trading Status

> **NOT_REAL_CAPITAL_READY**
>
> No strategy has passed all 8 safety requirements listed in PROJECT_RULEBOOK.md Section 15.
> Do not deploy real capital under any circumstances.

---

*Phase 30 executed by Antigravity on 2026-07-02.*
