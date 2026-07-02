# NEXT PHASE PLAN
## Phase 32 — Multi-Asset Strategy Hardening, Bad-Month Recovery Surgery, and Shadow Trading Scaffolding
## Last Updated: 2026-07-02 (Phase 31)

---

## Phase Identity

| Item | Value |
|---|---|
| Phase number | 32 |
| Phase name | Multi-Asset Strategy Hardening, Bad-Month Recovery Surgery, and Shadow Trading Scaffolding |
| Phase type | Strategy Hardening & Integration Scaffolding |
| Estimated complexity | Medium-High |
| Depends on | Phase 31 outputs (CAND_0190 baseline, Combined Router) |
| Must NOT do | Blind candidate search, claim live readiness, use future lookahead |

---

## Goal

Harden the newly discovered Phase 31 Combined Router across validation assets, optimize its sleeve weights and rescue zero/negative months to raise the profit factor, and scaffold shadow trading connectors to prepare for live testing.

---

## Specific Objectives

### Objective 1 — Multi-Asset Validation
Validate the CAND_0190 strategy baseline and the Combined Router on ETHUSDT, BNBUSDT, and SOLUSDT:
1. Run backtests on validation assets using Phase 31 engine settings.
2. Confirm there is no significant performance decay or overfit on validation assets.
3. Record monthly and yearly metrics tables for each asset.

### Objective 2 — Sleeve Weight Optimization & Bad-Month Recovery Surgery
Analyze the zero and negative PnL months of the Combined Router:
1. Design rule-based filters (e.g., ADX trend thresholds, session-specific entry restrictions, or funding extreme skips) targeting specific losing regimes.
2. Optimize candidate/sleeve risk allocation weights without lookahead bias.
3. Aim to raise the combined profit factor from 1.25 to 1.50+.

### Objective 3 — Shadow Trading Automation Scaffolding
Build the skeleton code for a shadow paper-trading container/module:
1. Define a mock exchange client interfacing with the Binance Perpetual API (or mock data generator).
2. Scaffold order placement, tick-by-tick/minute-by-minute execution simulator, and trade log serialization.
3. Validate order lifecycle states (submitted, filled, cancelled, rejected).

---

## Input Files Required

| File | Purpose |
|---|---|
| `reports/phase31_best_router_trade_log.csv` | Phase 31 BTCUSDT trade trace |
| `reports/phase31_candidate_results.csv` | Sweep metrics |
| `data/processed/ETHUSDT_1h_processed.csv` | Validation asset data |
| `data/processed/BNBUSDT_1h_processed.csv` | Validation asset data |
| `data/processed/SOLUSDT_1h_processed.csv` | Validation asset data |

---

## Output Files Required

| File | Content |
|---|---|
| `reports/phase32_multi_asset_results.csv` | Combined Router results on ETH, BNB, SOL |
| `reports/phase32_optimized_weights.json` | Optimized candidate/sleeve allocation weights |
| `reports/phase32_shadow_trading_scaffolding.py` | Shadow trading skeleton script |
| `reports/phase32_audit_manifest.json` | File hashes and sizes |
| `reports/phase32_strategy_hardening_report.md` | Phase 32 breakthrough and validation report |

---

## Success Criteria

Phase 32 is considered PASS if:
- Validation asset backtest results are computed and logged.
- Weight optimization and bad-month surgery successfully increase the profit factor.
- Shadow trading scaffolding skeleton is functional and mock-tested.
- Main report, manifest, and test files are committed.
- `project_memory/CURRENT_HANDOFF.md` is updated.
