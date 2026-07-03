# Phase 44 — Full Green Test Repair & Strategy #1.4 Search Report

**Date:** 2026-07-03
**Phase Verdict:** `PHASE44_PARTIAL_PASS_TESTS_GREEN_NO_STRATEGY_UPGRADE`
**Live Status:** `NOT_REAL_CAPITAL_READY`

---

## 1. Executive Summary

Phase 44 resolved outstanding test debt, truth-locked the Strategy #1.3 champion baseline, performed trade-level diagnostics, and conducted an optimization sweep of 199 candidate parameters to find a Strategy #1.4 upgrade.

### Test Debt Fixes
1. **Pytest Stale Assertion:** Corrected `tests/test_phase37_strategy1_1_optimization.py` line 160 to correctly allow Phase 38 to be either in the next phase plan or in the completed hands-off timeline. Full suite status: **654/654 passed (100% green)**.
2. **CLI Command NameErrors:** Fixed `scripts/research_lab.py` by implementing missing functions `handle_memory_check()`, `handle_data_check()`, and `handle_audit()`.

### Strategy #1.3 baseline Lock
Strategy #1.3 reproduced exactly:
- PnL: $11599.38
- Trades: 333
- PF: 1.5115
- DD: 7.9437%
- Stress Verdict: 15/15 Pass (Combined Adverse PnL: $6143.51)

### Search Search & Verdict
- **Verdict:** `PHASE44_PARTIAL_PASS_TESTS_GREEN_NO_STRATEGY_UPGRADE`

No candidate fulfilled all strict promotion requirements (including beating Strategy #1.3 on at least 5 metrics while maintaining 15/15 stress and positive combined adverse). 
**Strategy #1.3 remains the active champion baseline.**

---

## 2. Sleeve Performance (P43_CAND_0005)

| Sleeve | Trades | PnL | PF |
|---|---|---|---|
| ATR Expansion Long | 33 | $1043.72 | 1.3492 |
| ATR Expansion Short | 29 | $1912.15 | 1.9313 |
| BB Expansion Long | 93 | $3870.69 | 1.6586 |
| BB Expansion Short | 98 | $1725.51 | 1.2277 |
| Funding Reversal Long | 2 | $259.05 | 999.0000 |
| Funding Reversal Short | 69 | $1382.54 | 1.3654 |
| Low-Activity Filler Short | 9 | $1405.72 | 4.5259 |


---

## 3. Session Performance (P43_CAND_0005)

| Session | Trades | PnL |
|---|---|---|
| LONDON | 82 | $2519.56 |
| NEW_YORK | 231 | $9056.66 |
| OFF_HOURS | 20 | $23.16 |


---

## 4. Yearly Comparison

| Year | Strategy #1.2 PnL | Strategy #1.3 PnL | Strategy #1.4/Final PnL |
|---|---|---|---|
| 2020 | $310.57 | $377.59 | $377.59 |
| 2021 | $3595.39 | $3638.60 | $3638.60 |
| 2022 | $2485.40 | $2506.51 | $2506.51 |
| 2023 | $609.96 | $614.38 | $614.38 |
| 2024 | $1884.44 | $1896.91 | $1896.91 |
| 2025 | $1130.32 | $1144.51 | $1144.51 |
| 2026 | $1415.32 | $1420.88 | $1420.88 |

---

## 5. Month-by-Month Comparison

| Month | Strategy #1.2 PnL | Strategy #1.3 PnL | Strategy #1.4/Final PnL |
|---|---|---|---|
| 2020-01 | $309.48 | $309.48 | $309.48 |
| 2020-02 | $-340.03 | $-340.03 | $-340.03 |
| 2020-03 | $259.17 | $259.17 | $259.17 |
| 2020-04 | $402.85 | $402.85 | $402.85 |
| 2020-05 | $-25.56 | $-25.56 | $-25.56 |
| 2020-06 | $44.19 | $44.19 | $44.19 |
| 2020-07 | $-214.93 | $-135.70 | $-135.70 |
| 2020-08 | $-185.31 | $-197.37 | $-197.37 |
| 2020-09 | $202.64 | $204.05 | $204.05 |
| 2020-10 | $16.26 | $16.50 | $16.50 |
| 2020-11 | $4.31 | $4.09 | $4.09 |
| 2020-12 | $-162.51 | $-164.10 | $-164.10 |
| 2021-01 | $374.98 | $496.08 | $496.08 |
| 2021-02 | $262.89 | $177.10 | $177.10 |
| 2021-03 | $394.74 | $398.28 | $398.28 |
| 2021-04 | $451.93 | $448.26 | $448.26 |
| 2021-05 | $532.13 | $531.09 | $531.09 |
| 2021-06 | $-32.58 | $-33.80 | $-33.80 |
| 2021-07 | $321.90 | $324.67 | $324.67 |
| 2021-08 | $458.93 | $462.96 | $462.96 |
| 2021-09 | $-46.96 | $-46.04 | $-46.04 |
| 2021-10 | $724.25 | $727.31 | $727.31 |
| 2021-11 | $287.01 | $289.08 | $289.08 |
| 2021-12 | $-133.84 | $-136.38 | $-136.38 |
| 2022-01 | $422.78 | $427.19 | $427.19 |
| 2022-02 | $551.05 | $556.09 | $556.09 |
| 2022-03 | $196.15 | $197.42 | $197.42 |
| 2022-04 | $-450.72 | $-454.01 | $-454.01 |
| 2022-05 | $183.88 | $184.60 | $184.60 |
| 2022-06 | $359.75 | $362.60 | $362.60 |
| 2022-07 | $368.92 | $372.93 | $372.93 |
| 2022-08 | $24.89 | $25.28 | $25.28 |
| 2022-09 | $-77.31 | $-77.81 | $-77.81 |
| 2022-10 | $218.00 | $219.81 | $219.81 |
| 2022-11 | $415.79 | $417.88 | $417.88 |
| 2022-12 | $272.23 | $274.53 | $274.53 |
| 2023-01 | $236.97 | $239.06 | $239.06 |
| 2023-02 | $443.05 | $446.82 | $446.82 |
| 2023-03 | $987.43 | $995.12 | $995.12 |
| 2023-04 | $-148.48 | $-149.72 | $-149.72 |
| 2023-05 | $252.85 | $254.36 | $254.36 |
| 2023-06 | $-612.13 | $-616.78 | $-616.78 |
| 2023-08 | $-165.78 | $-167.23 | $-167.23 |
| 2023-10 | $-191.14 | $-192.88 | $-192.88 |
| 2023-11 | $-192.52 | $-194.67 | $-194.67 |
| 2023-12 | $-0.30 | $0.31 | $0.31 |
| 2024-01 | $500.39 | $507.54 | $507.54 |
| 2024-02 | $692.21 | $696.13 | $696.13 |
| 2024-03 | $-486.36 | $-493.45 | $-493.45 |
| 2024-04 | $-120.34 | $-122.13 | $-122.13 |
| 2024-05 | $252.87 | $255.47 | $255.47 |
| 2024-06 | $-144.42 | $-145.20 | $-145.20 |
| 2024-07 | $-386.46 | $-390.37 | $-390.37 |
| 2024-08 | $992.17 | $1000.33 | $1000.33 |
| 2024-09 | $-507.29 | $-511.81 | $-511.81 |
| 2024-11 | $628.82 | $630.25 | $630.25 |
| 2024-12 | $462.87 | $470.15 | $470.15 |
| 2025-01 | $363.44 | $364.01 | $364.01 |
| 2025-02 | $106.76 | $113.00 | $113.00 |
| 2025-03 | $661.73 | $672.83 | $672.83 |
| 2025-04 | $206.26 | $205.22 | $205.22 |
| 2025-05 | $275.22 | $277.39 | $277.39 |
| 2025-09 | $-238.06 | $-239.89 | $-239.89 |
| 2025-10 | $592.37 | $598.17 | $598.17 |
| 2025-11 | $-191.27 | $-193.03 | $-193.03 |
| 2025-12 | $-646.15 | $-653.19 | $-653.19 |
| 2026-01 | $290.24 | $292.03 | $292.03 |
| 2026-02 | $657.33 | $659.97 | $659.97 |
| 2026-03 | $375.27 | $376.28 | $376.28 |
| 2026-05 | $294.56 | $296.25 | $296.25 |
| 2026-06 | $-202.08 | $-203.64 | $-203.64 |

---

## 6. Integrity Audit Checks

- **Lookahead Bias:** None. Only closed-candle signals and live-known variables (like funding rate at bar close) are used.
- **Outcome Filter:** None. No Completed-trade properties used as logic conditions.
- **Forced Metrics:** None. Recomputed strictly from backtest engine trade logs.

---

## 7. Next Phase Recommendation

Phase 45:
- Proceed to BTC-only shadow execution client setup (websocket feed + private endpoints) using the parameters of the active champion strategy (P43_CAND_0005).
