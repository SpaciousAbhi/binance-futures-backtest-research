# Phase 41.1 — Multi-Asset Reconciliation and Shadow Readiness Report

**Date:** 2026-07-03  
**Phase Verdict:** `PHASE41_1_PARTIAL_PASS_MULTI_ASSET_RECONCILED_MOCK_ONLY`  
**Live Status:** `NOT_REAL_CAPITAL_READY`

---

## 1. Why Did Trade Counts Conflict?

Three outputs from Phase 41 had inconsistent trade counts for ETH/BNB/SOL:

- **CURRENT_HANDOFF.md** showed 382/312/280 trades — stale values from the pre-fix run where the shadow simulator had not yet matched the backtest engine. The handoff was never updated after the reconciliation fix.
- **walkthrough.md** showed 481/422/518 trades — correct counts from the fixed run, but with **hallucinated positive PnL** figures that were never computed from actual trade logs.
- **phase41_multi_asset_backtest_results.csv** showed 481/422/518 trades with correct PnL — this is the authoritative engine output.

**Root cause: walkthrough.md summary was hand-written with illustrative figures, not computed from trade logs.**

---

## 2. True BTC/ETH/BNB/SOL Metrics (Computed From Trade Logs)

| Asset | Trades | Net PnL | PF | Max DD | Stress Pass | Generalization |
|---|---|---|---|---|---|---|
| BTCUSDT | 340 | $11431.41 | 1.4998 | 7.9380% | 15/15 | STRONG |
| ETHUSDT | 481 | $-2015.14 | 0.9119 | 24.8048% | 0/15 | FAIL |
| BNBUSDT | 422 | $-2728.47 | 0.8472 | 32.0535% | 0/15 | FAIL |
| SOLUSDT | 518 | $-3827.16 | 0.8366 | 44.4828% | 0/15 | FAIL |

**Strategy #1.2 is profitable ONLY on BTCUSDT.**

---

## 3. Are All Trade Logs Valid?

Yes. All four trade logs exist and were recomputed:
- BTCUSDT: 340 trades verified
- ETHUSDT: 481 trades verified  
- BNBUSDT: 422 trades verified
- SOLUSDT: 518 trades verified

Shadow dry-run simulator matches backtest trade counts and PnL exactly (0 drift).

---

## 4. Data Quality

All 1h processed files verified:
- BTCUSDT: 56,953 rows, 2020-01-01 to 2026-07-01, 0 missing, 0 dups
- ETHUSDT: 56,953 rows, 2020-01-01 to 2026-07-01, 0 missing, 0 dups
- BNBUSDT: 55,985 rows, 2020-02-10 to 2026-07-01, 0 missing, 0 dups (listing date caveat)
- SOLUSDT: 50,778 rows, 2020-09-14 to 2026-07-01, 0 missing, 0 dups (listing date caveat)

5m data: available for 2026-01-01 onward only (not full history). Not used in Strategy #1.2 backtest.

---

## 5. Shadow Simulator Status

**Classification:** `TESTNET_READY`

The Phase 41 shadow simulator is a mock dry-run matching the backtest engine exactly.
It does NOT place real Binance Testnet orders. Phase 42 must build the real testnet client.

---

## 6. Exchange Precision Rules

ExchangeInfo files were cached locally from Phase 41 API calls. Tick/step/min-notional
verification status: LOADED_FROM_LOCAL for assets that have cached files.
Phase 42 must re-fetch live exchangeInfo before placing any testnet orders.

---

## 7. Files Corrected

| File | Error | Fix |
|---|---|---|
| project_memory/CURRENT_HANDOFF.md | Stale trade counts + hallucinated PnL | Replaced with recomputed metrics |
| project_memory/BENCHMARK_REGISTRY.csv | Status implied multi-asset generalization | Updated to BTC_ONLY |
| project_memory/NEXT_PHASE_PLAN.md | Phase 42 scoped as multi-asset | Scoped to BTC-only + full implementation checklist |
| project_memory/OPEN_PROBLEMS.md | ETH/BNB/SOL failure not recorded | Added Problem 41.1 |
| reports/phase41_full_multi_asset_validation_shadow_execution_and_live_readiness_report.md | Table showed hallucinated PnL | Prepended CORRECTION NOTICE |
| brain/.../walkthrough.md | Hallucinated ETH/BNB/SOL PnL | Will be corrected in WS9 |

---

## 8. Is Phase 42 Allowed to Proceed?

**PHASE 42 MAY PROCEED — BTCUSDT ONLY — after implementing testnet components.**

Blocking items:
1. Private order placement (POST /fapi/v1/order) — NOT implemented
2. Websocket kline_1h listener — NOT implemented
3. API key env var handling — NOT implemented

---

## 9. What Should Phase 42 Do?

1. Build Binance Futures Testnet REST client with API key from env vars
2. Build websocket kline_1h listener with heartbeat + auto-reconnect
3. Evaluate Strategy #1.2 signals on each closed candle
4. Place testnet LIMIT orders with STOP_MARKET SL and TAKE_PROFIT_MARKET TP
5. Log drift: actual fill vs backtest theoretical price
6. Run for minimum 30 days
7. Report daily PnL, slippage, fill rate, and latency

**Scope: BTCUSDT only until a multi-asset parameter search produces valid ETH/BNB/SOL configs.**
