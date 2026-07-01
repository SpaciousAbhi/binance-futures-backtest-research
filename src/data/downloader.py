import os
import time
import requests
import json
import pandas as pd
from datetime import datetime, timezone

class BinanceDownloader:
    """
    Downloads public historical market data and funding rates from Binance USD-M Futures.
    Implements pagination, exponential backoff, and local caching/incremental downloading.
    """
    BASE_URL = "https://fapi.binance.com"

    def __init__(self, raw_data_dir: str):
        self.raw_data_dir = raw_data_dir
        os.makedirs(raw_data_dir, exist_ok=True)

    def _request_with_retry(self, endpoint: str, params: dict, max_retries: int = 5) -> list:
        url = f"{self.BASE_URL}{endpoint}"
        retries = 0
        backoff = 1.0
        while retries < max_retries:
            try:
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 429:
                    # Rate limit hit, backoff longer
                    retry_after = int(response.headers.get("Retry-After", 10))
                    print(f"Rate limited (429). Sleeping for {retry_after} seconds...")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                elif response.status_code != 200:
                    print(f"Error {response.status_code}: {response.text}. Retrying in {backoff}s...")
                    time.sleep(backoff)
                    backoff *= 2
                    retries += 1
                    continue
                return response.json()
            except requests.RequestException as e:
                print(f"Request exception: {e}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
                retries += 1
        raise Exception(f"Failed to fetch data from {url} after {max_retries} retries.")

    def download_exchange_info(self, symbol: str) -> dict:
        """Downloads exchange info for symbol metadata, filters, and precision checks."""
        print(f"Downloading exchange info for {symbol}...")
        data = self._request_with_retry("/fapi/v1/exchangeInfo", {})
        symbols_info = data.get("symbols", [])
        for sym_info in symbols_info:
            if sym_info["symbol"] == symbol:
                info_path = os.path.join(self.raw_data_dir, f"{symbol}_exchange_info.json")
                with open(info_path, "w") as f:
                    json.dump(sym_info, f, indent=4)
                print(f"Saved exchange info to {info_path}")
                return sym_info
        raise ValueError(f"Symbol {symbol} not found in exchange info.")

    def download_candles(self, symbol: str, timeframe: str, start_str: str, end_str: str) -> pd.DataFrame:
        """
        Downloads OHLCV candles from start_str to end_str.
        Loads existing local file and performs incremental downloads if possible.
        """
        file_path = os.path.join(self.raw_data_dir, f"{symbol}_{timeframe}_raw.csv")
        start_ts = int(pd.to_datetime(start_str).tz_localize(timezone.utc).timestamp() * 1000)
        end_ts = int(pd.to_datetime(end_str).tz_localize(timezone.utc).timestamp() * 1000)

        existing_df = pd.DataFrame()
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path)
                if not existing_df.empty and "open_time" in existing_df.columns:
                    # Drop duplicate headers/cleanup if any
                    existing_df = existing_df.dropna(subset=["open_time"])
                    existing_df["open_time"] = existing_df["open_time"].astype(int)
                    existing_df = existing_df.sort_values("open_time").drop_duplicates(subset=["open_time"])
                    last_ts = existing_df["open_time"].max()
                    # If we already have up to the end_ts (or close to it, within 2 intervals), return it
                    if last_ts >= end_ts - 5000:
                        print(f"Local file {file_path} is up-to-date.")
                        return existing_df
                    # Adjust start_ts to incrementally download from last_ts + 1
                    start_ts = last_ts + 1
                    print(f"Found local file for {timeframe}. Incremental download starting from {datetime.fromtimestamp(start_ts/1000, tz=timezone.utc)}")
            except Exception as e:
                print(f"Error reading local file {file_path}: {e}. Redownloading from scratch.")
                existing_df = pd.DataFrame()

        print(f"Downloading {symbol} {timeframe} candles from {datetime.fromtimestamp(start_ts/1000, tz=timezone.utc)}...")
        
        limit = 1500
        candles = []
        current_start = start_ts

        while current_start < end_ts:
            params = {
                "symbol": symbol,
                "interval": timeframe,
                "startTime": current_start,
                "endTime": end_ts,
                "limit": limit
            }
            batch = self._request_with_retry("/fapi/v1/klines", params)
            if not batch:
                break
            candles.extend(batch)
            last_candle_open = batch[-1][0]
            if len(batch) < limit:
                break
            # Binance klines are inclusive of startTime. To avoid duplicates, start next batch after the last candle's open time.
            # We can calculate the timeframe delta or just add 1ms since it is open time.
            current_start = last_candle_open + 1
            # Add a small delay to respect rate limit limits (1200 weight per minute, klines has weight 2-10)
            time.sleep(0.05)

        if not candles:
            if not existing_df.empty:
                return existing_df
            raise ValueError(f"No candles downloaded for {symbol} {timeframe}.")

        # Convert to DataFrame
        columns = [
            "open_time", "open", "high", "low", "close", "volume", 
            "close_time", "quote_asset_volume", "number_of_trades", 
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ]
        new_df = pd.DataFrame(candles, columns=columns)
        # Convert numeric types
        numeric_cols = ["open", "high", "low", "close", "volume", "quote_asset_volume", 
                        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume"]
        new_df[numeric_cols] = new_df[numeric_cols].apply(pd.to_numeric)
        new_df["open_time"] = new_df["open_time"].astype(int)
        new_df["close_time"] = new_df["close_time"].astype(int)

        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.sort_values("open_time").drop_duplicates(subset=["open_time"])
        else:
            combined_df = new_df

        combined_df.to_csv(file_path, index=False)
        print(f"Saved {len(combined_df)} candles to {file_path}")
        return combined_df

    def download_funding_rates(self, symbol: str, start_str: str, end_str: str) -> pd.DataFrame:
        """Downloads funding rates with pagination and saving to CSV."""
        file_path = os.path.join(self.raw_data_dir, f"{symbol}_funding_raw.csv")
        start_ts = int(pd.to_datetime(start_str).tz_localize(timezone.utc).timestamp() * 1000)
        end_ts = int(pd.to_datetime(end_str).tz_localize(timezone.utc).timestamp() * 1000)

        existing_df = pd.DataFrame()
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path)
                if not existing_df.empty and "fundingTime" in existing_df.columns:
                    existing_df = existing_df.dropna(subset=["fundingTime"])
                    existing_df["fundingTime"] = existing_df["fundingTime"].astype(int)
                    existing_df = existing_df.sort_values("fundingTime").drop_duplicates(subset=["fundingTime"])
                    last_ts = existing_df["fundingTime"].max()
                    if last_ts >= end_ts - 5000:
                        print(f"Local funding file is up-to-date.")
                        return existing_df
                    start_ts = last_ts + 1
                    print(f"Found local funding file. Incremental download starting from {datetime.fromtimestamp(start_ts/1000, tz=timezone.utc)}")
            except Exception as e:
                print(f"Error reading local funding: {e}. Redownloading from scratch.")
                existing_df = pd.DataFrame()

        print(f"Downloading {symbol} funding rates from {datetime.fromtimestamp(start_ts/1000, tz=timezone.utc)}...")

        limit = 1000
        funding_records = []
        current_start = start_ts

        while current_start < end_ts:
            params = {
                "symbol": symbol,
                "startTime": current_start,
                "endTime": end_ts,
                "limit": limit
            }
            batch = self._request_with_retry("/fapi/v1/fundingRate", params)
            if not batch:
                break
            funding_records.extend(batch)
            last_record_time = batch[-1]["fundingTime"]
            if len(batch) < limit:
                break
            current_start = last_record_time + 1
            time.sleep(0.05)

        if not funding_records:
            if not existing_df.empty:
                return existing_df
            raise ValueError(f"No funding rates downloaded for {symbol}.")

        new_df = pd.DataFrame(funding_records)
        new_df["fundingTime"] = new_df["fundingTime"].astype(int)
        new_df["fundingRate"] = pd.to_numeric(new_df["fundingRate"])

        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.sort_values("fundingTime").drop_duplicates(subset=["fundingTime"])
        else:
            combined_df = new_df

        combined_df.to_csv(file_path, index=False)
        print(f"Saved {len(combined_df)} funding rate records to {file_path}")
        return combined_df
