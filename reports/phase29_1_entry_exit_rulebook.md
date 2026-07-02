# Phase 29.1 Entry/Exit Rulebook

## Router Priority

1. Core PF 1.2 remains the protected reconstructed benchmark, but is not used as a live sleeve.
2. Genuine recovery router evaluates independent sleeves from candle data.
3. Conflicts are resolved by highest expected-R.
4. If expected-R ties, the lower stop distance wins.
5. Long/short conflicts are never both accepted.

## Sleeves

| Sleeve | Entry | Exit |
|---|---|---|
| Second Retest | Prior BB breakout, retest of BB mid, close reclaim, volume guard | ATR SL/TP, optional time/BE/trailing |
| VWAP Reclaim | Prior deviation from VWAP, closed-candle reclaim, wick and volume guard | Structural wick stop and ATR target |
| Session Breakout | Prior Tokyo/London range, breakout plus retest, body filter | Range/ATR stop and ATR target |
| Pullback Reclaim | EMA50 pullback in EMA200 trend, ADX guard | ATR stop and target |
| Funding Defensive Filter | Router skips signals over configured funding threshold | No future funding used |
| NY Hardening | Higher expected-R threshold during NY hours for breakouts | Same engine exits |
| Weak Continuation Exit | Optional engine failed-continuation fields after entry | Post-entry closed-candle only |

All rules are deterministic and live-known, but this is still not real-capital ready because no exchange-level shadow executor exists.
