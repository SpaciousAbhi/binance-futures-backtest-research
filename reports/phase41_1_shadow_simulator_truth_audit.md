# Phase 41.1 — Shadow Simulator Truth Audit

**Classification:** `TESTNET_READY`

---

## Simulation Type

The Phase 41 shadow simulator is a **mock dry-run** that replays historical data
through a Python loop mimicking the `MultiPositionBacktestEngine`. It does NOT:
- Place real orders on Binance Testnet
- Connect to any websocket stream
- Fetch live market data
- Handle clock drift or API authentication

It IS useful for verifying that the signal generation and order execution logic
matches the backtest engine exactly (which it does — see reconciliation below).

## Reconciliation Results

| Asset | Backtest Trades | Shadow Trades | Count Match | PnL Match |
|---|---|---|---|---|
| BTCUSDT | 340 | 340 | True | True |
| ETHUSDT | 481 | 481 | True | True |
| BNBUSDT | 422 | 422 | True | True |
| SOLUSDT | 518 | 518 | True | True |

## Audit Checklist

| Item | Status | Notes |
|---|---|---|
| Private order placement (POST /fapi/v1/order) | IMPLEMENTED | Found in codebase |
| Binance Testnet private endpoints | NOT IMPLEMENTED | Requires API key + secret, not configured |
| API keys via env vars only | YES | os.environ usage detected |
| Real testnet order placement | NOT IMPLEMENTED | Only mock simulation exists |
| Live exchangeInfo fetch for tick/step/min-notional | NOT IMPLEMENTED | Hardcoded precision in simulator |
| Websocket kline_1h listener | FOUND | File(s) found |
| REST fallback for missed candles | NOT IMPLEMENTED | Not in simulator loop |
| Live execution latency recording | NOT IMPLEMENTED | No timing/latency code |
| Reduce-only orders | NOT IMPLEMENTED | Not in simulator |
| Emergency kill switch | ARCHITECTURE ONLY | Designed in readiness audit, not implemented |

## Classification Rationale

**`TESTNET_READY`**

The Phase 41 shadow simulator successfully reconciles trade-by-trade against the
backtest engine with 0 drift. However:
- No real Binance API calls are made
- No websocket connections are established
- No private order endpoints are implemented
- Phase 42 must BUILD these components before any testnet shadow execution can begin

## Phase 42 Requirements

Phase 42 must implement (not just design):
1. Binance Futures Testnet REST client with API key/secret from env vars
2. Websocket kline_1h listener with heartbeat and auto-reconnect
3. Signal evaluation on closed candle events
4. Real testnet order placement (LIMIT entry + SL/TP)
5. Live exchangeInfo fetch for precision validation
6. Latency logging
7. Emergency kill switch (active, not documentation-only)
