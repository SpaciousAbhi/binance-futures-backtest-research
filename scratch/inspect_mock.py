import numpy as np
import pandas as pd
from src.features.indicators import add_indicators

open_times = [1577836800000 + i * 15 * 60 * 1000 for i in range(100)] # 15m candles
prices = [10000.0]
for i in range(99):
    prices.append(prices[-1] * 1.001)
    
df = pd.DataFrame({
    "open_time": open_times,
    "open": prices,
    "high": [p * 1.002 for p in prices],
    "low": [p * 0.998 for p in prices],
    "close": prices,
    "volume": [100.0] * 100,
    "fundingRate": [0.0] * 100
})
df = add_indicators(df)
print("Columns:", df.columns)
print("BB Upper:", df["bb_upper_1h"].mean() if "bb_upper_1h" in df.columns else "No bb_upper_1h")
print("BB Upper (raw):", df["bb_upper"].mean() if "bb_upper" in df.columns else "No bb_upper")
print("BB Width:", df["bb_width"].mean() if "bb_width" in df.columns else "No bb_width")
print("Close > BB Upper count:", (df["close"] > df["bb_upper"]).sum() if "bb_upper" in df.columns else "N/A")
print("Close > BB Upper 1h count:", (df["close"] > df["bb_upper_1h"]).sum() if "bb_upper_1h" in df.columns else "N/A")
