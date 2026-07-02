# Phase 30.1 — Candidate Template Schema & Onboarding

This document defines the schema, lifecycle stages, and metadata requirements for compiling strategy candidates from raw hypotheses.

## 1. Lifecycle Status Mapping
Every candidate must transition through the following strict pipeline:

```
  [ REGISTERED ] ──( Static Scan )──> [ STATIC_AUDITED ] ──( Backtest )──> [ ENGINE_EXECUTED ]
                                                                                   │
     ┌───────────────────────┬─────────────────────────┬───────────────────────────┴────────────────────────────┐
     ▼                       ▼                         ▼                                                        ▼
[ REJECTED ]    [ PROMOTED_RESEARCH_ONLY ]    [ PROMOTED_BENCHMARK_CANDIDATE ]                      [ INVALID_FORCED_METRIC ]
```

*   **REGISTERED**: Candidate template created and parameters defined, but not yet verified or run.
*   **STATIC_AUDITED**: Passed the no-lookahead static checker (`audit_engine.py`).
*   **ENGINE_EXECUTED**: Run through `MultiPositionBacktestEngine` with authentic metrics computed from trade logs.
*   **REJECTED**: Failed to pass basic performance, stress testing, or lookahead checks.
*   **PROMOTED_RESEARCH_ONLY**: Authentic metrics confirmed; exhibits alpha but does not surpass target benchmarks.
*   **PROMOTED_BENCHMARK_CANDIDATE**: Passes all strict acceptance criteria and stress matrix tests, replacing/upgrading previous benchmarks.
*   **INVALID_FORCED_METRIC**: Classified if forced overrides, hardcoding, or duplicate sampling are detected in any associated runner.

---

## 2. Schema Specification
| Field | Data Type | Description |
|---|---|---|
| `candidate_id` | String (unique) | Structured hash-based ID (e.g. `CAND_001_a9b8c7d6`). |
| `idea_id` | String | Reference ID from the Idea Engine. |
| `family` | String | Strategy research family classification. |
| `parameters` | JSON-string | Strategy configuration dictionary passed to strategy class. |
| `live_known_feature_list` | CSV-string | Set of indicators/features used at signal time (fully audited). |
| `required_data` | CSV-string | Timeframe files required for backtesting. |
| `no_lookahead_audit_status` | String | `PENDING`, `PASSED`, or `FAILED`. |
| `implementation_file` | String | Source file where strategy class resides. |
| `execution_status` | String | Core lifecycle status (REGISTERED, STATIC_AUDITED, etc.). |
| `metric_status` | String | `BLANK` for unexecuted, or `COMPUTED_FROM_LOG` for executed. |

---

## 3. Mandatory Verification
Before any candidate is compiled or execution runs:
1. `no_lookahead_audit_status` must show `PASSED` using `python scripts/audit_engine.py`.
2. All parameters must be statically typed and present in the strategy definition.
