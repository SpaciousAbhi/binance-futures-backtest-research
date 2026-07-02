import os
import time
from pathlib import Path

import pandas as pd
import requests


BASE_URL = "https://fapi.binance.com"
ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT.parent / "phase29_market_data"
RAW_DIR = OUT_ROOT / "raw"
PROCESSED_DIR = OUT_ROOT / "processed"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
TIMEFRAMES = ["1h", "15m", "5m"]
START_TS = int(pd.Timestamp("2020-01-01T00:00:00Z").timestamp() * 1000)
END_TS = int(pd.Timestamp("2026-07-01T00:00:00Z").timestamp() * 1000)

INTERVAL_MS = {
    "1h": 60 * 60 * 1000,
    "15m": 15 * 60 * 1000,
    "5m": 5 * 60 * 1000,
}

CANDLE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "ignore",
]


def request_json(endpoint, params, retries=8):
    url = f"{BASE_URL}{endpoint}"
    delay = 0.5
    for attempt in range(retries):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 429:
            sleep_for = int(response.headers.get("Retry-After", "10"))
        else:
            sleep_for = delay
            delay = min(delay * 2, 20)
        print(f"request retry {attempt + 1}/{retries}: {response.status_code} {response.text[:160]}")
        time.sleep(sleep_for)
    response.raise_for_status()


def load_existing(path, time_col):
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty or time_col not in df.columns:
        return pd.DataFrame()
    df[time_col] = df[time_col].astype("int64")
    return df.sort_values(time_col).drop_duplicates(time_col).reset_index(drop=True)


def fetch_candles(symbol, interval):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{symbol}_{interval}_raw.csv"
    existing = load_existing(path, "open_time")
    start_ts = START_TS
    if not existing.empty:
        step = INTERVAL_MS[interval]
        if int(existing["open_time"].max()) >= END_TS - step:
            print(f"candles cached {symbol} {interval}: {len(existing)} rows")
            return existing
        start_ts = int(existing["open_time"].max()) + step

    rows = []
    cursor = start_ts
    while cursor <= END_TS:
        batch = request_json(
            "/fapi/v1/klines",
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": cursor,
                "endTime": END_TS,
                "limit": 1500,
            },
        )
        if not batch:
            break
        rows.extend(batch)
        last_open = int(batch[-1][0])
        next_cursor = last_open + INTERVAL_MS[interval]
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        if len(batch) < 1500:
            break
        time.sleep(0.02)

    if rows:
        new_df = pd.DataFrame(rows, columns=CANDLE_COLUMNS)
        for col in CANDLE_COLUMNS:
            if col != "ignore":
                new_df[col] = pd.to_numeric(new_df[col])
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.sort_values("open_time").drop_duplicates("open_time").reset_index(drop=True)
    else:
        combined = existing

    if combined.empty:
        raise RuntimeError(f"no candle data returned for {symbol} {interval}")
    combined.to_csv(path, index=False)
    print(f"candles saved {symbol} {interval}: {len(combined)} rows")
    return combined


def fetch_funding(symbol):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{symbol}_funding_raw.csv"
    existing = load_existing(path, "fundingTime")
    start_ts = START_TS
    if not existing.empty:
        if int(existing["fundingTime"].max()) >= END_TS - 8 * 60 * 60 * 1000:
            print(f"funding cached {symbol}: {len(existing)} rows")
            return existing
        start_ts = int(existing["fundingTime"].max()) + 1

    rows = []
    cursor = start_ts
    while cursor <= END_TS:
        batch = request_json(
            "/fapi/v1/fundingRate",
            {
                "symbol": symbol,
                "startTime": cursor,
                "endTime": END_TS,
                "limit": 1000,
            },
        )
        if not batch:
            break
        rows.extend(batch)
        last_time = int(batch[-1]["fundingTime"])
        cursor = last_time + 1
        if len(batch) < 1000:
            break
        time.sleep(0.02)

    if rows:
        new_df = pd.DataFrame(rows)
        new_df["fundingTime"] = new_df["fundingTime"].astype("int64")
        new_df["fundingRate"] = pd.to_numeric(new_df["fundingRate"])
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.sort_values("fundingTime").drop_duplicates("fundingTime").reset_index(drop=True)
    else:
        combined = existing

    if combined.empty:
        raise RuntimeError(f"no funding data returned for {symbol}")
    combined.to_csv(path, index=False)
    print(f"funding saved {symbol}: {len(combined)} rows")
    return combined


def process(symbol, interval, candles, funding):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    candles = candles.sort_values("open_time").reset_index(drop=True).copy()
    funding = funding.sort_values("fundingTime").reset_index(drop=True).copy()
    merged = pd.merge_asof(
        candles,
        funding[["fundingTime", "fundingRate"]],
        left_on="open_time",
        right_on="fundingTime",
        direction="backward",
    )
    merged["fundingRate"] = merged["fundingRate"].ffill().bfill()
    merged["fundingTime"] = merged["fundingTime"].fillna(0).astype("int64")
    merged["close_time"] = merged["open_time"].astype("int64") + INTERVAL_MS[interval] - 1
    out_path = PROCESSED_DIR / f"{symbol}_{interval}_processed.csv"
    merged.to_csv(out_path, index=False)
    print(f"processed saved {symbol} {interval}: {len(merged)} rows")


def main():
    print(f"writing external audit data under {OUT_ROOT}")
    for symbol in SYMBOLS:
        funding = fetch_funding(symbol)
        for interval in TIMEFRAMES:
            candles = fetch_candles(symbol, interval)
            process(symbol, interval, candles, funding)


if __name__ == "__main__":
    main()
