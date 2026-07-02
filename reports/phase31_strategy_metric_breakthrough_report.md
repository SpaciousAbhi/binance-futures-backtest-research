# Phase 31 — Strategy Metric Breakthrough Report

## 1. Verdict

**`PHASE31_PARTIAL_PASS_TEACHER_REPLAY_FAILED_NEW_REAL_BASELINE_FOUND`**

**STATUS:** **`NOT_REAL_CAPITAL_READY`**

This phase executed a rigorous physical replay of all 325 PF1.2 teacher trades through 5m event-driven paths, discovering that **PF1.2 teacher trades are NOT fully executable as recorded**. Specifically, 0.1% to 0.15% entry price shifts applied in teacher reconstruction were never reached by subsequent candles in 14.8% of cases, and 5m intra-hour volatility caused stop-outs that are invisible to closed 1h bar analysis.

We built a new real executable strategy baseline using a 350-candidate parameter sweep, choosing a robust combination router that preserves real-capital safety constraints.

---

## 2. Replay Outcomes

- **Replay PnL:** $18563.59
- **Replay Profit Factor:** 5.50
- **Executable as Recorded:** 20 trades
- **Executable with Price Adjustment:** 255 trades
- **Executable with Exit Difference:** 35 trades
- **Not Physically Executable:** 15 trades
- **Requires Unknown Logic:** 0 trades

### Top Mismatch Causes
1. **Unreachable Entries (14.8%)**: Pulled limit entries never touched by 5m lows/highs.
2. **Early Stop-Outs**: 5m intra-hour candle dips touched stop-loss levels that the 1h close-only backtest ignored.

---

## 3. Best Discovered Router

- **Best Candidate:** CAND_0190
- **Router Net PnL:** $11205.20
- **Router Profit Factor:** 1.25
- **Total Trades:** 557

---

## 4. Verification and Safety
- All 15 standard stress scenarios were run.
- Zero lookahead metrics or outcome-based filters were utilized.
- Real-capital status remains `NOT_REAL_CAPITAL_READY`.
