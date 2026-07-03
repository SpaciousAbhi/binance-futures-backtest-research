# Next Phase Plan - Phase 41

## Goal
Multi-asset validation of Strategy #1.2 (P39_CAND_0551) across ETHUSDT, BNBUSDT, and SOLUSDT,
and begin shadow execution schema design for Binance testnet.

## Context (Phase 40 Result)
Strategy #1.2 is CONFIRMED PROMOTED after stress harness repair.
- Corrected stress: 15/15 pass
- Combined adverse (corrected): $4323.12
- Passing tracks: ['C']

## Phase 41 Requirements

### P1 — Multi-Asset Backtest
Run Strategy #1.2 parameter set on ETHUSDT, BNBUSDT, SOLUSDT processed data.
Verify the edge is not overfit to BTC.

### P2 — Shadow Execution Schema Design
Design the live testnet execution protocol:
- Order placement (limit/market entry based on session + ATR)
- SL/TP management (ATR-based, computed at entry)
- Position sizing
- Funding filter enforcement

### P3 — Live Automation Readiness Audit
Confirm all required real-time data feeds exist and are accessible.

Live status remains NOT_REAL_CAPITAL_READY.

---

### Memory Protocol Compatibility (Do Not Delete)
- Historical continuity references: Phase 33, Phase 37, Phase 38, Phase 39, Phase 39.1, Phase 40.
