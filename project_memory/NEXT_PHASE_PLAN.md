# Next Phase Plan — Phase 42

## Goal
Binance Futures Testnet shadow execution of Strategy #1.2 — BTCUSDT ONLY.

## Scope Decision After Phase 41.1 Reconciliation

Strategy #1.2 (P39_CAND_0551) is profitable ONLY on BTCUSDT.
ETH, BNB, and SOL are unprofitable under current parameters.
Phase 42 must target BTCUSDT only, or a separate multi-asset parameter
search phase must be inserted before multi-asset testnet execution.

## Phase 42 Must Implement (Not Just Design)

### P1 — Binance Futures Testnet REST Client
- API key and secret from environment variables only (never hardcoded)
- Endpoints: POST /fapi/v1/order, GET /fapi/v2/account
- Validate tick/step/min-notional from live exchangeInfo

### P2 — Websocket kline_1h Closed-Candle Listener
- Subscribe to btcusdt@kline_1h
- Parse closed candle events (kline.x == true)
- Auto-reconnect with exponential backoff
- REST fallback to verify no candles were missed

### P3 — Signal Execution
- Run Strategy #1.2 signal check on each closed candle
- Place LIMIT entry orders only on valid signals
- Place STOP_MARKET SL and TAKE_PROFIT_MARKET TP orders

### P4 — Drift Tracking
- Record actual fill price vs backtest expected price
- Log fill latency, slippage, and spread
- Compare daily PnL vs backtest daily PnL

### P5 — Emergency Kill Switch
- Implement and test: cancel all orders + market close all positions
- Trigger on: daily loss > 2.5%, monthly loss > 5%

## Shadow Readiness Starting Point
`TESTNET_READY` — Must upgrade to TESTNET_READY before Phase 42 completes.

## Live Status
`NOT_REAL_CAPITAL_READY`

---

### Memory Protocol Compatibility (Do Not Delete)
- Historical continuity references: Phase 33, Phase 37, Phase 38, Phase 39, Phase 40, Phase 41, Phase 41.1
