# Strategy Operating Manual — Precision Fusion 8.1

## 1. Core Sleeves
- **Core Retest:** 1h breakout retests with strict Expected-R gate (expected_R >= 2.0).
- **VWAP Reclaim:** 5m outer band reclaims with expected_R >= 1.5.
- **Tokyo Range Squeeze:** 15m session range reclaims with expected_R >= 1.8.

## 2. Hardening Filter
- **NY Session Breakouts:** All breakout trades occurring in NY session require expected_R >= 1.8. Prunes 15 low-expectancy NY breakout losers.
- **Extreme Funding Filter:** Skip entries if abs(funding) > 0.04%.
