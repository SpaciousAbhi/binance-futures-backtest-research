# Phase 29.6 Event-Driven MTF Engine Design

PF means Precision Fusion: deterministic routing over candidate sleeves, filters, and risk rules.

Flow:
1. A 1h setup strategy is evaluated only after the 1h candle is closed.
2. A 5m trigger window starts at the 1h setup close timestamp.
3. Trigger candles must be closed 5m candles at or after setup close.
4. Entry is filled at the next 5m open, or at a conservative retest limit fill when configured.
5. SL, TP, breakeven, trailing, funding, fees, slippage, and time-stop are simulated on 5m bars.
6. If SL and TP touch inside the same 5m candle, same-candle priority is SL_FIRST.
7. Router conflict order is highest expected R, then lower risk, then saved sleeve priority, then earlier fill.

This is a backtest and shadow-readiness artifact only. It is NOT_REAL_CAPITAL_READY.
