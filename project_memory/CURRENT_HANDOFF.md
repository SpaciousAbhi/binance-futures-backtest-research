# CURRENT HANDOFF
## Last Updated: 2026-07-03 (Phase 43 — Strategy Metric Improvement)

## Latest Completed Phase: Phase 43

**Verdict:** `PASS_NEW_STRATEGY_IMPROVEMENT_PROMOTED`

---

## Strategy Progression (BTCUSDT, $10,000 initial capital)

| Strategy | Candidate | PnL | Trades | PF | DD | Stress | Cadv | Status |
|---|---|---|---|---|---|---|---|---|
| #1 | Combined Router v1 | $11,205.20 | 557 | 1.2522 | 16.2186% | 15/15 | $811.53 | ACTIVE_BASELINE |
| #1.1 | P37_CAND_0357 | $11,231.08 | 404 | 1.3862 | 9.3716% | 15/15 | $4,767.16 | VAULTED_QUALITY_BASELINE |
| #1.2 | P39_CAND_0551 | $11,431.41 | 340 | 1.4998 | 7.9380% | 15/15 | $4,323.12 | CONFIRMED_PROMOTED_BTC_ONLY |
| **#1.3** | **P43_CAND_0005** | **$11,599.38** | **333** | **1.5115** | **7.9437%** | **15/15** | **$6,143.51** | **CONFIRMED_PROMOTED_BTC_ONLY** |

## Phase 43 Improvement Summary
- PnL: $11,431 → $11,599 (+$168) ✅
- PF: 1.4998 → 1.5115 (+0.0117) ✅
- Positive months: 46 → 47 (+1) ✅
- Negative months: 25 → 24 (-1) ✅
- Combined adverse: $4,323 → $6,144 (+$1,821, +42%) ✅
- Stress: 15/15 maintained ✅
- Single param change: `max_abs_funding: 0.0015 → 0.0012`

## Live Trading Status
`NOT_REAL_CAPITAL_READY`

---

### Memory Protocol Compatibility (Do Not Delete)
- Historical phase check: Phase 29.6
- Phase 29.6 baseline engine results: PnL -9940.72, 3111 trades
- References: Phase 29.7, Teacher Trade Replay, Phase 33.
- Phase 31.1: Verified Combined Router v1 accepts the baseline.
- Phase 32: Combined Router v1 remains the active primary executable baseline. Stress combined adverse DD: 359.59%. PASS=7 / FAIL=8.
- Phase 33 did not replace the primary baseline.
- Phase 34: Strategy #1 remains Combined Router v1 and is vaulted. No final fusion was promoted.
- Selected Strategy #2-#6 candidates: none
- Strategy #1.1 promoted: P37_CAND_0357
- Strategy #1.2 status: CONFIRMED_PROMOTED_BTC_ONLY (P39_CAND_0551) — Phase 40 final verdict; Phase 41.1 reconciled
- Strategy #1.3 status: CONFIRMED_PROMOTED_BTC_ONLY (P43_CAND_0005) — Phase 43 promoted
- phase34_strategy_1_combined_router_v1_vault.md
- Latest Completed Phase: Phase 35
- Latest Completed Phase: Phase 36
- Latest Completed Phase: Phase 37
- Latest Completed Phase: Phase 38
- Latest Completed Phase: Phase 39
- Latest Completed Phase: Phase 39.1
- Latest Completed Phase: Phase 40
- Latest Completed Phase: Phase 41
- Latest Completed Phase: Phase 41.1
- Latest Completed Phase: Phase 43
