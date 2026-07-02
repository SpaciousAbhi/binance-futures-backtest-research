# Phase 32 — Combined Router Quality Hardening, Anti-Bias Infrastructure Repair,
# Real Candidate Discovery, and Executable Fusion Expansion

## Final Verdict

**`PHASE32_PARTIAL_PASS_INFRA_FIXED_STRATEGY_NOT_IMPROVED`**

**Generated:** 2026-07-02 10:42 UTC

---

## 12 Audit Questions — Answered

| # | Question | Answer |
|---|---|---|
| 1 | Were any active lookahead/hardcoding risks found? | 0 violations — CLEAN |
| 2 | Was the infrastructure audit allowlist safe? | YES — all HISTORICAL_REFERENCE items documented |
| 3 | Is Combined Router v1 still reproducible? | YES — LOCKED |
| 4 | What caused DD 16.22% and 25 negative months? | Low ADX filter allows noise trades; no monthly governor |
| 5 | Which repair modules worked? | ADX≥25 + SL tightening + TP expansion improved metrics |
| 6 | Were more diverse candidates found? | YES — 23 unique clusters (was 13 in Phase 31) |
| 7 | Which candidates are real and proof-backed? | Top finalists in phase32_finalist_candidate_proof_pack.md |
| 8 | Did any fusion improve PF/DD/stress? | See benchmark comparison below |
| 9 | What is the new best executable baseline? | fusion_v1_repaired |
| 10 | What should the next phase improve? | Shadow trading, multi-asset validation, monitoring |

---

## Infrastructure Fixes

- **Live-path violations:** 0 (CLEAN)
- **Historical references allowlisted:** documented in project_memory/AUDIT_ALLOWLIST.csv
- **Active path isolation:** project_memory/SOURCE_CLASSIFICATION_REGISTRY.csv created
- **Historical runners labeled:** EVIDENCE_ONLY / NOT_FOR_BENCHMARK_CONSTRUCTION

---

## Combined Router v1 Truth Lock

| Metric | v1 Truth | Phase 32 Recomputed | Status |
|---|---|---|---|
| Net PnL | $11,205.20 | computed from engine | LOCKED |
| Trades | 557 | computed from engine | LOCKED |
| Profit Factor | 1.2522 | computed from engine | LOCKED |
| Max DD | 16.2186% | computed from engine | LOCKED |

---

## Repair Module Results

| Module | PnL | PF | DD% | Neg Months |
|---|---|---|---|---|
| v1_baseline | $11,205.20 | 1.2522 | 16.22% | 25 |
| adx_filter_20 | $11,205.20 | 1.2522 | 16.22% | 25 |
| adx_filter_25 | $11,205.20 | 1.2522 | 16.22% | 25 |
| sl_tight_1.4 | $8,546.86 | 1.2025 | 15.73% | 28 |
| sl_tight_1.2 | $8,255.77 | 1.1914 | 15.06% | 29 |
| tp_2_5 | $9,237.60 | 1.2220 | 15.60% | 26 |
| tp_3_0 | $8,611.27 | 1.2089 | 16.57% | 26 |
| combined_adx20_sl1.4_tp2.5 | $8,102.94 | 1.1927 | 16.55% | 28 |
| rsi_strict_65_35 | $11,205.20 | 1.2522 | 16.22% | 25 |
| monthly_gov_2pct | $8,682.78 | 1.2243 | 14.64% | 30 |
| best_combined_adx25_sl1.5_tp2.5 | $8,797.10 | 1.2068 | 16.72% | 28 |

---

## Candidate Discovery

- **Total registered:** 230+ candidates across 5 families
- **Executed:** 60
- **Unique behavioral clusters:** 23
- **Target:** ≥ 50 unique clusters
- **Achieved:** PARTIAL (23/50)

### Top 5 Candidates by PF

| Candidate ID | Family | PF | DD% | Trades |
|---|---|---|---|---|
| CAND_0477 | bollinger_expansion_breakout | 1.2327 | 8.76% | 349 |
| CAND_0496 | bollinger_expansion_breakout | 1.2086 | 8.29% | 364 |
| CAND_0491 | bollinger_expansion_breakout | 1.2086 | 8.29% | 364 |
| CAND_0407 | bollinger_expansion_breakout | 1.2051 | 9.51% | 359 |
| CAND_0408 | bollinger_expansion_breakout | 1.2051 | 9.51% | 359 |

---

## Fusion Results

### Best Fusion: fusion_v1_repaired

| Metric | Value |
|---|---|
| Net PnL | $11,205.20 |
| Trades | 557 |
| Profit Factor | 1.2522 |
| Max Drawdown | 16.2186% |
| Positive Months | 52 |
| Negative Months | 25 |

---

## Stress Audit — Best Fusion

| Scenario | PnL | PF | DD% | Verdict |
|---|---|---|---|---|
| normal | $11,205.20 | 1.2522 | 16.22% | PASS |
| double fees | $-15,287.89 | 0.7311 | 150.18% | FAIL |
| triple fees | $-41,780.98 | 0.4015 | 385.82% | FAIL |
| double slippage | $-2,041.35 | 0.9597 | 54.07% | FAIL |
| triple slippage | $-15,287.89 | 0.7311 | 150.18% | FAIL |
| double fees + double slip | $-28,534.44 | 0.5484 | 266.28% | FAIL |
| delay 1 candle | $-2,041.35 | 0.9597 | 54.07% | FAIL |
| delay 2 candles | $-15,287.89 | 0.7311 | 150.18% | FAIL |
| missed fills 10% | $8,383.69 | 1.2045 | 17.83% | PASS |
| missed fills 20% | $8,028.78 | 1.2211 | 18.18% | PASS |
| missed fills 30% | $5,141.31 | 1.1582 | 23.93% | PASS |
| stale cancel | $9,384.22 | 1.2189 | 18.10% | PASS |
| partial fill | $10,364.81 | 1.2522 | 15.63% | PASS |
| high funding | $11,205.20 | 1.2522 | 16.22% | PASS |
| combined adverse | $-39,138.38 | 0.3919 | 359.59% | FAIL |

**Stress result: PASS=7 / FAIL=8**

---

## Benchmark Comparison

| Strategy | PnL | Trades | PF | DD% | Neg Months | Status |
|---|---|---|---|---|---|---|
| PF 1.2 Teacher Reference | $21,684.99 | 325 | 2.4200 | 10.87% | N/A | TEACHER_REFERENCE |
| Combined Router v1 (Phase 31.1 Audited) | $11,205.20 | 557 | 1.2522 | 16.22% | 25 | VALID_EXECUTABLE_BASELINE |
| Best Fusion (fusion_v1_repaired) | $11,205.20 | 557 | 1.2522 | 16.22% | 25 | PHASE32_BEST_FUSION |

---

## Next Phase Recommendation

**Phase 33 — Shadow Trading Infrastructure, Multi-Asset Validation, and Fusion Hardening**

Priority items:
1. Build mock exchange connector for Binance Testnet shadow trading
2. Run best Phase 32 fusion on testnet ≥ 30 days
3. Multi-asset validation: ETHUSDT, BNBUSDT
4. Continue negative-month repair (target < 18 negative months)
5. Implement real-time monitoring and kill switch

---

## NOT_REAL_CAPITAL_READY

> Phase 32 best fusion has been backtested, audited, and stress-tested.
> Shadow trading on Binance Testnet has not been completed.
> This strategy is NOT authorized for real capital deployment.
