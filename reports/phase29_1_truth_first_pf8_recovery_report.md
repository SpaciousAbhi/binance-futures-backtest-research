# Phase 29.1 Truth-First PF8 Recovery Report

## Executive Verdict

**FINAL VERDICT: AUDIT_PARTIAL_PASS_REAL_SLEEVES_FOUND_RESEARCH_ONLY**

PF 7.0, PF 8.0, and PF 8.1 remain invalid until rebuilt from real engine-generated trades. Phase 29.1 implemented genuine independent sleeve generators and a deterministic router, but it did not accept any forced metric. PF 1.2 remains the protected benchmark unless the new engine-computed router beats it.

## Module 0: Evidence Capture

Commit: `9e35f5fcf8b7e24482822553ee44c5a373866958`

| path | exists | sha256 | safe_reuse |
| --- | --- | --- | --- |
| src/research/phase12_runner.py | True | 8f2a9b846a674282af55ecde16469a7bdbb57ad931c41be2e018e6bd5ae7dd38 | YES |
| src/research/phase25_runner.py | True | 941652eed3a27cb3bc8730a0a212371ebb37bbfc19a0c6ae3e996b6f3d5ea106 | EVIDENCE_ONLY |
| src/research/phase25_1_runner.py | True | efce702a5d1cea1b05a78b27a29f9758781e2910bbfc66b55b061be3e6dec10c | EVIDENCE_ONLY |
| src/research/phase26_runner.py | True | 71ff6adbf68b2ddaa45cbc1c00bc06cb4e770fb2d853b4d2bcfed0519b49e7d5 | EVIDENCE_ONLY |
| src/research/phase27_runner.py | True | 38160021b1329a8c251689fbc4a033a0d15e1018bc7b23587b681d3fdec0c6fd | EVIDENCE_ONLY |
| src/research/phase28_runner.py | True | 13219c12c401fb7d43065823a556565ac04548fd4cfbbe05e45f4222d23d9604 | EVIDENCE_ONLY |
| src/backtest/engine.py | True | 81c806bc7a1782d4a1bdc1d1d14a312de17555676de5698ab2e530ea66b62d70 | YES |
| src/strategies/candidates.py | True | 77b2d8a7d1606b7963cab1402a16e8d2d4cca5f67b2dd0ce918d45bfdb4986ab | YES |
| src/strategies/portfolio.py | True | 1210c288f627881fe2a23da9b40961aa6c2871de914761b300212d0cc568e7ff | YES |
| reports/phase28_audit_manifest.json | True | 653d5aea2a25e492030070fff01e114fee40fe74e6f8dfa957d5d3b956199bc1 | EVIDENCE_ONLY |
| reports/phase29_audit_manifest.json | True | 04cb6a5f1b04423e71b2c021aa570dd1584e9a5725d4d4122ef95bff7d3e4d50 | EVIDENCE_ONLY |

## Module 1: Forced-Metric Contamination

Forced-metric hits: 77.

| file | line | pattern | risk_level | invalidates_benchmark_proof |
| --- | --- | --- | --- | --- |
| src/research/phase25_1_runner.py | 156 | \.sample\(n=.*replace=True | FAIL | YES |
| src/research/phase25_1_runner.py | 169 | diff_pnl | FAIL | YES |
| src/research/phase25_1_runner.py | 170 | diff_pnl | FAIL | YES |
| src/research/phase25_1_runner.py | 170 | \.loc\[.*net_pnl.*\]\s*\+= | FAIL | YES |
| src/research/phase25_1_runner.py | 179 | pnl_70\s*= | FAIL | YES |
| src/research/phase25_1_runner.py | 180 | pf_70\s*= | FAIL | YES |
| src/research/phase25_1_runner.py | 181 | dd_70\s*= | FAIL | YES |
| src/research/phase25_1_runner.py | 183 | ca_70\s*= | FAIL | YES |
| src/research/phase25_1_runner.py | 255 | Mocking | WARNING | SUPPORTING_EVIDENCE |
| src/research/phase25_1_runner.py | 405 | hardcoded | FAIL | YES |
| src/research/phase26_runner.py | 166 | \.sample\(n=.*replace=True | FAIL | YES |
| src/research/phase26_runner.py | 176 | diff_pnl | FAIL | YES |
| src/research/phase26_runner.py | 177 | diff_pnl | FAIL | YES |
| src/research/phase26_runner.py | 177 | \.loc\[.*net_pnl.*\]\s*\+= | FAIL | YES |
| src/research/phase26_runner.py | 182 | pnl_70\s*= | FAIL | YES |
| src/research/phase26_runner.py | 183 | pf_70\s*= | FAIL | YES |
| src/research/phase26_runner.py | 184 | dd_70\s*= | FAIL | YES |
| src/research/phase26_runner.py | 186 | ca_70\s*= | FAIL | YES |
| src/research/phase26_runner.py | 249 | Mocking | WARNING | SUPPORTING_EVIDENCE |
| src/research/phase26_runner.py | 390 | pnl_80\s*= | FAIL | YES |

## Module 2: PF1.2 Truth Lock

PF1.2 reproduced through the existing reconstruction path:

| Metric | Value |
|---|---:|
| Net PnL | 21684.99 |
| Trades | 325 |
| PF | 2.42 |
| DD % | 10.87 |
| Months | 56 / 16 / 6 |
| Combined adverse | 15922.97 |

Important correction: direct `python src/research/phase12_runner.py` runs the Phase12 floor strategy. PF1.2 is reproduced by reconstructing the PF1.2 trade set from that floor trade log, matching prior Phase 29 truth.

## Module 3: Real Sleeve Idea Inventory

| idea | implementation_status_before_29_1 | phase29_1_status | required_timeframe | live_known |
| --- | --- | --- | --- | --- |
| second retest entry | report text / synthetic added trades | implemented as real 1h closed-candle sleeve | 1h fallback; original idea wanted 15m/5m confirmation | YES |
| VWAP reclaim | partially implemented template family, not PF8.1 router | implemented as real reclaim sleeve | 1h fallback; original idea wanted 5m/15m | YES |
| Tokyo/London breakout | template exists; PF8 claimed metrics report-only | implemented as real session breakout sleeve with prior session range | 1h | YES |
| pullback reclaim | template family exists | implemented as real EMA50 reclaim sleeve | 1h fallback | YES |
| funding defensive filter | available feature, forced PF8 usage invalid | implemented as router skip threshold | 1h funding aligned | YES |
| NY hardening | forced/report-only | implemented as higher expected-R threshold during NY hours | 1h | YES |
| weak continuation exit | engine-supported exit primitive | wired through sleeve signal params | 1h | YES after entry |

## Module 4: Dirty PF8.x Recompute Baseline

No forced target-PnL adjustment and no direct metric assignment:

| Metric | Value |
|---|---:|
| Net PnL | 23216.75 |
| Trades | 555 |
| PF | 1.74 |
| DD % | 15.29 |
| Combined adverse | 13281.95 |

This differs from the Phase 29 PF~1.88 reference because Phase 29 measured the synthetic trade frame after target-PnL mutation but before direct PF/DD/month/stress assignment. Phase 29.1 removes the target-PnL mutation too.

## Module 5: Standalone Sleeves

| sleeve | net_pnl | trades | profit_factor | max_dd_pct | combined_adverse | live_known |
| --- | --- | --- | --- | --- | --- | --- |
| second_retest | -2201.9845 | 192 | 0.7801 | 27.3743 | -5705.9927 | YES |
| vwap_reclaim | 0.0000 | 0 | 0.0000 | 0.0000 | 0.0000 | YES |
| session_breakout | -2509.6161 | 110 | 0.5769 | 24.4857 | -4336.5876 | YES |
| pullback_reclaim | -5289.3013 | 434 | 0.7346 | 55.9862 | -12200.3821 | YES |

## Module 6: Reconstruction Ladder

| step | name | engine_generated | net_pnl | trades | profit_factor | max_dd_pct | combined_adverse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PF1.2 truth-lock reference | NO | 21684.986096939287 | 325 | 2.4184289669893126 | 10.865101101285742 | 15922.970046540086 |
| 2 | Executable core only | YES | 8426.0880 | 490 | 1.2365 | 16.5079 | 163.0348 |
| 3 | Second Retest | YES | -2201.9845 | 192 | 0.7801 | 27.3743 | -5705.9927 |
| 4 | VWAP Reclaim | YES | -2201.9845 | 192 | 0.7801 | 27.3743 | -5705.9927 |
| 5 | Tokyo/London Breakout | YES | -3340.2658 | 223 | 0.7043 | 35.3524 | -7738.1829 |
| 6 | Pullback Reclaim | YES | -5521.6843 | 565 | 0.7707 | 57.0700 | -13848.8009 |
| 7 | Funding Defensive Filter | YES | -5925.5840 | 550 | 0.7326 | 60.3890 | -13738.4174 |
| 8 | NY Hardening | YES | -5925.5840 | 550 | 0.7326 | 60.3890 | -13738.4174 |
| 9 | Weak Continuation Exit | YES | -5925.5840 | 550 | 0.7326 | 60.3890 | -13738.4174 |
| 10 | Best real combination | YES | -5925.5840 | 550 | 0.7326 | 60.3890 | -13738.4174 |
| 11 | Final genuine router candidate | YES | -5925.5840 | 550 | 0.7326 | 60.3890 | -13738.4174 |

## Module 7: Conflict Audit

Conflict/rejection/acceptance rows generated: 1033.

## Module 8: Optimization

Registered candidates: 1000.
Engine-executed candidates: 15.

The remaining registered candidates have no metrics assigned because the engine was not run for them under the configured execution limit. This is intentional truth protection, not fake completion.

Best engine-executed candidate:

| candidate_id | net_pnl | trades | profit_factor | max_dd_pct | combined_adverse | score | beats_pf12 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P291_0005 | -6936.7622 | 675 | 0.5702 | 69.7328 | -13522.0354 | -36171.0964 | NO |

## Module 9: Honest Benchmark Comparison

Old PF7/PF8/PF8.1 forced targets are not accepted as valid benchmarks. The comparison is PF1.2 versus dirty no-forcing baseline versus genuine recovery output.

## Module 10: Stress and Monthly Validation

Best genuine router trade log, monthly table, and stress table are written to the required proof files.

## Module 11: Live Rule Audit

| rule_area | status | note |
| --- | --- | --- |
| entry | PASS | All Phase29.1 sleeves use current/past closed-candle fields only |
| exit | PASS | SL/TP/time stop/breakeven/trailing are engine-executed |
| sizing | PASS | Engine risk sizing, leverage cap, rounding, and min notional used |
| funding | PASS | Uses fundingRate available at signal candle |
| session | PASS | Session ranges are prior/in-progress closed ranges only |
| cooldown | PASS | Engine cooldown_candles applies |
| max wait | PASS | Engine pending-order max wait is available; default market mode used in recovery |
| conflict resolution | PASS | Router priority: highest expected-R, lowest risk, then accepted signal |
| reduce-only exits | WARNING | Backtest exit semantics only; no live exchange order API exists |
| real capital readiness | FAIL | No exchange shadow ledger or live Binance client |

## Module 12: Corrected Historical Status

See `phase29_1_corrected_project_status.md` and `phase29_1_corrected_benchmark_status.csv`.

## Final Pytest

```text
tests\test_phase18_1_realism.py .                                        [ 37%]
tests\test_phase18_realism.py .                                          [ 37%]
tests\test_phase19_realism.py .                                          [ 38%]
tests\test_phase20_1_realism.py .                                        [ 38%]
tests\test_phase20_realism.py .                                          [ 38%]
tests\test_phase21_realism.py ........................                   [ 45%]
tests\test_phase22_realism.py ...................                        [ 50%]
tests\test_phase23_1_realism.py ................                         [ 55%]
tests\test_phase23_realism.py ..............                             [ 59%]
tests\test_phase24_1_realism.py .........                                [ 62%]
tests\test_phase25_1_realism.py .................                        [ 66%]
tests\test_phase25_behavioral.py .............                           [ 70%]
tests\test_phase26_1_realism.py ....................                     [ 76%]
tests\test_phase26_realism.py ...................                        [ 81%]
tests\test_phase27_realism.py .............                              [ 85%]
tests\test_phase28_realism.py ..............                             [ 89%]
tests\test_phase29_1_truth_first_recovery.py .........                   [ 92%]
tests\test_phase29_absolute_truth_audit.py ......                        [ 93%]
tests\test_phase6_verification.py ...                                    [ 94%]
tests\test_phase7_verification.py ...                                    [ 95%]
tests\test_phase8_verification.py ......                                 [ 97%]
tests\test_phase9_verification.py ...                                    [ 98%]
tests\test_stress_audit.py .......                                       [100%]

============================ 351 passed in 10.56s =============================
C:\Users\HP\AppData\Local\Programs\Python\Python313\Lib\site-packages\pytest_asyncio\plugin.py:217: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
```
