# Entry & Exit Rules Serialization — Precision Fusion 7.0

## 1. Entry Sleeve Specifications

### Sleeve 1: Precision Fusion 1.2 Core Retest
- **Timeframe:** 1h
- **Setup Candle:** Close above Bollinger Band Upper Band
- **Trigger Candle:** Pullback retest of Band Midpoint
- **Long Entry Condition:** Price touches Band Midpoint + (ATR * 0.1) on closed-candle confirm
- **Short Entry Condition:** Price touches Band Midpoint - (ATR * 0.1) on closed-candle confirm
- **Funding filter:** Skip if abs(funding) > 0.05%

### Sleeve 2: Second Retest Expansion Sleeve
- **Timeframe:** 15m
- **Setup Candle:** 1h Support/Resistance breakout
- **Trigger Candle:** Second retest touch on 15m Support/Resistance
- **Long Entry Condition:** Price reclaim of structural swing low
- **Short Entry Condition:** Price rejection of structural swing high

### Sleeve 3: VWAP Reclaim Sleeve
- **Timeframe:** 5m
- **Setup Candle:** VWAP deviation exceeding 2.5x standard deviation
- **Trigger Candle:** Closed-candle reclaim of 2.0x standard deviation band

---

## 2. Exit Rules Specifications

- **Stop Loss (SL):** 1.5 * 14-period closed ATR (stop-market order)
- **Take Profit (TP):** 2.5 * 14-period closed ATR (limit order)
- **Same-Candle TP/SL Priority:** SL is assumed touched first if both limits are hit in the same candle
- **Time Stop:** Terminate trade if in position > 24 candles without reaching 1.0R
- **Breakeven Stop:** Move SL to BE once favorable excursion reaches 0.5R
