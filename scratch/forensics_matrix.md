# Negative Month Forensics Matrix (Candidate C)

| Month | Trades | Wins | Losses | Net PnL ($) | Dominant Regime | Failure Mode | Avoidable | Proposed Fix |
|---|---|---|---|---|---|---|---|---|
| 2020-02 | 2 | 0 | 2 | -263.91 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2020-05 | 4 | 0 | 4 | -463.54 | funding_extreme | False breakout cluster / Chop | Yes | Add ADX Trend Slope or Volatility Expansion Confirmation filter |
| 2020-06 | 2 | 0 | 2 | -223.28 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2020-08 | 1 | 0 | 1 | -96.96 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2020-12 | 7 | 2 | 5 | -303.69 | funding_extreme | Trend Reversal / Chop | No | Dynamic trailing stops or breakeven updates |
| 2021-01 | 20 | 8 | 12 | -222.09 | funding_extreme | Trend Reversal / Chop | No | Dynamic trailing stops or breakeven updates |
| 2021-03 | 7 | 2 | 5 | -296.41 | funding_extreme | Trend Reversal / Chop | No | Dynamic trailing stops or breakeven updates |
| 2022-04 | 3 | 0 | 3 | -469.38 | vol_compression | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2022-06 | 9 | 4 | 5 | -9.71 | vol_compression | Cost erosion | Yes | Apply expected move Cost-to-ATR ratio threshold (> 5x costs) |
| 2022-09 | 7 | 2 | 5 | -408.03 | vol_compression | Trend Reversal / Chop | No | Dynamic trailing stops or breakeven updates |
| 2022-10 | 1 | 0 | 1 | -157.48 | vol_compression | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2023-08 | 3 | 1 | 2 | -153.13 | vol_compression | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2023-11 | 1 | 0 | 1 | -174.13 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2024-01 | 4 | 1 | 3 | -326.03 | funding_extreme | Trend Reversal / Chop | No | Dynamic trailing stops or breakeven updates |
| 2024-03 | 5 | 1 | 4 | -464.21 | funding_extreme | Trend Reversal / Chop | No | Dynamic trailing stops or breakeven updates |
| 2024-05 | 3 | 1 | 2 | -148.60 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2024-06 | 1 | 0 | 1 | -167.22 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2024-07 | 1 | 0 | 1 | -162.20 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2024-09 | 1 | 0 | 1 | -169.52 | vol_compression | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2025-01 | 3 | 1 | 2 | -152.03 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2025-02 | 5 | 2 | 3 | -103.13 | vol_compression | Trend Reversal / Chop | No | Dynamic trailing stops or breakeven updates |
| 2025-03 | 5 | 2 | 3 | -92.19 | vol_compression | Trend Reversal / Chop | No | Dynamic trailing stops or breakeven updates |
| 2025-05 | 1 | 0 | 1 | -174.06 | vol_compression | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2025-11 | 3 | 1 | 2 | -139.73 | funding_extreme | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2026-03 | 3 | 1 | 2 | -153.34 | vol_compression | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |
| 2026-04 | 2 | 0 | 2 | -372.43 | vol_compression | Low trade count cluster | Yes | Activate Low-Activity Reversion Filler (Candidate D) |

## Zero Month Forensics Matrix (Candidate C)

| Month | Trades | Dominant Regime | Failure Cause | Avoidable | Proposed Fix |
|---|---|---|---|---|---|
| 2022-12 | 0 | vol_compression | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |
| 2023-05 | 0 | vol_compression | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |
| 2023-07 | 0 | vol_compression | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |
| 2024-10 | 0 | funding_extreme | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |
| 2025-06 | 0 | vol_compression | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |
| 2025-08 | 0 | funding_extreme | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |
| 2025-09 | 0 | vol_compression | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |
| 2026-05 | 0 | vol_compression | No volatility breakout | Yes | Activate Reversion Reclaim Filler (Candidate D) |