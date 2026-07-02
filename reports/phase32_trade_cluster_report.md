# Phase 32 — Trade Quality Forensics Report

## Trade Classifications

| Class | Count |
|---|---|
| ACCEPTABLE_WINNER | 205 |
| AMBIGUOUS_EXECUTION | 46 |
| NORMAL_LOSER | 149 |
| TOXIC_LOSER | 91 |
| WEAK_WINNER | 66 |

## Session Analysis

| Session | Total PnL | Trade Count |
|---|---|---|
| LONDON | $5,770.87 | 188 |
| NEW_YORK | $4,271.87 | 166 |
| OFF_HOURS | $1,162.46 | 203 |

## Exit Reason Analysis

| Exit Reason | Total PnL | Trade Count |
|---|---|---|
| SAME_CANDLE | $2,949.74 | 46 |
| SL_HIT | $-41,555.23 | 240 |
| TP_HIT | $49,810.69 | 271 |

## R-Multiple Distribution

- Trades with R < 1.0: 116 (20.8%)
- Trades with R >= 1.5: 29 (5.2%)
- AMBIGUOUS_EXECUTION (same-candle): 46

## Key Weaknesses Identified

1. **OFF_HOURS session**: $1162.46 PnL — noisy, filter candidate
2. **Low R-multiple trades**: 116 trades with R < 1.0 — primary DD driver
3. **AVOIDABLE_LOSER trades**: 0 — rule-based fixes possible
4. **Same-candle ambiguity**: 46 trades

NOT_REAL_CAPITAL_READY
