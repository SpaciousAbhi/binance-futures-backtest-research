# Phase 36 - Strategy #1 Decomposition, Repair, and Breakthrough Search Report

## Final Verdict

`PHASE36_PARTIAL_PASS_INTERNAL_EDGE_MAPPED_NO_UPGRADE`

Strategy #1 reproduced exactly from active code/data and remains the protected baseline. Phase 36 mapped the internal edge and found several live-known guard variants that improve individual dimensions such as PF or DD, but none passed the Strategy #1.1 promotion gates. No expansion candidate was promoted.

Live status remains `NOT_REAL_CAPITAL_READY`.

## AI Sync And Workspace State

- Branch: `master`
- Local repository was fetched/pulled before Phase 36 work.
- Safety tag created before edits: `backup_before_phase36_strategy1_repair`
- AI handoff and project memory were updated so Antigravity, Codex, ChatGPT, or another AI can continue from repository files instead of chat history.
- Proof file: `reports/phase36_ai_sync_and_workspace_state.csv`

## Strategy #1 Reproduction Lock

Strategy #1, Combined Router v1, reproduced exactly:

| Metric | Expected | Observed | Status |
|---|---:|---:|---|
| Net PnL | 11205.20 | 11205.20 | PASS |
| Trades | 557 | 557 | PASS |
| Profit Factor | 1.2522 | 1.2522 | PASS |
| Max DD % | 16.2186 | 16.2186 | PASS |
| Winners | 301 | 301 | PASS |
| Losers | 256 | 256 | PASS |
| Positive Months | 52 | 52 | PASS |
| Negative Months | 25 | 25 | PASS |
| Zero Months | 0 | 0 | PASS |

Proof file: `reports/phase36_strategy1_reproduction_lock.csv`

## Where Strategy #1 Makes Money

The edge is concentrated, not evenly distributed.

| Source Sleeve | Trades | Net PnL | Mean PnL |
|---|---:|---:|---:|
| BB Expansion Long | 149 | 4900.85 | 32.89 |
| BB Expansion Short | 159 | 1748.35 | 11.00 |
| ATR Expansion Short | 56 | 1583.78 | 28.28 |
| ATR Expansion Long | 47 | 1196.00 | 25.45 |
| Low-Activity Filler Short | 14 | 935.51 | 66.82 |
| Funding Reversal Short | 110 | 927.92 | 8.44 |
| Funding Reversal Long | 6 | 724.93 | 120.82 |
| Low-Activity Filler Long | 16 | -812.15 | -50.76 |

Session decomposition:

| Session | Trades | Net PnL | Mean PnL |
|---|---:|---:|---:|
| New York | 264 | 9755.21 | 36.95 |
| Off-hours | 203 | 1162.46 | 5.73 |
| London | 90 | 287.53 | 3.19 |

Conclusion: Strategy #1's strongest repeatable edge is BB/ATR expansion, especially New York participation. The weakest explicit component is Low-Activity Filler Long. Off-hours is positive but thin, so full deletion harms trade distribution while stricter gates can reduce drawdown.

Proof files:

- `reports/phase36_strategy1_internal_decomposition.csv`
- `reports/phase36_strategy1_edge_map.md`

## Drawdown And Negative Month Causes

The max drawdown context clusters around July to October 2024, with losses across BB Expansion Short, ATR Expansion, and Low-Activity Filler Long. This is not a single bad trade or a single removable ID. It is a regime/stress issue and must be repaired with live-known features, not month/date filters.

Worst trade-active months included:

- 2026-04: -718.58
- 2025-05: -678.18
- 2025-09: -675.46
- 2024-01: -653.06
- 2024-09: -648.08
- 2024-03: -612.37

No Phase 36 rule targets these dates directly.

## Ablation Results

The most informative executable ablations:

| Ablation | PnL | Trades | PF | DD % | Stress Pass |
|---|---:|---:|---:|---:|---:|
| Projected net-R >= 0.90 | 12883.49 | 524 | 1.2993 | 13.3756 | 8 |
| Remove Low-Activity Filler Long | 11682.54 | 536 | 1.2813 | 14.9634 | 7 |
| Remove all Low-Activity Filler | 11140.65 | 525 | 1.2856 | 13.0041 | 7 |
| London + New York only | 8932.88 | 431 | 1.2953 | 11.0883 | 7 |
| Keep BB + ATR only | 7936.01 | 435 | 1.2775 | 8.2310 | 7 |
| ATR Expansion isolated | 1943.75 | 116 | 1.3110 | 7.8112 | 6 |

Interpretation: some live-known gates improve PF and DD, but stress robustness does not yet improve enough. The projected net-R gate improved PnL over Strategy #1, but missed the PF and stress gates for Strategy #1.1 promotion.

Proof file: `reports/phase36_ablation_results.csv`

## Repair Module Results

Eight bounded repair modules were executed through the engine. Best observations:

| Repair | PnL | Trades | PF | DD % | Negative Months | Stress Pass |
|---|---:|---:|---:|---:|---:|---:|
| Cost-to-risk cap 0.12 | 9739.09 | 454 | 1.3024 | 9.7295 | 27 | 7 |
| Off-hours strict R 1.50 | 9169.42 | 456 | 1.2840 | 9.5132 | 30 | 7 |
| Low-Activity Long suppression | 11682.54 | 536 | 1.2813 | 14.9634 | 27 | 7 |
| BB width filter 0.035 | 9309.63 | 492 | 1.2628 | 10.3328 | 24 | 7 |
| ADX strength 18 | 8715.63 | 521 | 1.2269 | 16.3595 | 23 | 7 |

No repair module reached the required stress pass count or combined adverse improvement target. The useful direction is clear: cost-to-risk and off-hours gates reduce DD sharply, while Low-Activity Filler Long suppression keeps PnL healthy. These need a second-stage combination search with more runtime, not promotion from this phase.

Proof file: `reports/phase36_repair_module_results.csv`

## Strategy #1.1 Search

Four engine-run Strategy #1.1 combinations were tested and each wrote a trade log.

| Candidate | PnL | Trades | PF | DD % | Stress Pass | Promotion |
|---|---:|---:|---:|---:|---:|---|
| low_activity_offhours | 9931.64 | 420 | 1.3421 | 9.2821 | 8 | RESEARCH_ONLY_NOT_PROMOTED |
| projected_R | 10143.55 | 438 | 1.3355 | 13.5266 | 7 | RESEARCH_ONLY_NOT_PROMOTED |
| cost_session | 6316.12 | 343 | 1.3046 | 12.9208 | 7 | RESEARCH_ONLY_NOT_PROMOTED |
| bb_atr_cost | 7474.76 | 412 | 1.2798 | 8.2190 | 7 | RESEARCH_ONLY_NOT_PROMOTED |

Best quality row was `strategy1_1_candidate_low_activity_offhours`, but it did not reach the promotion target because PnL, trade count, and stress pass count were still below required thresholds.

Promoted Strategy #1.1: none.

Proof files:

- `reports/phase36_strategy1_1_candidate_results.csv`
- `reports/phase36_strategy1_1_candidate_low_activity_offhours_trade_log.csv`
- `reports/phase36_strategy1_1_mini_vault.md`

## Candidate Expansion

Phase 36 registered 2,000 candidates based on Strategy #1's proven edge families and engine-executed 20 within runtime. The remaining candidates have blank metrics and are marked unexecuted.

No expansion candidate passed the selection target:

- PnL >= 4000
- trades >= 150
- PF >= 1.35
- DD <= 12
- stress pass >= 9/15

Near observations:

- `P36_CAND_0000` was close to Strategy #1 but not meaningfully improved: PnL 11189.15, 555 trades, PF 1.2538, DD 16.1684, stress 7/15.
- `P36_CAND_0003` had PF 1.3474 and DD 5.1348 but only 112 trades and negative stressed PnL, so it was not selected.

Proof files:

- `reports/phase36_candidate_expansion_registry.csv`
- `reports/phase36_candidate_expansion_results.csv`
- `reports/phase36_candidate_expansion_top_trade_logs_index.csv`

## Integrity Audit

Integrity result: PASS for the Phase 36 path.

- No forced metrics.
- No direct target PnL/PF/DD assignment.
- No trade-log-only repair promoted as a strategy.
- No future labels in live rules.
- No teacher-label routing.
- Metrics are computed from engine trade logs.
- Live status remains `NOT_REAL_CAPITAL_READY`.

Proof file: `reports/phase36_integrity_audit.csv`

## Stress And Monthly Validation

Stress comparison was generated for Strategy #1. Because no Strategy #1.1 or expansion candidate was selected, the stress comparison does not replace the baseline. Strategy #1 remains stress-fragile at 7/15 pass.

Proof files:

- `reports/phase36_stress_comparison.csv`
- `reports/phase36_monthly_comparison.csv`

## Answers To Phase 36 Questions

1. Was Strategy #1 reproduced?
   Yes. It reproduced exactly on PnL, trades, PF, DD, winners/losers, and month counts.

2. Where does Strategy #1 make money?
   Mostly BB Expansion Long, ATR Expansion, and New York session exposure.

3. Which sleeves are strongest?
   BB Expansion Long is the largest absolute contributor. ATR Expansion sleeves are smaller but cleaner. Funding Reversal Long is high mean PnL but only 6 trades.

4. Which sleeves are weakest?
   Low-Activity Filler Long is the clearest weak sleeve, with -812.15 across 16 trades.

5. What causes DD and negative months?
   Regime clusters across 2024 and selected 2025/2026 months, not one hard-removable trade ID. DD includes BB, ATR, and Low-Activity losses.

6. Which ablations worked?
   Projected net-R >= 0.90 improved PnL and PF but not enough stress. Removing Low-Activity Filler Long improved PnL but did not fix stress.

7. Which repair modules worked?
   Cost-to-risk and off-hours strict gates improved DD materially. Low-Activity Long suppression improved PnL. None met full promotion gates.

8. Was Strategy #1.1 created?
   No. All Strategy #1.1 candidates remain research-only.

9. Did Strategy #1.1 beat Strategy #1?
   No promoted Strategy #1.1 exists. Some candidates beat Strategy #1 on DD/PF, but not on the full promotion gate.

10. Were new candidates found?
   No selected expansion candidates. Twenty were engine-executed; 1,980 remain registered but unexecuted due to runtime.

11. Are all results free from lookahead/hardcoding?
   The Phase 36 active path audit says yes for generated repairs and candidates.

12. What is the exact next phase direction?
   Phase 37 should run a larger combination search around three live-known levers: projected net-R gate, Low-Activity Filler Long suppression, and cost/off-hours hardening. It should also target combined adverse stress directly.

13. Is GitHub/project memory fully updated for AI switching?
   Project memory files were updated. GitHub sync should be completed by committing and pushing the Phase 36 artifacts after validation passes.

## Final Status

Strategy #1 remains:

- `VALID_EXECUTABLE_BASELINE`
- `BACKTEST_VERIFIED_NOT_SHADOWED`
- `NOT_REAL_CAPITAL_READY`

No benchmark replacement occurred in Phase 36.
