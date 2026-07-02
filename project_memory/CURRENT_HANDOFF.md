# CURRENT HANDOFF
## Last Updated: 2026-07-02 (after Phase 29.6 sync from Codex)

---

## Latest Completed Phase: Phase 29.6

**Phase name:** True 5m Event-Driven MTF Engine
**Verdict:** `PF12_MTF_ENGINE_MAJOR_PROGRESS_BUT_NOT_RECOVERED`
**Source:** Codex workspace — synced to Antigravity on 2026-07-02

---

## Exact Latest Result (Phase 29.6)

### PF1.2 Event-Driven MTF Engine (Best Row)

| Metric | Value |
|---|---|
| Net PnL | **-$9,940.72** |
| Trades | 3,111 |
| Profit Factor | 0.64 |
| Max Drawdown | 99.41% |
| Combined Adverse Stress | -$24,422.06 |
| Teacher time/side matches | **1 / 325** |

### PF8-Family MTF Sleeve (Best Row)

| Metric | Value |
|---|---|
| Net PnL | -$9,945.87 |
| Trades | 2,468 |
| Profit Factor | 0.45 |
| Max Drawdown | 99.46% |
| Combined Adverse Stress | -$19,849.76 |

---

## What Was Proven in Phase 29.6

- A true 5m event-driven MTF engine was built and runs cleanly.
- It operates: `1h setup close -> 5m trigger window -> 5m entry/fill -> 5m SL/TP simulation`.
- No-lookahead and order timing tests pass.
- Every emitted trade records setup close, trigger, entry, and exit timestamps.
- Setup-before-trigger and trigger-before-entry ordering is verified.
- Execution rules recovered: closed-candle entries, ATR SL/TP, SL-first same-candle priority,
  breakeven, trailing/time-stop, funding filters, fee/slippage, rounding, reduce-only concept.
- Conflict recovery tested: missed fill stress, stale cancel stress, partial-fill stress.

## What Was NOT Proven

- PF 1.2 executable exact recovery (teacher matches: 1/325).
- Any new locked benchmark.
- PF 7.0 / PF 8.0 / PF 8.1 validity — these remain INVALID (forced metrics).

## What Was Proven in Earlier Phases (29 - 29.5)

- Phase 29: AUDIT_FAIL_LOOKAHEAD_OR_HARDCODING_FOUND — PF8.1 rejected as verified benchmark.
- Phase 29.1: PF1.2 truth lock re-established. Genuine candidate search (no forced metrics).
- Phase 29.2: Truth reconstruction with genuine candidates; Dirty PF8 cluster diagnostic.
- Phase 29.3: Variant B and Variant C teacher lineage recovery and rebuild attempt.
- Phase 29.4: Teacher distillation — 325 teacher trades analyzed for entry/exit feature extraction.
- Phase 29.5: Major MTF router recovery attempt — teacher_mtf_trigger_match results generated.

---

## Current Best Real Engine Result

| Benchmark | Source | PnL | Trades | PF | Max DD | Status |
|---|---|---|---|---|---|---|
| PF 1.2 (teacher reference) | Phase 12 runner | $21,684.99 | 325 | 2.42 | 10.87% | VALID_TEACHER_REFERENCE |
| Phase 29.5 MTF Router | Phase 29.5 | See reports | — | — | — | RESEARCH_ONLY |
| Phase 29.6 5m Engine | Phase 29.6 | -$9,940.72 | 3,111 | 0.64 | 99.41% | ENGINE_PROGRESS |

---

## Next Recommended Phase: Phase 29.7

**Phase name:** Teacher Trade Replay and Execution Feasibility Audit
**Goal:** Use the Phase 29.6 trace log (`phase29_6_pf12_mtf_trade_log.csv`) to compare teacher entries
against exact 5m trigger and exit paths. Optimize only live-known trigger timing and exit parameters
to minimize the teacher gap (currently 1/325 match). No blind candidate searches.

### Key files to load at start of Phase 29.7:
```
reports/phase29_6_pf12_mtf_trade_log.csv        <- 5m trace log (1.7 MB)
reports/phase29_4_teacher_distilled_rules.csv    <- teacher entry rules
reports/phase29_4_teacher_canonical_sets.csv     <- teacher canonical trade sets
reports/phase29_5_teacher_mtf_trigger_match.csv  <- teacher trigger match audit
reports/phase29_6_execution_rule_recovery_audit.csv <- recovered rules (31 rows)
```

---

## Critical Rules (Never Break)

1. **Do not run a new blind large candidate search** before teacher-entry replay is solved.
2. **Do not chase PF 8.1 forced targets** — they are invalid.
3. **Do not trust report-only metrics** — compute from trade logs.
4. **Do not hardcode benchmark values** — all metrics must be computed from engine output.
5. **Do not use `is_winner`, `future_pnl`, `future_mfe`, `future_mae`, or future dates** in any live routing feature.
6. **Always update this CURRENT_HANDOFF.md** at the end of every phase.

---

## Session Start Checklist (Every AI Must Do This)

- [ ] Read `project_memory/CURRENT_HANDOFF.md` (this file)
- [ ] Read `project_memory/MASTER_PROJECT_STATE.md`
- [ ] Check `reports/phase29_6_audit_manifest.json` for latest proof hashes
- [ ] Run `pytest -q` to confirm tests pass before doing anything
- [ ] Confirm git status is clean before any new work
- [ ] Do NOT start Phase 29.7 unless the above checklist is complete

---

## Git State (as of last sync)

- **Branch:** master
- **Pre-sync commit:** `9e35f5fcf8b7e24482822553ee44c5a373866958`
- **Sync date:** 2026-07-02
- **Remote:** https://github.com/SpaciousAbhi/binance-futures-backtest-research
