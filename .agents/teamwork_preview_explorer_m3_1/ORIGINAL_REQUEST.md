## 2026-06-30T04:57:11Z
You are teamwork_preview_explorer.
Your coordination directory is C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\.agents\teamwork_preview_explorer_m3_1.
Your task is to analyze the codebase and design the MTF (Multi-Timeframe) alignment and execution strategy for Phase 8.

Specifically, analyze:
1. How to align 1h and 15m candle data with 5m candles lookahead-free. Specify the exact Pandas merge keys and directions (e.g. merge_asof backward on close times).
2. How the UniversalStrategyTemplate and backtesting engine should be modified or extended to support MTF setups and triggers (1h regimes, 15m setups, 5m precision entries).
3. How to design delayed confirmation rules, breakout retests, failed breakout reversals, and tighter 5m stops.
4. How to integrate dynamic exits and risk scaling (ATR/swing SL/TP, loss-streak throttles).
5. How to design the bad-month conversion and zero-month rescue modules lookahead-free.

Write your report to C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest\.agents\teamwork_preview_explorer_m3_1\handoff.md and report completion to the orchestrator (conversation ID: 018d8f91-6e1d-4f25-b39d-d45240058a42).
Do NOT write any code files; propose designs only.
