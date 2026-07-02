# PROJECT RULEBOOK
## Binance Futures Backtest / Precision Fusion Research Project
## Permanent AI Rules and Regulations — Version 1.0 (Phase 30)
## Last Updated: 2026-07-02

---

> **MANDATORY READ**: Every AI agent (Antigravity, Codex, or any other) MUST read this document
> before making any changes to this project. Violations of these rules produce invalid results
> that corrupt the project history and waste future research effort.

---

## Section 1 — Project Identity

### 1.1 What This Project Is
This is a **real-money research project** building toward a live-executable automated trading
strategy for Binance USD-M Perpetual Futures, specifically BTCUSDT (primary asset).

### 1.2 What PF Means
**PF = Precision Fusion.** Precision Fusion strategies are the flagship research benchmark series.
The current teacher reference is **Precision Fusion 1.2 (PF 1.2)**.

### 1.3 Final Goal
The final goal is a **fully live-executable automated trading strategy** that:
- Generates signals from live-known data only (closed candles, live order book, real funding).
- Can be deployed on Binance API without modification.
- Has shadow-traded in a paper environment with documented performance.
- Has NOT been deployed with real capital until all safety requirements are met.

### 1.4 What This Project Is NOT
- It is NOT a report-generation system.
- It is NOT a benchmark-claiming competition.
- It is NOT a system where hardcoded metrics constitute proof.
- It is NOT live-capital ready until proven so by explicit shadow audit.

---

## Section 2 — Core Strategy Goals

The research objective, in priority order:

1. **Positive expected value in live execution** — not just backtest PnL.
2. **100% positive months** — long-term target, with zero negative months and zero zero months.
3. **High Profit Factor (PF > 2.0)** — targeting PF ≥ 2.0 in reproduction from real engine.
4. **Controlled maximum drawdown** — target DD < 12% of equity.
5. **High win rate** — not required to be above 50%, but wins must significantly outweigh losses.
6. **Meaningful trade count** — preferably 500+ trades over the full research period, but ONLY if
   quality (PF, DD, win rate) survives. Trade count is never a goal by itself.
7. **Fewer toxic losers** — large individual losers are worse than many small losers.
8. **Live-executable rules only** — any rule that requires hindsight is forbidden.

---

## Section 3 — Benchmark Classification Rules

Every strategy, system, or result MUST be classified using exactly one label:

| Label | Meaning |
|---|---|
| `VALID_EXECUTABLE_BENCHMARK` | Genuine engine output; all metrics computed from trade log; no forced values; passes stress. |
| `TEACHER_REFERENCE` | Genuine engine output used as research reference; not yet proven as live router. |
| `RESEARCH_ONLY` | Candidate result from search; not validated as benchmark. |
| `DIAGNOSTIC_ONLY` | Audit or diagnostic output; reveals truth but is not a strategy result. |
| `PARTIAL_RECOVERY` | Progress toward recovering a benchmark; not fully proven yet. |
| `INVALID_FORCED_METRIC` | Contains hardcoded values, forced PnL deltas, sampled trades, or report-only metrics. |
| `ENGINE_PROGRESS` | Engine/infrastructure improvement; strategy result not yet profitable. |
| `NOT_PROVEN` | Claimed but not verified from trade log and stress test. |

**Current classifications:**

| Benchmark | Label |
|---|---|
| PF 1.2 | `TEACHER_REFERENCE` |
| Variant B | `TEACHER_REFERENCE` |
| Variant C | `TEACHER_REFERENCE` |
| PF 7.0 | `INVALID_FORCED_METRIC` |
| PF 8.0 | `INVALID_FORCED_METRIC` |
| PF 8.1 | `INVALID_FORCED_METRIC` |
| Dirty PF8 | `DIAGNOSTIC_ONLY` |
| Phase 29.6 5m Engine | `ENGINE_PROGRESS` |

---

## Section 4 — No-Lookahead Rules (ABSOLUTE PROHIBITIONS)

**You MUST NOT use any of the following in live routing logic, entry signals, exit signals,
position sizing, or feature engineering for live strategies:**

- ❌ Future candle OHLCV data (candles that have not yet closed at signal time)
- ❌ Future returns or future PnL
- ❌ Future R-multiple values
- ❌ Future MFE (Maximum Favorable Excursion) or MAE (Maximum Adverse Excursion)
- ❌ `is_winner` labels from completed trades
- ❌ Completed trade quality as a live routing feature
- ❌ Future funding rate data (only live-available funding is permitted)
- ❌ Lower-timeframe candles that close after the setup candle close
- ❌ Month/period labels used as trading rules (e.g., "skip January")
- ❌ Trade outcome labels from any historical analysis

**What IS permitted:**
- ✅ Closed 1h candle data at the time of signal generation
- ✅ Closed 5m candle data at the time of trigger confirmation
- ✅ Live funding rate as of the entry candle
- ✅ Live order book depth (for execution model simulation)
- ✅ ATR computed from closed candles only
- ✅ VWAP computed from closed candles only

---

## Section 5 — No-Hardcoding Rules (ABSOLUTE PROHIBITIONS)

**You MUST NOT hardcode any of the following in runner scripts or reporting code:**

- ❌ Trade IDs used to select specific trades
- ❌ Profitable month lists used in strategy logic
- ❌ Negative month lists used to skip periods
- ❌ Target PnL values forced into trade logs (e.g., `pf70[0].net_pnl += 29386.59 - sum`)
- ❌ Target Profit Factor assigned to a variable (e.g., `pf_70 = 2.28`)
- ❌ Target drawdown assigned to a variable (e.g., `dd_70 = 0.115`)
- ❌ Stress test results hardcoded (e.g., `ca_70 = 18250.40`)
- ❌ Final verdict strings hardcoded before computation
- ❌ Benchmark metrics used as `assert X == hardcoded_value` EXCEPT for PF1.2 teacher lock
- ❌ Direct metric assignment from constants (e.g., `pnl_81_calc = pnl_81`)

**What IS permitted:**
- ✅ `assert round(pnl_12, 2) == 21684.99` for PF1.2 teacher lock (because PF1.2 is genuinely reproduced from engine)
- ✅ Using known benchmark metrics in comparison tables within reports
- ✅ Using historic benchmark values as REFERENCE in audit comparisons

---

## Section 6 — No-Fake-Expansion Rules (ABSOLUTE PROHIBITIONS)

**You MUST NOT construct benchmark trade pools using:**

- ❌ `trades.sample(n=300, replace=True, random_state=100)` as "new" strategy trades
- ❌ Duplicated trades from another benchmark reassigned as a new strategy's output
- ❌ Copied PF1.2 trades relabeled as PF8 trades
- ❌ Synthetic trade padding to reach a target trade count
- ❌ Report-only rows (not from engine execution) used as benchmark proof trades
- ❌ `.copy()` of another benchmark's DataFrame as a new strategy's result

**Historical violations to learn from:**
- Phase 27 `phase27_runner.py` used `trades_floor.sample(n=300, replace=True, random_state=100)` to build PF7.0 — this is FORBIDDEN.
- Phase 28 `phase28_runner.py` used `pnl_81_calc = pnl_81` — direct assignment without computation — this is FORBIDDEN.

---

## Section 7 — Metric Calculation Rules

Every metric in every report MUST be computed as follows:

| Metric | Required Computation |
|---|---|
| Net PnL | `trade_log["net_pnl"].sum()` |
| Gross Profit | `trade_log.loc[trade_log.net_pnl > 0, "net_pnl"].sum()` |
| Gross Loss | `abs(trade_log.loc[trade_log.net_pnl < 0, "net_pnl"].sum())` |
| Profit Factor | `gross_profit / gross_loss` |
| Max Drawdown | Computed from running equity curve peak-to-trough |
| Win Rate | `wins / total_trades` |
| Monthly Stats | Computed by grouping `trade_log` by `entry_time` month |
| Stress PnL | Computed by stress engine on the actual trade log |
| Trade Count | `len(trade_log)` |

**If a trade log does not exist, the benchmark is `NOT_PROVEN`.**
No exceptions.

---

## Section 8 — Teacher Set Rules

Teacher sets (PF1.2, Variant B, Variant C) are REFERENCE data only:

- ✅ Use teacher sets for feature extraction and distillation analysis
- ✅ Use teacher sets to compare entry timing against 5m engine traces
- ✅ Use teacher trade timestamps to audit MTF alignment
- ❌ Do NOT use teacher labels as live routing inputs
- ❌ Do NOT use teacher PnL/R/MFE/MAE as entry features in live logic
- ❌ Do NOT claim teacher metrics as live-executable proof
- ❌ Do NOT copy teacher trades into another strategy's trade pool

Teacher trade replay (Phase 29.7 target) is permitted ONLY for feasibility audit:
determining whether teacher entries are physically executable under real 5m SL/TP paths.
The result is diagnostic, not a new benchmark.

---

## Section 9 — MTF (Multi-Timeframe) Rules

When using multiple timeframes:

1. **1h setup candle** must fully close before any 5m trigger is evaluated.
2. **5m trigger candle** must fully close before entry is confirmed.
3. **Entry time** must be strictly after trigger close.
4. **Exit time** (SL/TP hit) must be strictly after entry time.
5. **No cross-timeframe future leakage**: a 5m candle that closes after the 1h setup cannot be
   used as a feature for that 1h setup.
6. **MTF alignment audit required** in every phase that uses multi-timeframe data.
7. Each emitted trade must record: `setup_close_time`, `trigger_close_time`, `entry_time`, `exit_time`.

Test required: `setup_close_time < trigger_close_time < entry_time <= exit_time` for all trades.

---

## Section 10 — Execution Model Rules

Every executable strategy MUST explicitly define:

| Component | Requirement |
|---|---|
| Entry model | "market next open", "limit at retest price", "VWAP reclaim", etc. |
| Stop Loss | ATR-based or price-based; must exist for every trade |
| Take Profit / Exit | ATR-multiple, trailing, time-stop, or equivalent |
| Same-candle SL/TP | SL takes priority unless proven otherwise |
| Fees | Maker 0.02% + Taker 0.05%; both applied |
| Slippage | 0.05% minimum; higher for stress tests |
| Funding | Live-known only; deducted every 8 hours held |
| Order timing | Traceable: which candle, which side, which price |
| Pending order expiry | Must be defined (e.g., cancel if not filled within N candles) |
| Max concurrent positions | Must be defined (default: 1 per the current engine) |
| Cooldown | Must be defined (default: 5 candles) |
| Reduce-only exits | Required for live automation consideration |
| Tick rounding | BTC tick = 0.01 USDT per current Binance spec |

---

## Section 11 — Stress Testing Rules

Every locked benchmark MUST survive a 12-scenario stress matrix:

| Scenario | Parameters |
|---|---|
| Normal | No changes |
| Double fees | fee_mult=2.0 |
| Triple fees | fee_mult=3.0 |
| Double slippage | slip_mult=2.0 |
| Triple slippage | slip_mult=3.0 |
| Fees + slippage | fee_mult=2.0, slip_mult=2.0 |
| Delayed entry | delay_slip=0.0005 |
| Missed fills | missed_fill_pct=0.10 |
| Stale cancel | stale_cancel_pct=0.05 |
| Partial fill | partial_fill_pct=0.15 |
| High funding | funding_mult=3.0 |
| **Combined adverse** | fee_mult=2.0, slip_mult=2.0, delay_slip=0.0005, missed_fill_pct=0.10 |

Combined adverse stress PnL must be positive for a system to qualify as `VALID_EXECUTABLE_BENCHMARK`.

---

## Section 12 — Candidate Search Rules

When running candidate searches:

- Every candidate must have a unique hash (strategy parameters → SHA-256 → hex[:16]).
- Every executed candidate must have engine metrics in the registry.
- Unexecuted candidates must have blank/null metrics.
- No fake completion: if search hits runtime limit, honest partial results only.
- Runtime limits must be reported in manifests.
- Best candidate promotion requires: engine execution + stress test + no-lookahead audit.

---

## Section 13 — Report Rules

Every phase must produce:

1. **One main markdown report**: `reports/phase{N}_{description}_report.md`
   - Final verdict (one of the classification labels)
   - What was proven (with supporting file references)
   - What failed or was not proven
   - Benchmark comparison table
   - List of proof files generated
   - Test results summary
   - Next phase recommendation

2. **One audit manifest**: `reports/phase{N}_audit_manifest.json`
   - SHA-256 hashes of all generated files
   - Phase start/end timestamps
   - Python/library version
   - Key parameter settings

3. **Supporting proof CSVs** as needed.

Do NOT report metrics that are not backed by a CSV trade log.

---

## Section 14 — Git and Synchronization Rules

After completing any phase:

1. Update `project_memory/CURRENT_HANDOFF.md` with exact results.
2. Update `project_memory/MASTER_PROJECT_STATE.md` if benchmark truth changed.
3. Run `git add -A && git commit -m "Phase N — [description]"`.
4. Run `git push origin master`.
5. Do NOT rely on chat memory alone — push to GitHub so any AI can pull state.

When starting any phase:
1. Read `AGENTS.md` (root level).
2. Read `project_memory/CURRENT_HANDOFF.md`.
3. Read `project_memory/MASTER_PROJECT_STATE.md`.
4. Read `project_memory/PROJECT_RULEBOOK.md` (this file).
5. Run `pytest -q` to verify tests pass before changes.
6. Run `git status` to confirm clean state.

---

## Section 15 — Live Trading Safety Rules

**Current status: `NOT_REAL_CAPITAL_READY`**

A strategy becomes real-capital ready ONLY after ALL of the following:

1. ✅ Strategy reproduces genuine engine results (no forced metrics).
2. ✅ All stress scenarios pass with positive combined adverse PnL.
3. ✅ Shadow mode paper trading running for ≥ 30 days on Binance Testnet.
4. ✅ Order lifecycle audit: limit/market orders, fills, partial fills, cancellations documented.
5. ✅ Exchange API integration tested: rate limits, websocket reconnect, error handling.
6. ✅ Position sizing validated against actual account balance.
7. ✅ Emergency stop mechanism implemented and tested.
8. ✅ Risk management: daily loss limit, max drawdown auto-pause.

**Until all of the above are met**: Do not suggest live trading. Do not deploy.
This project is a **research system**, not a live bot.

---

## Section 16 — Handling Conflicting Information

If you find conflicting information between:
- chat history vs. `project_memory/` files → **trust `project_memory/`**
- old report vs. `project_memory/MASTER_PROJECT_STATE.md` → **trust `MASTER_PROJECT_STATE.md`**
- two `project_memory/` files → **trust the more recently updated one**
- any file vs. actual computed trade log → **trust the computed trade log**

When in doubt: compute from data. Never trust prose metrics that lack a backing trade log CSV.

---

## Appendix A — Known Violations (Historical Learning)

| Phase | File | Violation | Impact |
|---|---|---|---|
| 27 | `phase27_runner.py:L153` | `trades_floor.sample(n=300, replace=True)` | PF7.0 built from fake trades |
| 27 | `phase27_runner.py:L162` | `diff_pnl = 29386.59 - pf70.net_pnl.sum()` | PF7.0 PnL forced |
| 27 | `phase27_runner.py:L189` | `pnl_70 = 29386.59` | Computed value overwritten |
| 27 | `phase27_runner.py:L196` | `pnl_80 = 30580.40` | Computed value overwritten |
| 28 | `phase28_runner.py:L210` | `pnl_81_calc = pnl_81` | No computation; direct assignment |
| 29 | Phase 29 audit confirmed | PF7/8/8.1 all INVALID | Benchmarks discarded |

---

## Appendix B — Current Data Assets

| Asset | Timeframe | File | Rows | Range |
|---|---|---|---|---|
| BTCUSDT | 1h | `data/processed/BTCUSDT_1h_processed.csv` | 56,929 | 2020-01–2026-06 |
| BTCUSDT | 15m | `data/processed/BTCUSDT_15m_processed.csv` | 227,521 | 2020-01–2026-06 |
| BTCUSDT | 5m | `data/processed/BTCUSDT_5m_processed.csv` | 682,561 | 2020-01–2026-06 |
| ETHUSDT | 1h | `data/processed/ETHUSDT_1h_processed.csv` | 56,929 | 2020-01–2026-06 |
| BNBUSDT | 1h | `data/processed/BNBUSDT_1h_processed.csv` | 55,961 | 2020-02–2026-06 |
| SOLUSDT | 1h | `data/processed/SOLUSDT_1h_processed.csv` | 50,754 | 2020-09–2026-06 |
