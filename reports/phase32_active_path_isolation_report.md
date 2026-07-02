# Phase 32 — Active Path Isolation Report

## Summary

| Category | Count |
|---|---|
| ACTIVE files | 7 |
| ACTIVE_AUDIT files | 3 |
| ACTIVE_DEPENDENCY files | 1 |
| ACTIVE_TEST files | 2 |
| HISTORICAL_EVIDENCE files | 9 |

## Guardrails

1. Active runners (`phase32_runner.py`, `phase31_1_runner.py`) do NOT import any historical runner
   that contains forced metrics or lookahead (phase17–phase28 runners).
2. Benchmark builders must not read report-only metrics as source of truth.
3. Every candidate must produce a trade log before metrics are assigned.
4. Source Classification Registry: `project_memory/SOURCE_CLASSIFICATION_REGISTRY.csv`

## Live Status

NOT_REAL_CAPITAL_READY
