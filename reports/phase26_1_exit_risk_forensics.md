# Exit & Risk Forensics — Precision Fusion 8.0

- **SL Logic:** 1.5 * closed ATR. Built as stop-market order, executed immediately on price trigger.
- **TP Logic:** 2.5 * closed ATR. Built as limit order on exchange book.
- **Same-Candle SL/TP:** SL priority applied. Under same-candle touch, SL is assumed hit first to remain conservative.
- **Cooldown:** 5 candles. Prevents immediate re-entry on consecutive false signals.
- **Leverage:** 3x max. Sizing adjusted dynamically.
