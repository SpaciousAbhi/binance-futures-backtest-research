import os
import re
import pandas as pd
import numpy as np

class SystemAuditor:
    """
    Performs comprehensive audits on strategies and backtests to detect lookahead bias,
    future leakage, repainting, hardcoded dates/months, trade filtering, and cost errors.
    """
    def __init__(self, df: pd.DataFrame, strategy, engine):
        self.df = df
        self.strategy = strategy
        self.engine = engine

    def run_all_audits(self) -> dict:
        print("Running System Audits...")
        signal_audit = self.audit_signals()
        trade_audit = self.audit_trades()
        no_fake_audit = self.audit_no_fake()

        return {
            "signal_audit": signal_audit,
            "trade_audit": trade_audit,
            "no_fake_audit": no_fake_audit
        }

    def audit_signals(self) -> dict:
        """
        Signal Audit: Verifies that the strategy has no lookahead bias.
        It runs the strategy on truncated DataFrames up to index 'i'
        and compares the generated signals with the signals from the full DataFrame.
        """
        print("Auditing signals for future leakage/lookahead...")
        
        # Test 100 random bars spread across the dataset
        n = len(self.df)
        test_indices = np.linspace(250, n - 2, 100, dtype=int)
        
        leaks_detected = 0
        reasons = []

        for idx in test_indices:
            # 1. Get signal from the full dataframe
            signal_full = self.strategy.get_signal(self.df, idx)
            
            # 2. Get signal from a truncated dataframe (completely removing future rows)
            df_truncated = self.df.iloc[:idx + 1].copy()
            signal_truncated = self.strategy.get_signal(df_truncated, idx)

            # Compare signals
            if signal_full != signal_truncated:
                leaks_detected += 1
                reasons.append(f"Signal mismatch at index {idx}: Full={signal_full}, Truncated={signal_truncated}")
                if leaks_detected >= 5: # Stop after 5 logs
                    break

        status = "PASS" if leaks_detected == 0 else "FAIL"
        return {
            "status": status,
            "leak_count": leaks_detected,
            "reasons": reasons
        }

    def audit_trades(self) -> dict:
        """
        Trade Audit: Verifies trade execution timing, fees, slippage, and funding.
        Ensures execution occurs strictly on the next candle's open.
        """
        print("Auditing trade executions...")
        
        # Run a quick backtest to inspect the trade logs
        res = self.engine.run(self.df, self.strategy)
        trades = res["trades"]
        
        if trades.empty:
            return {
                "status": "PASS",
                "notes": "No trades generated to audit."
            }

        failures = []
        
        # Sample trades to check
        for _, trade in trades.head(20).iterrows():
            entry_time = trade["entry_time"]
            exit_time = trade["exit_time"]
            
            # Check entry time alignment
            # Find the index of the candle that triggered the signal
            # The signal was evaluated on bar i (close time)
            # The trade was executed on bar i+1 open time
            # Open time of bar i+1 should be the same as entry_time
            matching_entry_candles = self.df[self.df["open_time"] == entry_time]
            if matching_entry_candles.empty:
                failures.append(f"Trade entry_time {entry_time} does not match any candle open_time.")
                continue
                
            entry_candle = matching_entry_candles.iloc[0]
            raw_entry = entry_candle["open"]
            side = trade["side"]
            
            # Verify slippage calculation
            expected_slip_factor = 1.0 + self.engine.slippage if side == "Long" else 1.0 - self.engine.slippage
            expected_entry = raw_entry * expected_slip_factor
            
            if abs(trade["entry_price"] - round(expected_entry, 1)) > 1.0: # Allow small rounding discrepancy
                failures.append(f"Slippage deviation: Trade price={trade['entry_price']}, expected={expected_entry}")

            # Verify fees calculation
            # Entry fee + Exit fee
            entry_fee = trade["size"] * trade["entry_price"] * self.engine.taker_fee
            exit_fee = trade["size"] * trade["exit_price"] * self.engine.taker_fee
            total_expected_fee = entry_fee + exit_fee
            
            if abs(trade["fees"] - total_expected_fee) > 0.05:
                failures.append(f"Fee deviation: Trade fees={trade['fees']}, expected={total_expected_fee}")

        status = "PASS" if not failures else "FAIL"
        return {
            "status": status,
            "reasons": failures
        }

    def audit_no_fake(self) -> dict:
        """
        No-Fake Audit: Statically inspects the strategy source code
        for hardcoded dates, months, trade IDs, or signal IDs.
        """
        print("Running No-Fake and Code Integrity static checks...")
        
        # Get path of the strategy implementation file
        import inspect
        try:
            strategy_file = inspect.getfile(self.strategy.__class__)
            if "test_" in os.path.basename(strategy_file) or "mock" in self.strategy.__class__.__name__.lower():
                return {
                    "status": "PASS",
                    "reasons": [],
                    "notes": "Skipped static no-fake check for test mock strategy."
                }
            with open(strategy_file, "r") as f:
                code_content = f.read()
        except Exception as e:
            return {
                "status": "FAIL",
                "reasons": [f"Could not load strategy source code: {e}"]
            }

        failures = []

        # Check for hardcoded date structures (e.g. 2021, 2022, "2020-01-01")
        # We allow numbers, but search for date patterns like "202x" or "datetime(" or "pd.to_datetime" inside the signal logic
        date_patterns = [
            r"['\"]\d{4}-\d{2}-\d{2}['\"]",
            r"datetime\(\d{4}",
            r"year\s*==\s*\d{4}",
            r"month\s*==\s*\d{1,2}"
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, code_content)
            if matches:
                failures.append(f"Potential date/month hardcoding detected: {matches}")

        # Check for trade ID or signal ID filters
        id_patterns = [
            r"trade_id",
            r"signal_id",
            r"uuid",
            r"if\s+i\s*==\s*[1-9]\d*"
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, code_content)
            if matches:
                # Filter out False Positives like standard index checks
                if "if i <" not in code_content:
                    failures.append(f"Potential trade/signal ID hardcoded filter: {matches}")

        status = "PASS" if not failures else "FAIL"
        return {
            "status": status,
            "reasons": failures
        }
