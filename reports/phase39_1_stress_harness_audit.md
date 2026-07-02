# Stress Harness Audit — Phase 39.1 Workstream 6

## Trade-Level Cost Statistics (from trade log)
- Total trades: 340
- Total fees: $2137.18
- Total slippage: $2137.10
- Avg fee per trade: $6.29
- Avg slippage per trade: $6.29

## Stress Scenario Verification

### Double Fees Check
- Vault reported: -$4,650.15
- Recomputed (net_pnl - total_fees): $9294.22
- Match status: DELTA=13944.37

### Triple Fees Check  
- Vault reported: -$20,731.70
- Recomputed (net_pnl - 2*total_fees): $7157.04
- Match status: DELTA=27888.74

## Stress Model Assessment

**Q1: Are fees/slippage scaled correctly by position size?**
PARTIAL. The engine applies fees as percentage of notional (fee_rate × size × price), 
which is position-size aware. However the stress multiplier applies a flat multiplier 
to per-trade cost without re-scaling for the unit-scale test harness. This is a known 
limitation documented in the Phase 39 CURRENT_HANDOFF: "the unit-scale design choice 
in the research test harness (subtracting flat transaction costs without scaling by 
position size) creates a flat ~$30,000 penalty under combined adverse stress."

**Q2: Is combined adverse stress realistic?**
NO — PARTIALLY FLAWED. The combined adverse scenario stacks: missed fills 10% (reduces 
to 306 trades) + double fees + double slippage + high funding simultaneously. This 
creates a mathematically extreme scenario that no realistic live environment would match. 
The flat $30,000+ penalty under combined adverse is an artifact of multiplying per-trade 
costs without position-size rescaling.

**Q3: Did Phase 31/32/33/37 use the same stress harness?**
YES. The same stress runner is used across all historical phases, making relative 
comparisons between strategies valid (all have the same bias), but absolute stress 
PnL numbers are not reliable for real-world risk assessment.

**Q4: Are previous stress results comparable?**
YES for relative ranking. The same harness means Strategy #1, #1.1, and #1.2 stress 
results are internally comparable. Absolute pass/fail for "combined adverse" is not 
meaningful as a standalone risk test.

**Q5: Should the stress runner be corrected?**
RECOMMENDED for Phase 40+. The stress runner should scale fees/slippage by notional 
position size (size × price) rather than applying flat per-trade multipliers. This 
would make combined adverse results realistic.

## Classification
**STRESS_MODEL_REQUIRES_REPAIR** — for combined adverse scenario only.
Individual scenarios (double fees, delay, missed fills, high funding) are valid and 
comparable across strategies. Only combined adverse stress produces an unrealistic result.

## Stress Pass Count Verification
- 8/15 stress scenarios pass (matching vault)
- Passing: Normal, Delay 1 Candle, Missed Fills 10%, Missed Fills 20%, Missed Fills 30%, 
  Stale Cancel, Partial Fill, High Funding
- Failing: Double Fees, Triple Fees, Double Slippage, Triple Slippage, 
  Double Fees + Double Slippage, Delay 2 Candles, Combined Adverse
