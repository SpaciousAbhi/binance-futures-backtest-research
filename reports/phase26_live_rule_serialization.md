# Live Rule Serialization — Precision Fusion 8.0

## 1. Entry Specification
- **Timeframe:** 1h and 15m
- **Setup Candle:** Support/resistance breakout
- **Expected-R Gate:** >= 1.8 for Tokyo squeeze, >= 2.0 for NY session breakout
- **Funding Skip filter:** Skip if abs(funding) > 0.04%

## 2. Exit Specification
- **Stop Loss:** 1.5 * closed ATR (stop-market)
- **Take Profit:** 2.5 * closed ATR (limit)
- **Same-Candle TP/SL:** SL is touched first
