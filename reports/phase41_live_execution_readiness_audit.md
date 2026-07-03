# Phase 41 — Live Execution Readiness Audit

**Status:** `NOT_REAL_CAPITAL_READY`

---

## 1. Exchange Connector
- **Binance API Integration:** The connector is configured to use USD-M Futures public REST API endpoints `/fapi/v1/klines` and `/fapi/v1/fundingRate`.
- **Private Endpoint Status:** NOT implemented/verified. Order placement APIs are mocked for shadow execution.
- **Clock Drift:** Local system clock must sync with Binance server time using NTP or by requesting `/fapi/v1/time` to prevent `TIMESTAMP_AHEAD` API rejection.

## 2. Websocket Recovery
- Websocket connections to live streams (`btcusdt@kline_1h`) require a heartbeat ping-pong mechanism.
- Auto-reconnect flow must catch connection drops, re-initialize websocket, and verify missed candles via REST API.

## 3. Order Precision & Step Sizes
According to current Binance Futures specifications:

| Asset | Price Precision (Tick Size) | Qty Precision (Step Size) | Min Notional |
|---|---|---|---|
| BTCUSDT | 0.10 USDT | 0.001 BTC | 5.0 USDT |
| ETHUSDT | 0.01 USDT | 0.001 ETH | 5.0 USDT |
| BNBUSDT | 0.01 USDT | 0.001 BNB | 5.0 USDT |
| SOLUSDT | 0.001 USDT | 0.01 SOL | 5.0 USDT |

All mock orders in the shadow dry-run simulator enforce tick and step size rounding to prevent exchange rejection.

## 4. Emergency Kill Switch & Loss Guards
- **Emergency Kill Switch:** A script that cancels all active orders and market-closes open positions immediately.
- **Daily Loss Guard:** Enforces suspension of execution if the daily account equity drop exceeds 2.5% ($250 on a $10,000 account).
- **Monthly Loss Guard:** Enforces suspension if the monthly drop exceeds 5% of account balance.

## 5. Live-Known Constraints
- Signals MUST only be evaluated on the close of 1h bars.
- Cooldown period: 5 bars after each exit must be strictly enforced.
- Single-position constraint: No new position can be entered while there is an active trade.
