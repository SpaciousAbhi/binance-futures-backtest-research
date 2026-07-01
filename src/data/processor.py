import os
import pandas as pd
from datetime import datetime, timezone

class DataProcessor:
    """
    Processes raw candles and funding rates, aligning them using merge_asof.
    Fills gaps and saves the clean, combined data.
    """
    def __init__(self, raw_data_dir: str, processed_data_dir: str):
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        os.makedirs(processed_data_dir, exist_ok=True)

    def process_and_align(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Loads raw candles and funding rates, merges them on time, and saves the result.
        """
        candles_path = os.path.join(self.raw_data_dir, f"{symbol}_{timeframe}_raw.csv")
        funding_path = os.path.join(self.raw_data_dir, f"{symbol}_funding_raw.csv")

        if not os.path.exists(candles_path):
            raise FileNotFoundError(f"Raw candle data not found: {candles_path}")
        if not os.path.exists(funding_path):
            raise FileNotFoundError(f"Raw funding data not found: {funding_path}")

        # Load data
        candles = pd.read_csv(candles_path)
        funding = pd.read_csv(funding_path)

        # Sort by timestamp
        candles = candles.sort_values("open_time").reset_index(drop=True)
        funding = funding.sort_values("fundingTime").reset_index(drop=True)

        # Ensure correct column types
        candles["open_time"] = candles["open_time"].astype(int)
        funding["fundingTime"] = funding["fundingTime"].astype(int)
        funding["fundingRate"] = funding["fundingRate"].astype(float)

        # Check for empty dataframes
        if candles.empty:
            raise ValueError(f"Candles DataFrame is empty for {timeframe}")
        if funding.empty:
            raise ValueError("Funding DataFrame is empty")

        # Merge using merge_asof
        # We want to associate each candle with the most recent funding rate available at or before open_time.
        merged = pd.merge_asof(
            candles,
            funding[["fundingTime", "fundingRate"]],
            left_on="open_time",
            right_on="fundingTime",
            direction="backward"
        )

        # Forward fill and then backfill funding rate if any NaNs (e.g. before the first funding rate record)
        merged["fundingRate"] = merged["fundingRate"].ffill().bfill()
        # Default fundingTime to 0 if not matched
        merged["fundingTime"] = merged["fundingTime"].fillna(0).astype(int)

        # Compute close_time
        duration_ms = 300000 if timeframe == "5m" else 900000 if timeframe == "15m" else 3600000
        merged["close_time"] = merged["open_time"] + duration_ms

        # Add datetime columns for readability / debugging (UTC)
        merged["datetime"] = pd.to_datetime(merged["open_time"], unit="ms", utc=True)
        merged["datetime_str"] = merged["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

        # Save processed data
        out_path = os.path.join(self.processed_data_dir, f"{symbol}_{timeframe}_processed.csv")
        merged.to_csv(out_path, index=False)
        print(f"Processed and aligned {len(merged)} candles for {timeframe}, saved to {out_path}")
        return merged

    @staticmethod
    def align_multitimeframe_data(df_5m: pd.DataFrame, df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> pd.DataFrame:
        """
        Aligns 15m and 1h DataFrames onto the 5m DataFrame using pd.merge_asof.
        Assumes close_time columns exist and are sorted.
        Adds suffixes _15m and _1h to columns from secondary timeframes.
        """
        df_5m = df_5m.sort_values("close_time").reset_index(drop=True)
        df_15m = df_15m.sort_values("close_time").reset_index(drop=True)
        df_1h = df_1h.sort_values("close_time").reset_index(drop=True)

        # Rename columns to avoid collision, keeping close_time as merge key
        cols_15m = {col: f"{col}_15m" for col in df_15m.columns if col != "close_time"}
        df_15m_renamed = df_15m.rename(columns=cols_15m)

        cols_1h = {col: f"{col}_1h" for col in df_1h.columns if col != "close_time"}
        df_1h_renamed = df_1h.rename(columns=cols_1h)

        # Lookahead-free backward merge
        merged = pd.merge_asof(
            df_5m,
            df_15m_renamed,
            on="close_time",
            direction="backward"
        )
        merged = pd.merge_asof(
            merged,
            df_1h_renamed,
            on="close_time",
            direction="backward"
        )
        return merged

