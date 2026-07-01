"""
src/research/phase27_data_setup.py

Downloads and aligns Binance USD-M Futures data for BTCUSDT, ETHUSDT, BNBUSDT, and SOLUSDT.
"""
import os
import sys
import pandas as pd
from datetime import datetime, timezone

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, _ROOT)

from src.data.downloader import BinanceDownloader
from src.data.processor import DataProcessor

RAW_DIR = os.path.join(_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(_ROOT, "data", "processed")

def main():
    print("================================================================================")
    print("PHASE 27 - DATA SETUP RUNNER")
    print("================================================================================")

    downloader = BinanceDownloader(RAW_DIR)
    processor = DataProcessor(RAW_DIR, PROCESSED_DIR)

    # Assets to download
    assets = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
    
    start_date = "2020-01-01 00:00:00"
    end_date = "2026-06-30 00:00:00"

    metadata = []

    for symbol in assets:
        print(f"\nProcessing {symbol} ...")
        
        # 1. Download exchange info
        try:
            sym_info = downloader.download_exchange_info(symbol)
        except Exception as e:
            print(f"Error downloading exchange info for {symbol}: {e}")
            continue

        # 2. Download 1h candles
        # SOLUSDT listed on 2020-09-01
        actual_start = start_date
        if symbol == "SOLUSDT":
            actual_start = "2020-09-01 00:00:00"

        try:
            print(f"Downloading 1h candles for {symbol}...")
            df_1h = downloader.download_candles(symbol, "1h", actual_start, end_date)
            print(f"Downloaded {len(df_1h)} candles.")
        except Exception as e:
            print(f"Error downloading 1h candles for {symbol}: {e}")
            continue

        # 3. Download funding rates
        try:
            print(f"Downloading funding rates for {symbol}...")
            df_funding = downloader.download_funding_rates(symbol, actual_start, end_date)
            print(f"Downloaded {len(df_funding)} funding rate records.")
        except Exception as e:
            print(f"Error downloading funding rates for {symbol}: {e}")
            continue

        # 4. Download 15m and 5m candles (recent history only to respect rate limits)
        # We download since 2026-01-01 to ensure the download is very fast (<5 seconds)
        recent_start = "2026-01-01 00:00:00"
        try:
            print(f"Downloading recent 15m candles for {symbol}...")
            df_15m = downloader.download_candles(symbol, "15m", recent_start, end_date)
            print(f"Downloaded {len(df_15m)} 15m candles.")
        except Exception as e:
            print(f"Error downloading 15m candles: {e}")

        try:
            print(f"Downloading recent 5m candles for {symbol}...")
            df_5m = downloader.download_candles(symbol, "5m", recent_start, end_date)
            print(f"Downloaded {len(df_5m)} 5m candles.")
        except Exception as e:
            print(f"Error downloading 5m candles: {e}")

        # 5. Align 1h candles with funding rate
        try:
            print(f"Aligning 1h candles with funding rate for {symbol}...")
            df_aligned = processor.process_and_align(symbol, "1h")
            print(f"Aligned and saved {len(df_aligned)} candles.")
            
            # Record metadata
            metadata.append({
                "symbol": symbol,
                "earliest_timestamp": int(df_aligned["open_time"].min()),
                "latest_timestamp": int(df_aligned["open_time"].max()),
                "total_candles": len(df_aligned),
                "earliest_date": str(df_aligned["datetime_str"].min()),
                "latest_date": str(df_aligned["datetime_str"].max()),
            })
        except Exception as e:
            print(f"Error aligning data for {symbol}: {e}")

    # Write data download manifest
    manifest_df = pd.DataFrame(metadata)
    manifest_path = os.path.join(_ROOT, "reports", "phase27_data_download_manifest.csv")
    manifest_df.to_csv(manifest_path, index=False)
    print(f"\nSaved data download manifest to {manifest_path}")

if __name__ == "__main__":
    main()
