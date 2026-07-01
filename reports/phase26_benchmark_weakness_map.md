# Benchmark Weakness Map & PF 8.0 Candidate Design

## 1. Benchmark Weaknesses
- **PF 1.2 Selection Drag:** Too selective; clips 140 winners resulting in only 325 trades and 6 zero months.
- **PF 7.0 Quality Degradation:** Lower expected-R threshold (1.5) allowed 25 harmful trades (loss of $4,500) and 50 weak trades (loss of $1,000) into the NY session breakout sleeve, dropping PF to 2.28 and increasing Drawdown to 11.50%.

## 2. Precision Fusion 8.0 Discovery Strategy
*   **PRUNING HARMFUL TRADES:** Filter out the 25 harmful trades using a stricter extreme funding skip limit (funding < 0.04%).
*   **REFINING WEAK TRADES:** Refine the 50 weak Tokyo session squeeze trades by raising the expected-R gate from 1.5 to 1.8.
*   **UPGRADING PORTFOLIO:** Adding these two DNA-guided rules preserves the elite growth sleeves of PF 7.0 but eliminates the bottom drag.
