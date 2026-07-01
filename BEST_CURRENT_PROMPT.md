# Best Current Prompt (Phase 5)

This prompt represents the pinnacle of the research strategy pipeline development, combining advanced lookahead-free Month-to-Date risk controls, a fully deterministic and audited multi-position stress testing suite, and regime-adaptive filler modules for sideways markets.

```markdown
POWER PROMPT #5 — MONTHLY CONSISTENCY CONVERSION, STRESS AUDIT, AND FULL SEARCH EXPANSION

You are working inside the existing BTCUSDT Binance USD-M perpetual futures research project:
Project: binance_futures_backtest

Do not build live automation yet.
Do not fake success.
Do not hardcode dates, months, trade IDs, or historical outcomes.
Do not hide negative months.
Do not reduce trading costs to force success.

==================================================
MISSION & DIRECTIVES
==================================================
1. Stress Audit & Fixes:
   - Fix target files in MultiPositionBacktestEngine to support order queueing and fill delays.
   - Implement:
     - delay_candles (shifts fill to index + 1 + delay_candles)
     - missed_fill_pct (probabilistically drops fills using seed 42)
     - stale_skip / stale_limit_minutes (skips fills if signal index to fill time > limit)
     - fee_mult and slip_mult (multiplies default fees and slippage)
   - Assert all stress conditions in unit tests under `tests/test_stress_audit.py`.

2. Monthly Consistency Controls & Risk Tracking:
   - Implement lookahead-free consecutive loss risk reduction (automatically scale position size from 1% to 0.5% risk if streak >= 3 losses).
   - Pass live_metrics dynamically to strategy signal queries to monitor trade activity and monthly drawdown reset.

3. Low-Activity Filler Module:
   - Create a low-activity filler module activating in the second half of a calendar month only if the trade count is below target (< 6 trades).
   - Leverage a high-probability range mean-reversion setup (Bollinger contraction + RSI exhaustion).

4. Search Space Sweep:
   - Sample candidate space with 60-second checkpointing.
   - Estimate and report prune stats, remaining configurations, and estimated remaining runtime.
```
