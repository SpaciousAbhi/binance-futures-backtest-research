"""
scratch/generate_manifest.py
Generates the data manifest reports/data_manifest_phase11_1.json
"""
import os
import sys
import json
import hashlib
from datetime import datetime, timezone
import pandas as pd

def get_file_sha256(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    manifest_path = "reports/data_manifest_phase11_1.json"
    print("Generating data manifest...")
    
    files = {
        "1h_processed": "data/processed/BTCUSDT_1h_processed.csv",
        "15m_processed": "data/processed/BTCUSDT_15m_processed.csv",
        "5m_processed": "data/processed/BTCUSDT_5m_processed.csv"
    }
    
    manifest = {
        "symbol": "BTCUSDT",
        "market_type": "Perpetual Futures (Binance USD-M)",
        "generation_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "files": {}
    }
    
    for label, path in files.items():
        if not os.path.exists(path):
            print(f"File {path} not found, skipping...")
            continue
            
        df = pd.read_csv(path)
        
        # Calculate missing/duplicate candles
        df["open_datetime"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        time_diffs = df["open_time"].diff().dropna()
        timeframe_ms = time_diffs.median()
        
        expected_candles = int((df["open_time"].max() - df["open_time"].min()) / timeframe_ms) + 1
        missing_candles = int(expected_candles - len(df))
        duplicate_candles = int(df["open_time"].duplicated().sum())
        nan_count = int(df.isna().sum().sum())
        
        # Funding rate coverage
        funding_col = "fundingRate" if "fundingRate" in df.columns else "fundingRate_1h" if "fundingRate_1h" in df.columns else None
        if funding_col:
            funding_coverage = float((df[funding_col] != 0.0).sum() / len(df))
        else:
            funding_coverage = 0.0
            
        file_hash = get_file_sha256(path)
        
        manifest["files"][label] = {
            "path": path,
            "hash": file_hash,
            "row_count": len(df),
            "first_timestamp": int(df["open_time"].min()),
            "last_timestamp": int(df["open_time"].max()),
            "first_datetime_utc": str(df["open_datetime"].min()),
            "last_datetime_utc": str(df["open_datetime"].max()),
            "missing_candles": missing_candles,
            "duplicate_candles": duplicate_candles,
            "nan_count": nan_count,
            "funding_coverage_pct": round(funding_coverage * 100.0, 2)
        }
        
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Data manifest saved to: {manifest_path}")

if __name__ == "__main__":
    main()
