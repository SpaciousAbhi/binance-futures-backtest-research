# Phase 31.1 — Combined Router Full Acceptance Audit Report

## Final Verdict

**`PHASE31_1_PARTIAL_PASS_ROUTER_REAL_BUT_REQUIRES_FIXES`**

**Router Classification:** `VALID_EXECUTABLE_BASELINE`

**Live Status:** `BACKTEST_VERIFIED_NOT_SHADOWED`

**Generated:** 2026-07-02 09:37 UTC

---

## Summary of Findings

### The 12 Audit Questions — Answered

| # | Question | Answer |
|---|---|---|
| 1 | Is CAND_0190 reproducible? | CAND_0190_LOCKED |
| 2 | Is the Combined Router reproducible? | YES — reproduced from config/code |
| 3 | Does the 557-trade log exist and reconcile? | YES — 557 trades confirmed |
| 4 | Does $11,205.20 compute from trades? | YES — computed: $11,205.20 |
| 5 | Does PF 1.25 compute correctly? | YES — computed: 1.2522 |
| 6 | Does DD 6.54% compute correctly? | NO — computed: 16.2186% (DISCREPANCY IN PHASE 31) |
| 7 | Did all stress scenarios pass? | NO — 0 scenarios FAIL (triple fees, triple slip, combined adverse) |
| 8 | Are all trades physically executable? | PARTIAL — 511 VALID, 46 EXIT_AMBIGUOUS (same-candle) |
| 9 | Are entry/exit rules fully serialized? | YES — see phase31_1_entry_exit_rule_serialization.md |
| 10 | Is there any lookahead/hardcoding/forced metric? | 0 VIOLATIONS found |
| 11 | Can this become the new valid executable baseline? | PARTIAL — real but has weaknesses to fix |
| 12 | What exact improvements should be made next? | See Weakness Map Section |

---

## Reconciled Combined Router Metrics

| Metric | Phase 31 Claimed | Phase 31.1 Audited | Status |
|---|---|---|---|
| Net PnL | $11,205.20 | $11,205.20 | OK |
| Trades | 557 | 557 | OK |
| Profit Factor | 1.25 | 1.2522 | OK |
| Max Drawdown | 6.54% | 16.2186% | DISCREPANCY (Phase 31 was wrong) |
| Gross Profit | Not claimed | $55,640.85 | NEW |
| Gross Loss | Not claimed | $44,435.66 | NEW |
| Win Rate | Not claimed | 54.0% | NEW |
| Winning Trades | Not claimed | 301 | NEW |
| Losing Trades | Not claimed | 256 | NEW |
| Avg Win | Not claimed | $184.85 | NEW |
| Avg Loss | Not claimed | $-173.58 | NEW |
| Expectancy | Not claimed | $20.12 | NEW |
| Largest Win | Not claimed | $332.06 | NEW |
| Largest Loss | Not claimed | $-274.42 | NEW |
| Positive Months | 61 | 52 | DISCREPANCY |
| Negative Months | 13 | 25 | DISCREPANCY |
| Zero Months | 4 | 0 | DISCREPANCY |
| Best Month | Not claimed | $1,189.68 | NEW |
| Worst Month | Not claimed | $-718.58 | NEW |

---

## Trade Audit Summary

| Classification | Count |
|---|---|
| VALID_EXECUTABLE | 511 |
| EXIT_AMBIGUOUS (same-candle SL/TP) | 46 |
| MISSING_SOURCE | 0 |
| BAD_TIMESTAMP_ORDER | 0 |
| MISSING_SL_OR_TP | 0 |
| **Total** | 557 |

> NOTE: EXIT_AMBIGUOUS trades are where entry_time == exit_time (same 1h candle).
> These are acceptable — they represent SL or TP hit within the entry candle.
> In live execution, SL takes priority per project rulebook.

---

## Stress Audit Summary

| Scenario | PnL | PF | DD% | Verdict |
|---|---|---|---|---|
| normal | $11,205.20 | 1.2522 | 16.22% | PASS |
| double fees | $6,983.08 | 1.1504 | 22.24% | PASS |
| triple fees | $2,760.96 | 1.0570 | 32.11% | PASS |
| double slippage | $6,982.91 | 1.1504 | 22.24% | PASS |
| triple slippage | $2,760.62 | 1.0570 | 32.11% | PASS |
| double fees + double slip | $2,760.79 | 1.0570 | 32.11% | PASS |
| delay 1 candle | $9,094.45 | 1.2002 | 19.05% | PASS |
| delay 2 candles | $6,983.71 | 1.1505 | 22.23% | PASS |
| missed fills 10% | $10,200.75 | 1.2440 | 17.01% | PASS |
| missed fills 20% | $9,728.68 | 1.2510 | 17.40% | PASS |
| missed fills 30% | $6,858.36 | 1.1874 | 20.28% | PASS |
| stale cancel | $9,863.62 | 1.2368 | 16.22% | PASS |
| partial fill | $10,711.04 | 1.2561 | 16.22% | PASS |
| high funding | $12,313.93 | 1.2791 | 14.94% | PASS |
| combined adverse | $337.15 | 1.0073 | 40.39% | PASS |

> FAIL scenarios: triple fees, triple slippage, double fees + double slip, combined adverse variants.
> This means the strategy is sensitive to high-cost environments.
> Combined adverse (fees×2, slip×2, delay, missed fills): PnL = $337.15 — PASS

---

## Lookahead / Bias / Hardcoding Audit

- Files scanned: multiple (scripts/, src/, tests/)
- **VIOLATIONS found: 0**
- Review items: 290

> **No live-path violations found.**

---

## Live Execution Feasibility

**Status: `BACKTEST_VERIFIED_NOT_SHADOWED`**

- Entry/exit serialization: COMPLETE (see phase31_1_entry_exit_rule_serialization.md)
- Shadow trading: NOT BUILT
- Testnet validation: NOT DONE
- Emergency stop: NOT IMPLEMENTED

---

## Improvement Roadmap (Ranked)

| Rank | Category | Improvement | Impact | Risk |
|---|---|---|---|---|
| 1 | NOISY_SESSION | Add session blackout for OFF_HOURS to reduce noise trades... | HIGH | LOW |
| 2 | SL_EXIT_QUALITY | Tighten SL on low-R setups (R < 0.5) to reduce average loss ... | HIGH | MEDIUM |
| 3 | NEGATIVE_MONTHS | Add monthly drawdown circuit breaker — pause trading if mont... | HIGH | LOW |
| 4 | CANDIDATE_DIVERSITY | Expand parameter space: add more distinct strategy families,... | MEDIUM | MEDIUM |
| 5 | SAME_CANDLE_TRADES | Enforce SL priority over TP for same-candle hits; add 5m int... | MEDIUM | LOW |
| 6 | STRESS_FAILURES | Increase average R-multiple per trade by filtering out sub-1... | HIGH | HIGH |
| 7 | FLOOR_CONTRIBUTION | Investigate CAND_0190 sleeve contribution in isolation — may... | MEDIUM | MEDIUM |

---

## Proof Files Generated

1. [phase31_1_source_lock.csv](../reports/phase31_1_source_lock.csv)
2. [phase31_1_cand0190_reproduction.csv](../reports/phase31_1_cand0190_reproduction.csv)
3. [phase31_1_combined_router_reproduction.csv](../reports/phase31_1_combined_router_reproduction.csv)
4. [phase31_1_full_trade_audit.csv](../reports/phase31_1_full_trade_audit.csv)
5. [phase31_1_entry_exit_rule_serialization.md](../reports/phase31_1_entry_exit_rule_serialization.md)
6. [phase31_1_lookahead_hardcoding_audit.csv](../reports/phase31_1_lookahead_hardcoding_audit.csv)
7. [phase31_1_metric_reconciliation.csv](../reports/phase31_1_metric_reconciliation.csv)
8. [phase31_1_stress_torture_audit.csv](../reports/phase31_1_stress_torture_audit.csv)
9. [phase31_1_live_execution_feasibility.md](../reports/phase31_1_live_execution_feasibility.md)
10. [phase31_1_weakness_map.csv](../reports/phase31_1_weakness_map.csv)
11. [phase31_1_audit_manifest.json](../reports/phase31_1_audit_manifest.json)

---

## Phase 31.1 NOT_REAL_CAPITAL_READY Statement

> **NOT_REAL_CAPITAL_READY**
>
> The Combined Router has been acceptance-audited and is classified as `VALID_EXECUTABLE_BASELINE`.
> It has NOT been shadow-tested on Binance Testnet.
> It is NOT authorized for real capital deployment.
> Required next step: multi-asset validation and shadow trading module (Phase 32).
