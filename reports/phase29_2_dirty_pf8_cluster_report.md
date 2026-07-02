# Phase 29.2 Dirty PF8 Cluster Report

Dirty PF8 is research material, not an accepted benchmark. The audit below is post-trade forensics only; no recovered live router is allowed to remove trades by these labels.

## Source Contribution
| source_sleeve | trades | pnl | stress |
| --- | --- | --- | --- |
| pf12_reconstructed_core | 555 | 23216.75 | 14932.03 |

## Quality Buckets
| trade_quality_bucket | trades | pnl | stress |
| --- | --- | --- | --- |
| acceptable_winner | 212 | 29593.22 | 26930.39 |
| avoidable_loser | 135 | -15770.11 | -17205.60 |
| elite_winner | 106 | 24515.24 | 22310.26 |
| toxic_loser | 91 | -15727.81 | -17638.35 |
| weak_winner | 11 | 606.21 | 535.34 |

## Session Buckets
| session | trades | pnl | stress |
| --- | --- | --- | --- |
| london | 91 | 1856.55 | 538.57 |
| ny | 239 | 12649.82 | 8842.41 |
| off | 66 | 2696.25 | 1648.92 |
| tokyo | 159 | 6014.13 | 3902.13 |

## Main Finding
The extra dirty PF8 rows increase activity and gross PnL potential, but many rows carry shifted timestamps inherited from trade-frame surgery. This makes the dirty frame useful for diagnostics, not as a clean executable router.
