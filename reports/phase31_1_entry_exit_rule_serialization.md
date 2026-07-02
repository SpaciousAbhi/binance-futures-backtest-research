# Phase 31.1 — Combined Router: Full Entry/Exit Rule Serialization

## Purpose
This document fully serializes every trading rule needed for live automation of the Combined Router.
A future automation engineer MUST be able to implement this system from this document alone.

---

## 1. Strategy Identity

| Component | Value |
|---|---|
| Strategy Name | Combined Router v1 (Phase 31.1 Locked) |
| Primary Asset | BTCUSDT Perpetual (Binance USD-M) |
| Primary Timeframe | 1-Hour OHLCV |
| Sleeves | Floor (PF1.2-derived) + CAND_0190 (Bollinger Breakout) |
| Conflict Rule | Cancel (when both sleeves signal same candle, no trade taken) |
| Fusion Mode | Union (signals from either sleeve are eligible) |
| Max Concurrent Positions | 1 at any time |
| Cooldown | 5 candles after exit before new entry allowed |

---

## 2. Data Requirements

### Required at Signal Generation Time (No Lookahead)
- Closed 1h candle OHLCV (open, high, low, close, volume)
- Bollinger Bands (period=20, std=2.0) computed from closed candles only
- ATR (period=14) computed from closed candles only
- RSI (period=14) computed from closed candles only
- ADX (period=14) computed from closed candles only
- Funding rate: latest live-known value (every 8 hours at 00:00, 08:00, 16:00 UTC)
- VWAP (optional, from volume-weighted session average)

### NOT Permitted
- Future candle data
- is_winner labels
- future_pnl / future_return
- Teacher trade labels
- Outcome-based routing features

---

## 3. Floor Strategy (PF1.2-derived) Entry Rules

### Floor Long Entry
1. Current 1h candle CLOSE is below the lower Bollinger Band at the prior close time.
2. RSI(14) < RSI_oversold_threshold (default: 30).
3. Funding rate is not extremely negative (< -0.05% per 8h) — skip if funding is deeply negative.
4. No existing position open.
5. Cooldown period satisfied (≥ 5 candles since last exit).

### Floor Short Entry
1. Current 1h candle CLOSE is above the upper Bollinger Band at the prior close time.
2. RSI(14) > RSI_overbought_threshold (default: 70).
3. Funding rate is not extremely positive (> +0.05% per 8h) — skip if funding is deeply positive.
4. No existing position open.
5. Cooldown period satisfied (≥ 5 candles since last exit).

---

## 4. CAND_0190 (Bollinger Expansion Breakout) Entry Rules

### CAND_0190 Parameters
- Template: bollinger_expansion_breakout
- tp_atr_mult: 2.0
- sl_atr_mult: 1.8
- rsi_overbought: 70
- rsi_oversold: 20
- adx_thresh: 15
- regime_filter_mode: no_filter
- trend_filter: None

### CAND_0190 Long Entry
1. Close breaks above upper Bollinger Band (expansion).
2. RSI(14) < 70 (not overbought — confirms breakout has room).
3. ADX(14) > 15 (confirms trending regime, not pure chop).
4. No existing position open.
5. Cooldown period satisfied (≥ 5 candles since last exit).

### CAND_0190 Short Entry
1. Close breaks below lower Bollinger Band (expansion).
2. RSI(14) > 20 (not oversold — confirms downside breakout has room).
3. ADX(14) > 15 (confirms trending regime).
4. No existing position open.
5. Cooldown period satisfied (≥ 5 candles since last exit).

---

## 5. Router Conflict Rules

1. If both Floor and CAND_0190 signal a Long on the same candle: **CANCEL** (no trade).
2. If both Floor and CAND_0190 signal a Short on the same candle: **CANCEL** (no trade).
3. If Floor signals Long and CAND_0190 signals Short on the same candle: **CANCEL** (no trade).
4. If only one sleeve signals: take that signal.

---

## 6. Order Type and Execution Model

| Component | Rule |
|---|---|
| Entry order | Market order at next open after signal candle closes |
| SL order | Limit order placed immediately upon entry fill |
| TP order | Limit order placed immediately upon entry fill |
| Order model | Touch-fill: SL/TP triggered when price touches the level |
| Reduce-only | Exit orders are reduce-only |
| Max wait | If entry order not filled within 1 candle, cancel |

---

## 7. Position Sizing

| Component | Rule |
|---|---|
| Risk per trade | 1.0% of current account equity |
| Position size | risk_amount / (entry_price * sl_distance_pct) |
| Tick size | 0.01 USDT (BTC contract) |
| Step size | 0.001 BTC minimum |
| Min notional | $5 minimum trade notional |
| Max leverage | Constrained by monthly_risk_limit (2.5% monthly drawdown cap) |

---

## 8. Stop Loss Rules

| Component | Rule |
|---|---|
| SL basis | ATR(14) * sl_atr_mult from entry price |
| Floor sl_atr_mult | Derived from PF1.2 teacher — approximately 1.5× ATR |
| CAND_0190 sl_atr_mult | 1.8 |
| Long SL | entry_price - (ATR * sl_atr_mult) |
| Short SL | entry_price + (ATR * sl_atr_mult) |
| SL type | Hard stop (not trailing on entry) |
| Same-candle SL/TP | SL takes priority if both triggered in same candle |

---

## 9. Take Profit Rules

| Component | Rule |
|---|---|
| TP basis | ATR(14) * tp_atr_mult from entry price |
| Floor tp_atr_mult | Derived from PF1.2 teacher — approximately 2.0× ATR |
| CAND_0190 tp_atr_mult | 2.0 |
| Long TP | entry_price + (ATR * tp_atr_mult) |
| Short TP | entry_price - (ATR * tp_atr_mult) |
| TP type | Limit order, reduce-only |

---

## 10. Time Stop Rules

| Component | Rule |
|---|---|
| Max hold time | 240 candles (10 days at 1h timeframe) |
| Time stop action | Close at market price if position still open after 240 candles |
| Breakeven rule | Move SL to entry price once trade reaches +0.5R |

---

## 11. Fee and Slippage Model

| Component | Rule |
|---|---|
| Entry fee | Taker 0.05% (market order) |
| Exit fee | Taker 0.05% (stop/limit touched = market fill in backtest) |
| Entry slippage | 0.05% of notional |
| Exit slippage | 0.05% of notional |
| Funding | Deducted every 8 hours at 00:00, 08:00, 16:00 UTC |
| Funding calculation | size × mark_price × funding_rate (direction-adjusted) |

---

## 12. Session Rules

| Session | UTC Hours | Notes |
|---|---|---|
| Asia | 02:00–09:59 | Lower volume; caution on limit fills |
| London | 08:00–15:59 | Primary trading session |
| NY | 13:00–20:59 | Overlap with London is high-volume |
| Off-hours | 22:00–01:59 | Low liquidity; stale cancel risk highest |

No session blackout is applied in current backtests.
Recommended future filter: skip entries in off-hours (22:00–01:59 UTC).

---

## 13. Funding Rules

| Rule | Value |
|---|---|
| Funding source | Live Binance funding rate API (updated every 8h) |
| Extreme positive funding skip | If funding_rate > +0.05%: skip new Short entry |
| Extreme negative funding skip | If funding_rate < -0.05%: skip new Long entry |
| Funding applied in backtest | Yes — deducted on every 8h mark while position is open |

---

## 14. Pending Order Expiry

| Rule | Value |
|---|---|
| Limit order max wait | 1 candle after signal |
| Stale cancel trigger | If entry price not reached within 1 candle: cancel order |
| Stale cancel impact | In stress test: 5% stale cancel reduces PnL by ~$5,331 |

---

## 15. Max Concurrent Positions

| Rule | Value |
|---|---|
| Max positions | 1 |
| Conflict handling | Only one sleeve active at a time; cancel if both fire |
| New signal during open position | Ignored until cooldown after exit |

---

## Live Execution Status

**STATUS: BACKTEST_VERIFIED_NOT_SHADOWED**

This router has been verified in backtesting.
It has NOT been shadow-tested on Binance Testnet.
It is NOT real-capital ready.
Shadow testing requirement: ≥ 30 days of live signal monitoring.
