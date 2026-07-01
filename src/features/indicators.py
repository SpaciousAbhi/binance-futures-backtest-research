import numpy as np
import pandas as pd

def calculate_sma(df: pd.DataFrame, window: int, column: str = "close") -> pd.Series:
    return df[column].rolling(window=window).mean()

def calculate_ema(df: pd.DataFrame, window: int, column: str = "close") -> pd.Series:
    return df[column].ewm(span=window, adjust=False).mean()

def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # Use wilder's moving average (exponential with alpha = 1/window)
    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calculate_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # Wilder's smoothing for ATR
    atr = tr.ewm(alpha=1/window, adjust=False).mean()
    return atr

def calculate_atr_percentile(df: pd.DataFrame, atr_col: str, window: int = 250) -> pd.Series:
    """Calculates where the current ATR stands relative to historical ATR over a rolling window."""
    atr = df[atr_col]
    rolling_min = atr.rolling(window=window).min()
    rolling_max = atr.rolling(window=window).max()
    denom = (rolling_max - rolling_min).replace(0, np.nan)
    norm = (atr - rolling_min) / denom
    return norm.fillna(0.5)

def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> tuple:
    sma = calculate_sma(df, window)
    rstd = df["close"].rolling(window=window).std()
    upper = sma + (rstd * num_std)
    lower = sma - (rstd * num_std)
    width = (upper - lower) / sma
    return sma, upper, lower, width

def calculate_vwap(df: pd.DataFrame) -> tuple:
    """
    Calculates daily-reset VWAP and VWAP bands.
    Resets at the start of each calendar day in UTC.
    """
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    v = df["volume"]
    pv = tp * v

    # Identify day changes using datetime column
    dates = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.date
    
    # Calculate cumulative sums resetting each day
    cum_pv = pv.groupby(dates).cumsum()
    cum_v = v.groupby(dates).cumsum()
    
    # Prevent division by zero
    vwap = cum_pv / cum_v.replace(0, np.nan)
    vwap = vwap.fillna(df["close"]) # Fallback to close if volume is zero

    # Standard deviation of price from VWAP for bands
    # Resetting squared price-VWAP dev sum
    dev = (df["close"] - vwap) ** 2
    cum_dev = dev * v
    cum_dev_sum = cum_dev.groupby(dates).cumsum()
    vwap_std = np.sqrt(cum_dev_sum / cum_v.replace(0, np.nan))
    vwap_std = vwap_std.fillna(0)

    upper_band = vwap + 2.0 * vwap_std
    lower_band = vwap - 2.0 * vwap_std

    return vwap, upper_band, lower_band

def calculate_adx(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Calculates Average Directional Index (ADX) to determine trend strength."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    # True Range
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/window, adjust=False).mean()

    # Directional Movement
    up_move = high - prev_high
    down_move = prev_low - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/window, adjust=False).mean() / atr.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/window, adjust=False).mean() / atr.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/window, adjust=False).mean()

    return adx.fillna(0)

def calculate_swing_highs_lows(df: pd.DataFrame, window: int = 5) -> tuple:
    """
    Identifies swing highs and swing lows.
    A swing high is the highest high in a window of 2*window + 1 candles.
    """
    highs = df["high"]
    lows = df["low"]
    
    # Vectorized rolling max/min (centered window)
    rolling_max = highs.rolling(window=2*window+1, center=True).max()
    rolling_min = lows.rolling(window=2*window+1, center=True).min()
    
    swing_highs = pd.Series(np.where(highs == rolling_max, highs, np.nan), index=df.index)
    swing_lows = pd.Series(np.where(lows == rolling_min, lows, np.nan), index=df.index)
    
    # Forward fill running levels (shifted by window to prevent lookahead)
    running_high = swing_highs.shift(window).ffill()
    running_low = swing_lows.shift(window).ffill()
    
    return running_high, running_low

def calculate_wick_metrics(df: pd.DataFrame) -> tuple:
    """Calculates wick and body sizes as ratios."""
    body = (df["close"] - df["open"]).abs()
    total_range = df["high"] - df["low"]
    total_range = total_range.replace(0, 0.0001) # Avoid division by zero

    upper_wick = np.where(df["close"] >= df["open"], df["high"] - df["close"], df["high"] - df["open"])
    lower_wick = np.where(df["close"] >= df["open"], df["open"] - df["low"], df["close"] - df["low"])

    upper_wick_ratio = upper_wick / total_range
    lower_wick_ratio = lower_wick / total_range
    body_ratio = body / total_range

    return pd.Series(upper_wick_ratio, index=df.index), pd.Series(lower_wick_ratio, index=df.index), pd.Series(body_ratio, index=df.index)

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Enriches DataFrame with all required features and regime classification."""
    df = df.copy()
    
    # SMA / EMA
    df["sma_20"] = calculate_sma(df, 20)
    df["ema_50"] = calculate_ema(df, 50)
    df["ema_200"] = calculate_ema(df, 200)

    # RSI
    df["rsi_14"] = calculate_rsi(df, 14)

    # ATR & ATR Percentile
    df["atr_14"] = calculate_atr(df, 14)
    df["atr_pct"] = calculate_atr_percentile(df, "atr_14", 250)

    # Bollinger Bands
    df["bb_mid"], df["bb_upper"], df["bb_lower"], df["bb_width"] = calculate_bollinger_bands(df, 20, 2.0)

    # VWAP
    df["vwap"], df["vwap_upper"], df["vwap_lower"] = calculate_vwap(df)

    # ADX
    df["adx"] = calculate_adx(df, 14)
    df["adx_slope_1"] = df["adx"].diff(1).fillna(0.0)
    df["adx_slope_3"] = df["adx"].diff(3).fillna(0.0)
    df["adx_slope_5"] = df["adx"].diff(5).fillna(0.0)
    
    # Volume Trend (rolling window 20)
    df["volume_trend"] = (df["volume"] / df["volume"].rolling(20).mean()).fillna(1.0)

    # Swing Highs/Lows
    df["swing_high"], df["swing_low"] = calculate_swing_highs_lows(df, 5)

    # Wick ratios
    df["upper_wick_ratio"], df["lower_wick_ratio"], df["body_ratio"] = calculate_wick_metrics(df)

    # Extract time metrics for session range breakouts
    dt = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["hour"] = dt.dt.hour
    df["dayofweek"] = dt.dt.dayofweek
    df["date_strs"] = dt.dt.date.astype(str)
    df["days_of_month"] = dt.dt.day

    # Add funding details
    df["funding_rate_roll_3d"] = df["fundingRate"].rolling(window=72).sum() # ~3 days on 1h

    # --- REGIME DETECTION ENGINE (Non-leaking, closed data only) ---
    df["regime_bull_trend"] = (df["ema_50"] > df["ema_200"]) & (df["close"] > df["ema_200"]) & (df["adx"] >= 25)
    df["regime_bear_trend"] = (df["ema_50"] < df["ema_200"]) & (df["close"] < df["ema_200"]) & (df["adx"] >= 25)
    df["regime_sideways_range"] = (df["adx"] < 20) & (df["bb_width"] < 0.05)
    df["regime_vol_compression"] = (df["bb_width"] < 0.03) | (df["atr_pct"] < 0.2)
    df["regime_vol_expansion"] = (df["bb_width"] > 0.08) | (df["atr_pct"] > 0.8)
    df["regime_funding_extreme"] = (df["fundingRate"].abs() > 0.0005) | (df["funding_rate_roll_3d"].abs() > 0.003)
    df["regime_toxic_chop"] = (df["adx"] < 15) & (df["bb_width"] < 0.025)
    
    return df
