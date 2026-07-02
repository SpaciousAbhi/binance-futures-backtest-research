# NEXT PHASE PLAN
## Phase 29.7 — Teacher Trade Replay and Execution Feasibility Audit
## Last Updated: 2026-07-02 (Phase 30)

---

## Phase Identity

| Item | Value |
|---|---|
| Phase number | 29.7 (or 31 if renumbered) |
| Phase name | Teacher Trade Replay and Execution Feasibility Audit |
| Phase type | Diagnostic / Engine Research |
| Estimated complexity | Medium-High |
| Depends on | Phase 29.6 outputs (5m engine trace log) |
| Must NOT do | Blind candidate search, new benchmark claims, hardcoded metrics |

---

## Goal

Determine whether the 325 PF1.2 teacher trades are physically executable under real 5m SL/TP paths.

The current gap: Phase 29.6 5m engine produces 3,111 trades with PF 0.64 when trying to replicate
the PF1.2 setup conditions. Only 1/325 teacher entries match in time/side.

The hypothesis is that the 1h backtest engine makes price-path assumptions (e.g., "if candle low
touches SL, trade is stopped; if candle high touches TP, trade wins") that are NOT valid at 5m
resolution where the actual path may trigger SL before TP.

---

## Specific Objectives

### Objective 1 — Teacher Trade Replay
For each of the 325 teacher trades (from `reports/phase29_4_teacher_distilled_rules.csv`):
1. Find the exact 5m candles covering `entry_time` to `exit_time`.
2. Simulate the SL/TP path at 5m resolution using the teacher's entry price, SL level, TP level.
3. Record: does the teacher trade survive at 5m resolution? Or is it stopped out?
4. Output: `reports/phase29_7_teacher_trade_5m_replay.csv` — one row per teacher trade.

### Objective 2 — Gap Analysis
Compute:
- How many of the 325 teacher trades survive 5m resolution as-is?
- What is the PnL of trades that survive?
- What ATR multipliers would be needed to recover the full teacher result?
- Which teacher trades are structurally impossible (e.g., SL is hit in same 5m candle as entry)?

### Objective 3 — Parameter Optimization (Narrow)
For the surviving subset of teacher trades:
- Test ATR_SL_mult values from 1.0 to 3.0 in 0.25 steps.
- Test ATR_TP_mult values from 1.5 to 5.0 in 0.25 steps.
- No blind grid search — only parameters that affect teacher survival rate.
- Output: best parameter set that maximizes teacher match rate.

### Objective 4 — Feasibility Verdict
Produce a binary verdict:
- `TEACHER_EXECUTABLE_WITH_ORIGINAL_PARAMS` — teacher trades survive 5m resolution unchanged.
- `TEACHER_EXECUTABLE_WITH_ADJUSTED_PARAMS` — teacher trades survive with modified SL/TP.
- `TEACHER_NOT_EXECUTABLE` — fundamental path mismatch; a new strategy design is needed.

---

## Input Files Required

| File | Purpose |
|---|---|
| `data/processed/BTCUSDT_5m_processed.csv` | 5m OHLCV + funding (682,561 rows) |
| `data/processed/BTCUSDT_1h_processed.csv` | 1h OHLCV (for setup confirmation) |
| `reports/phase29_4_teacher_distilled_rules.csv` | 325 teacher trades with entry/exit rules |
| `reports/phase29_4_teacher_canonical_sets.csv` | Teacher canonical trade sets |
| `reports/phase29_6_pf12_mtf_trade_log.csv` | 5m engine trace (for comparison) |
| `reports/phase29_6_execution_rule_recovery_audit.csv` | 31 recovered execution rules |
| `reports/phase29_5_teacher_mtf_trigger_match.csv` | Previous trigger match attempt |

---

## Output Files Required

| File | Content |
|---|---|
| `reports/phase29_7_teacher_trade_5m_replay.csv` | One row per teacher trade: survives/stopped/impossible |
| `reports/phase29_7_param_optimization_results.csv` | ATR mult grid: match rate, PnL, PF |
| `reports/phase29_7_gap_analysis.csv` | Which trades survive, which fail, why |
| `reports/phase29_7_audit_manifest.json` | File hashes, timestamps |
| `reports/phase29_7_teacher_replay_feasibility_report.md` | Main report with verdict |
| `scripts/phase29_7_teacher_replay.py` | Replay script |
| `tests/test_phase29_7_teacher_replay.py` | Tests for no-lookahead, ordering constraints |

---

## Non-Negotiable Rules for Phase 29.7

1. Every teacher trade replay must use only data available at `entry_time` (no future data).
2. SL takes priority if hit in the same 5m candle as TP.
3. Fees and slippage must be applied to all replayed trades.
4. The final verdict must be computed from the actual replay results — not asserted.
5. Do NOT start a new candidate search during this phase.
6. Do NOT claim a new benchmark unless the replay produces a trade log with no forced metrics.
7. Update `project_memory/CURRENT_HANDOFF.md` after completion.
8. Push to GitHub after completion.

---

## Success Criteria

Phase 29.7 is considered PASS if:
- All 325 teacher trades are replayed at 5m resolution and logged.
- Gap analysis is complete with root cause for non-surviving trades.
- A binary feasibility verdict is produced.
- Main report, manifest, and at least 1 test file are committed.
- `project_memory/CURRENT_HANDOFF.md` is updated with exact results.
