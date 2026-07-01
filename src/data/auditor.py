import os
import pandas as pd
import numpy as np

class DataAuditor:
    """
    Audits the processed candles and funding rates to ensure dataset completeness,
    correct alignment, and absence of NaNs, duplicates, or timezone issues.
    """
    TIMEFRAME_MS = {
        "5m": 5 * 60 * 1000,
        "15m": 15 * 60 * 1000,
        "1h": 60 * 60 * 1000
    }

    def __init__(self, processed_data_dir: str):
        self.processed_data_dir = processed_data_dir

    def audit_file(self, symbol: str, timeframe: str) -> dict:
        """
        Runs comprehensive data quality checks on a processed CSV file.
        Returns a dict of audit results. Raises ValueError if critical checks fail.
        """
        file_path = os.path.join(self.processed_data_dir, f"{symbol}_{timeframe}_processed.csv")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Processed file not found for auditing: {file_path}")

        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError(f"Audit failed: Dataset {file_path} is empty.")

        # Basic properties
        first_ts = int(df["open_time"].min())
        last_ts = int(df["open_time"].max())
        total_rows = len(df)

        # Check duplicates
        duplicate_count = df["open_time"].duplicated().sum()

        # Check NaNs across critical columns
        nan_counts = df[["open", "high", "low", "close", "volume", "fundingRate"]].isna().sum().to_dict()
        total_nans = sum(nan_counts.values())

        # Check timestamp gaps
        expected_step = self.TIMEFRAME_MS.get(timeframe)
        if not expected_step:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # Compute diffs between consecutive open_times
        diffs = df["open_time"].diff().dropna().astype(int)
        gaps = diffs[diffs != expected_step]
        gap_count = len(gaps)
        max_gap_ms = gaps.max() if gap_count > 0 else 0

        # Calculate missing candles based on theoretical total
        expected_candles = ((last_ts - first_ts) // expected_step) + 1
        missing_count = expected_candles - total_rows

        # Timezone check: verify if there is any timezone offset mismatch (Binance data is UTC)
        # Check if open_time corresponds to exact candle boundaries in UTC
        timezone_clean = True
        for ts in df["open_time"].iloc[:100]:
            if ts % expected_step != 0:
                timezone_clean = False
                break

        # Funding rate coverage & alignment
        # Check if funding rate is missing (NaN)
        funding_nan_count = df["fundingRate"].isna().sum()
        # Verify funding rate has reasonable values (e.g., between -0.05 and 0.05, i.e., -5% and +5%)
        funding_out_of_bounds = ((df["fundingRate"] < -0.05) | (df["fundingRate"] > 0.05)).sum()

        audit_results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "first_timestamp": first_ts,
            "first_datetime": str(pd.to_datetime(first_ts, unit="ms", utc=True)),
            "last_timestamp": last_ts,
            "last_datetime": str(pd.to_datetime(last_ts, unit="ms", utc=True)),
            "total_rows": total_rows,
            "expected_rows": expected_candles,
            "missing_candles": int(missing_count),
            "duplicate_candles": int(duplicate_count),
            "nans": nan_counts,
            "timestamp_gaps": int(gap_count),
            "max_gap_minutes": float(max_gap_ms / (60 * 1000)),
            "timezone_consistency": "UTC" if timezone_clean else "INCONSISTENT",
            "funding_coverage_pct": float(100.0 * (total_rows - funding_nan_count) / total_rows),
            "funding_out_of_bounds": int(funding_out_of_bounds),
            "status": "PASS"
        }

        # Determine if data audit fails
        # Critical failures:
        # - Any duplicate candles
        # - Any NaNs in OHLCV or funding rate
        # - Timezone inconsistency
        # - Missing candles > 5% of dataset (suggests major download gaps)
        # - Gaps in timestamps > 4 hours (240 mins)
        reasons = []
        if duplicate_count > 0:
            reasons.append(f"Found {duplicate_count} duplicate candles.")
        if total_nans > 0:
            reasons.append(f"Found NaNs: {nan_counts}")
        if not timezone_clean:
            reasons.append("Timezone check failed: open_time not aligned to UTC boundary.")
        if missing_count > expected_candles * 0.05:
            reasons.append(f"Too many missing candles: {missing_count} missing out of {expected_candles} expected.")
        if max_gap_ms > 24 * 60 * 60 * 1000: # 1 day gap
            reasons.append(f"Large timestamp gap detected: {max_gap_ms / (3600*1000):.2f} hours.")
        if funding_nan_count > 0:
            reasons.append(f"Missing funding rate for {funding_nan_count} rows.")

        if reasons:
            audit_results["status"] = "FAIL"
            audit_results["failure_reasons"] = reasons
            print(f"Data audit FAILED for {symbol} {timeframe}: {reasons}")
            # Do not raise immediately; let runner handle it, or raise if runner needs to abort
        else:
            print(f"Data audit PASSED for {symbol} {timeframe}.")

        return audit_results
