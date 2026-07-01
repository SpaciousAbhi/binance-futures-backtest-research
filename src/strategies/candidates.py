import numpy as np
import pandas as pd
from src.strategies.base import BaseStrategy

class VolatilitySqueezeBreakout(BaseStrategy):
    """
    Hypothesis: When volatility is compressed (ATR percentile is low) and price breaks out 
    of the Bollinger Bands in the direction of the major EMA trend, it signals a strong breakout.
    """
    def __init__(self, params: dict = None):
        default_params = {
            "atr_pct_thresh": 0.35, # ATR below 35th percentile indicates squeeze
            "ema_trend_len": 200,   # Trend filter
            "rsi_filter": True,     # RSI filter to prevent buying overbought
            "tp_atr_mult": 2.5,     # Take profit multiple of ATR
            "sl_atr_mult": 1.5      # Stop loss multiple of ATR
        }
        if params:
            default_params.update(params)
        super().__init__(
            name="VolatilitySqueezeBreakout",
            hypothesis="Enter breakouts of Bollinger Bands when ATR volatility is compressed and price is aligned with EMA trend.",
            params=default_params
        )

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        if i < max(200, self.params["ema_trend_len"]):
            return None

        row = df.iloc[i]
        
        # Volatility Squeeze condition
        is_squeezed = row["atr_pct"] <= self.params["atr_pct_thresh"]
        
        # Major trend filter
        trend_long = row["close"] > row["ema_200"]
        trend_short = row["close"] < row["ema_200"]

        # RSI filters
        rsi = row["rsi_14"]
        rsi_long_ok = rsi < 65 if self.params["rsi_filter"] else True
        rsi_short_ok = rsi > 35 if self.params["rsi_filter"] else True

        # Breakout indicators
        close_above_bb = row["close"] > row["bb_upper"]
        close_below_bb = row["close"] < row["bb_lower"]

        atr = row["atr_14"]

        if is_squeezed:
            if close_above_bb and trend_long and rsi_long_ok:
                return {
                    "side": "Long",
                    "stop_loss": row["close"] - (atr * self.params["sl_atr_mult"]),
                    "take_profit": row["close"] + (atr * self.params["tp_atr_mult"]),
                    "reason": "BB Upper Breakout during Volatility Squeeze"
                }
            elif close_below_bb and trend_short and rsi_short_ok:
                return {
                    "side": "Short",
                    "stop_loss": row["close"] + (atr * self.params["sl_atr_mult"]),
                    "take_profit": row["close"] - (atr * self.params["tp_atr_mult"]),
                    "reason": "BB Lower Breakout during Volatility Squeeze"
                }
        return None

    def get_param_grid(self) -> dict:
        return {
            "atr_pct_thresh": [0.25, 0.35, 0.45],
            "tp_atr_mult": [2.0, 2.5, 3.0],
            "sl_atr_mult": [1.5, 2.0]
        }


class VWAPMeanReversionFunding(BaseStrategy):
    """
    Hypothesis: When price expands to outer VWAP Bands and the funding rate is extreme, 
    reversals are highly probable due to liquidations and extreme funding costs.
    """
    def __init__(self, params: dict = None):
        default_params = {
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "funding_threshold": 0.0001, # 0.01%
            "tp_atr_mult": 2.0,
            "sl_atr_mult": 1.5
        }
        if params:
            default_params.update(params)
        super().__init__(
            name="VWAPMeanReversionFunding",
            hypothesis="Revert to VWAP when price reaches extreme bands and funding rate is high/low.",
            params=default_params
        )

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        if i < 50:
            return None

        row = df.iloc[i]
        
        # Funding rate regime
        funding = row["fundingRate"]
        funding_long_ok = funding < -self.params["funding_threshold"] # Extreme negative funding -> positive pressure
        funding_short_ok = funding > self.params["funding_threshold"]  # Extreme positive funding -> short pressure

        # Extreme extension from VWAP
        above_vwap_upper = row["close"] > row["vwap_upper"]
        below_vwap_lower = row["close"] < row["vwap_lower"]

        # RSI conditions
        rsi = row["rsi_14"]
        rsi_overbought = rsi >= self.params["rsi_overbought"]
        rsi_oversold = rsi <= self.params["rsi_oversold"]

        atr = row["atr_14"]

        # Mean Reversion signals
        if below_vwap_lower and rsi_oversold and funding_long_ok:
            return {
                "side": "Long",
                "stop_loss": row["close"] - (atr * self.params["sl_atr_mult"]),
                "take_profit": row["vwap"], # Target is the VWAP mean
                "reason": "Oversold VWAP Mean Reversion with negative funding"
            }
        elif above_vwap_upper and rsi_overbought and funding_short_ok:
            return {
                "side": "Short",
                "stop_loss": row["close"] + (atr * self.params["sl_atr_mult"]),
                "take_profit": row["vwap"], # Target is the VWAP mean
                "reason": "Overbought VWAP Mean Reversion with positive funding"
            }
        return None

    def get_param_grid(self) -> dict:
        return {
            "rsi_overbought": [65, 70, 75],
            "rsi_oversold": [25, 30, 35],
            "funding_threshold": [0.00005, 0.0001, 0.00015]
        }


class MultiTimeframeTrendPullback(BaseStrategy):
    """
    Hypothesis: Trade pullbacks in trend direction. We define major trend on 1h (EMA 200)
    and enter pullbacks on 15m when momentum shifts back in trend direction.
    """
    def __init__(self, params: dict = None):
        default_params = {
            "adx_thresh": 20,
            "rsi_pullback_long": 40,
            "rsi_pullback_short": 60,
            "tp_atr_mult": 3.0,
            "sl_atr_mult": 1.5
        }
        if params:
            default_params.update(params)
        super().__init__(
            name="MultiTimeframeTrendPullback",
            hypothesis="Trade pullbacks on 15m aligned with 1h major trend, filtered by ADX trend strength.",
            params=default_params
        )

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        if i < 200:
            return None

        row = df.iloc[i]
        
        # ADX trend strength
        strong_trend = row["adx"] >= self.params["adx_thresh"]

        # Major trend on 1h (represented by ema_200 on 15m/1h)
        trend_long = row["close"] > row["ema_200"]
        trend_short = row["close"] < row["ema_200"]

        # RSI pullbacks
        rsi = row["rsi_14"]
        pullback_long = rsi <= self.params["rsi_pullback_long"]
        pullback_short = rsi >= self.params["rsi_pullback_short"]

        # Confirm price is near key support/resistance (EMA 50)
        near_ema50_long = row["low"] <= row["ema_50"] and row["close"] > row["ema_50"]
        near_ema50_short = row["high"] >= row["ema_50"] and row["close"] < row["ema_50"]

        atr = row["atr_14"]

        if strong_trend:
            if trend_long and pullback_long and near_ema50_long:
                return {
                    "side": "Long",
                    "stop_loss": row["close"] - (atr * self.params["sl_atr_mult"]),
                    "take_profit": row["close"] + (atr * self.params["tp_atr_mult"]),
                    "reason": "1h Trend Long, 15m RSI Pullback to EMA 50"
                }
            elif trend_short and pullback_short and near_ema50_short:
                return {
                    "side": "Short",
                    "stop_loss": row["close"] + (atr * self.params["sl_atr_mult"]),
                    "take_profit": row["close"] - (atr * self.params["tp_atr_mult"]),
                    "reason": "1h Trend Short, 15m RSI Pullback to EMA 50"
                }
        return None

    def get_param_grid(self) -> dict:
        return {
            "adx_thresh": [15, 20, 25],
            "rsi_pullback_long": [35, 40, 45],
            "rsi_pullback_short": [55, 60, 65]
        }


class SessionRangeBreakout(BaseStrategy):
    """
    Hypothesis: The high/low of the Asian session (00:00 to 08:00 UTC) represents key support/resistance.
    A breakout during the European/US session (08:00 to 20:00 UTC) will lead to strong continuation.
    """
    def __init__(self, params: dict = None):
        default_params = {
            "breakout_atr_mult": 1.0,
            "tp_atr_mult": 2.5,
            "sl_atr_mult": 1.5
        }
        if params:
            default_params.update(params)
        super().__init__(
            name="SessionRangeBreakout",
            hypothesis="Trade breakouts of the 00:00-08:00 UTC Asian session range during active London/NY hours.",
            params=default_params
        )

        self.last_day = None
        self.asian_high = None
        self.asian_low = None

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        if i < 50:
            return None

        # Cache array references
        if not hasattr(self, "_cached_df_id") or self._cached_df_id != id(df):
            self._cached_df_id = id(df)
            self._close = df["close"].values
            self._high = df["high"].values
            self._low = df["low"].values
            self._open_time = df["open_time"].values
            self._atr_14 = df["atr_14"].values
            
            # Pre-calculate hour and date vectors to avoid pd.to_datetime inside loop
            dts = pd.to_datetime(df["open_time"], unit="ms", utc=True)
            self._hours = dts.dt.hour.values
            self._dates = dts.dt.date.values

        hour = self._hours[i]
        day = self._dates[i]

        # If it's a new day, reset ranges
        if self.last_day != day:
            self.last_day = day
            self.asian_high = None
            self.asian_low = None

        # Accumulate Asian range between 00:00 and 08:00 UTC
        if 0 <= hour < 8:
            if self.asian_high is None:
                self.asian_high = self._high[i]
                self.asian_low = self._low[i]
            else:
                self.asian_high = max(self.asian_high, self._high[i])
                self.asian_low = min(self.asian_low, self._low[i])

        # Check for breakout signals during active trading hours (08:00 to 20:00 UTC)
        if 8 <= hour <= 20 and self.asian_high is not None and self.asian_low is not None:
            close_break_high = self._close[i] > self.asian_high
            close_break_low = self._close[i] < self.asian_low
            
            atr = self._atr_14[i]
            
            if close_break_high and (self._close[i] - self.asian_high) < (atr * self.params["breakout_atr_mult"]):
                return {
                    "side": "Long",
                    "stop_loss": self._close[i] - (atr * self.params["sl_atr_mult"]),
                    "take_profit": self._close[i] + (atr * self.params["tp_atr_mult"]),
                    "reason": "Asian session range high breakout"
                }
            elif close_break_low and (self.asian_low - self._close[i]) < (atr * self.params["breakout_atr_mult"]):
                return {
                    "side": "Short",
                    "stop_loss": self._close[i] + (atr * self.params["sl_atr_mult"]),
                    "take_profit": self._close[i] - (atr * self.params["tp_atr_mult"]),
                    "reason": "Asian session range low breakout"
                }

        return None

    def get_param_grid(self) -> dict:
        return {
            "breakout_atr_mult": [0.5, 1.0, 1.5],
            "tp_atr_mult": [2.0, 2.5, 3.0],
            "sl_atr_mult": [1.0, 1.5]
        }


class LiquiditySweepFundingReversal(BaseStrategy):
    """
    Hypothesis: Major swing highs/lows hold stop-loss liquidity. Price often sweeps these levels 
    and reverses, especially near funding rate payments where volatility is high.
    """
    def __init__(self, params: dict = None):
        default_params = {
            "wick_ratio_thresh": 0.45,  # Candle must have a large wick indicating rejection
            "tp_atr_mult": 2.5,
            "sl_atr_mult": 1.5
        }
        if params:
            default_params.update(params)
        super().__init__(
            name="LiquiditySweepFundingReversal",
            hypothesis="Revert when price sweeps a swing high/low near funding hour and gets rejected with a long wick.",
            params=default_params
        )

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        if i < 50:
            return None

        # Cache array references
        if not hasattr(self, "_cached_df_id") or self._cached_df_id != id(df):
            self._cached_df_id = id(df)
            self._close = df["close"].values
            self._high = df["high"].values
            self._low = df["low"].values
            self._open_time = df["open_time"].values
            self._atr_14 = df["atr_14"].values
            self._swing_high = df["swing_high"].values
            self._swing_low = df["swing_low"].values
            self._upper_wick_ratio = df["upper_wick_ratio"].values
            self._lower_wick_ratio = df["lower_wick_ratio"].values
            
            # Pre-calculate hour vectors to avoid pd.to_datetime inside loop
            dts = pd.to_datetime(df["open_time"], unit="ms", utc=True)
            self._hours = dts.dt.hour.values

        hour = self._hours[i]
        near_funding = (hour in [23, 0, 7, 8, 15, 16])

        # Swing levels
        swing_h = self._swing_high[i]
        swing_l = self._swing_low[i]

        if np.isnan(swing_h) or np.isnan(swing_l):
            return None

        # Rejection candle checks
        upper_wick_large = self._upper_wick_ratio[i] >= self.params["wick_ratio_thresh"]
        lower_wick_large = self._lower_wick_ratio[i] >= self.params["wick_ratio_thresh"]

        # Sweep checks
        swept_high_reversal = (self._high[i] > swing_h) and (self._close[i] < swing_h) and upper_wick_large
        swept_low_reversal = (self._low[i] < swing_l) and (self._close[i] > swing_l) and lower_wick_large

        atr = self._atr_14[i]

        if near_funding:
            if swept_low_reversal:
                return {
                    "side": "Long",
                    "stop_loss": self._low[i] - (atr * 0.2), # Just below sweep candle low
                    "take_profit": self._close[i] + (atr * self.params["tp_atr_mult"]),
                    "reason": "Swing Low Liquidity Sweep + Rejection near funding hour"
                }
            elif swept_high_reversal:
                return {
                    "side": "Short",
                    "stop_loss": self._high[i] + (atr * 0.2), # Just above sweep candle high
                    "take_profit": self._close[i] - (atr * self.params["tp_atr_mult"]),
                    "reason": "Swing High Liquidity Sweep + Rejection near funding hour"
                }
        return None

    def get_param_grid(self) -> dict:
        return {
            "wick_ratio_thresh": [0.35, 0.45, 0.55],
            "tp_atr_mult": [2.0, 2.5, 3.0]
        }


class UniversalStrategyTemplate(BaseStrategy):
    """
    Mega Strategy Template supporting 20 trading modules, calibrated regime modes,
    and extensive parameters.
    """
    def __init__(self, params: dict = None):
        default_params = {
            "template_type": "trend_pullback",  # 20 raw modules supported
            "trend_filter": None,               # None, ema_200, sma_50_200
            "regime_filter_mode": "soft",       # no_filter, soft, strict
            "tp_atr_mult": 2.5,
            "sl_atr_mult": 1.5,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "atr_pct_thresh": 0.35,
            "adx_thresh": 20,
            "wick_ratio_thresh": 0.45,
            "funding_threshold": 0.0001,
            "cost_to_atr_mult": 0.0,
            "bb_width_thresh": 0.06,
            "timeframe": None
        }
        if params:
            default_params.update(params)
        super().__init__(
            name="UniversalStrategyTemplate",
            hypothesis=f"Universal template representing strategy type: {default_params['template_type']}.",
            params=default_params
        )
        
        self.last_day = None
        self.asian_high = None
        self.asian_low = None
        self.london_high = None
        self.london_low = None
        self.prior_day_high = None
        self.prior_day_low = None
        self.current_day_high = None
        self.current_day_low = None

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        # Cache array references on first call for this DataFrame to optimize speed
        if not hasattr(self, "_cached_df_id") or self._cached_df_id != id(df):
            self._cached_df_id = id(df)
            self._use_1h = (self.params.get("timeframe") == "1h") or (
                "close_1h" in df.columns and self.params.get("template_type") != "mtf_breakout"
            )
            self._cached_close_time = df["close_time"].values if "close_time" in df.columns else df["open_time"].values + 300000

            def get_col(col_name):
                if self._use_1h:
                    col_1h = f"{col_name}_1h"
                    if col_1h in df.columns:
                        return df[col_1h].values
                return df[col_name].values if col_name in df.columns else None

            self._close = get_col("close")
            self._open = get_col("open")
            self._high = get_col("high")
            self._low = get_col("low")
            self._volume = get_col("volume")
            self._open_time = df["open_time"].values
            self._date_strs = get_col("date_strs") if ("date_strs" in df.columns or "date_strs_1h" in df.columns) else pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.date.astype(str).values
            self._days_of_month = get_col("days_of_month") if ("days_of_month" in df.columns or "days_of_month_1h" in df.columns) else pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.day.values
            self._hours = get_col("hour") if ("hour" in df.columns or "hour_1h" in df.columns) else pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.hour.values
            self._ema_200 = get_col("ema_200")
            self._ema_50 = get_col("ema_50")
            self._atr_pct = get_col("atr_pct")
            self._bb_width = get_col("bb_width")
            self._bb_upper = get_col("bb_upper")
            self._bb_lower = get_col("bb_lower")
            self._bb_mid = get_col("bb_mid")
            self._rsi_14 = get_col("rsi_14")
            self._lower_wick_ratio = get_col("lower_wick_ratio")
            self._upper_wick_ratio = get_col("upper_wick_ratio")
            self._fundingRate = get_col("fundingRate")
            self._atr_14 = get_col("atr_14")
            self._adx = get_col("adx")
            
            # ADX slopes
            self._adx_slope_1 = get_col("adx_slope_1") if get_col("adx_slope_1") is not None else (df["adx"].diff(1).fillna(0.0).values if "adx" in df.columns else None)
            self._adx_slope_3 = get_col("adx_slope_3") if get_col("adx_slope_3") is not None else (df["adx"].diff(3).fillna(0.0).values if "adx" in df.columns else None)
            self._adx_slope_5 = get_col("adx_slope_5") if get_col("adx_slope_5") is not None else (df["adx"].diff(5).fillna(0.0).values if "adx" in df.columns else None)
            
            # Volume Trend
            self._volume_trend = get_col("volume_trend") if get_col("volume_trend") is not None else ((df["volume"] / df["volume"].rolling(20).mean()).fillna(1.0).values if "volume" in df.columns else None)
            
            # 1h Fallbacks for MTF
            self._bb_width_1h = df["bb_width_1h"].values if "bb_width_1h" in df.columns else (self._bb_width if self._bb_width is not None else None)
            self._bb_upper_1h = df["bb_upper_1h"].values if "bb_upper_1h" in df.columns else (self._bb_upper if self._bb_upper is not None else None)
            self._bb_lower_1h = df["bb_lower_1h"].values if "bb_lower_1h" in df.columns else (self._bb_lower if self._bb_lower is not None else None)
            
            # 15m Fallbacks for MTF
            self._close_15m = df["close_15m"].values if "close_15m" in df.columns else None
            self._high_15m = df["high_15m"].values if "high_15m" in df.columns else None
            self._low_15m = df["low_15m"].values if "low_15m" in df.columns else None
            self._bb_upper_15m = df["bb_upper_15m"].values if "bb_upper_15m" in df.columns else None
            self._bb_lower_15m = df["bb_lower_15m"].values if "bb_lower_15m" in df.columns else None
            self._body_ratio_15m = df["body_ratio_15m"].values if "body_ratio_15m" in df.columns else None
            self._body_ratio = get_col("body_ratio")
            self._swing_high = get_col("swing_high")
            self._swing_low = get_col("swing_low")
            self._vwap = get_col("vwap") if ("vwap" in df.columns or "vwap_1h" in df.columns) else None
            
            # 15m columns (safely get them to avoid key errors if single timeframe is run)
            self._close_15m = df["close_15m"].values if "close_15m" in df.columns else None
            self._high_15m = df["high_15m"].values if "high_15m" in df.columns else None
            self._low_15m = df["low_15m"].values if "low_15m" in df.columns else None
            self._bb_upper_15m = df["bb_upper_15m"].values if "bb_upper_15m" in df.columns else None
            self._bb_lower_15m = df["bb_lower_15m"].values if "bb_lower_15m" in df.columns else None
            self._swing_high_15m = df["swing_high_15m"].values if "swing_high_15m" in df.columns else None
            self._swing_low_15m = df["swing_low_15m"].values if "swing_low_15m" in df.columns else None

            # 1h columns
            self._close_1h = df["close_1h"].values if "close_1h" in df.columns else None
            self._high_1h = df["high_1h"].values if "high_1h" in df.columns else None
            self._low_1h = df["low_1h"].values if "low_1h" in df.columns else None
            self._ema_200_1h = df["ema_200_1h"].values if "ema_200_1h" in df.columns else None
            self._regime_bull_trend_1h = df["regime_bull_trend_1h"].values if "regime_bull_trend_1h" in df.columns else None
            self._regime_bear_trend_1h = df["regime_bear_trend_1h"].values if "regime_bear_trend_1h" in df.columns else None
            self._regime_vol_expansion_1h = df["regime_vol_expansion_1h"].values if "regime_vol_expansion_1h" in df.columns else None

            # Regime columns
            self._regime_bull_trend = get_col("regime_bull_trend")
            self._regime_bear_trend = get_col("regime_bear_trend")
            self._regime_sideways_range = get_col("regime_sideways_range")
            self._regime_vol_compression = get_col("regime_vol_compression")
            self._regime_vol_expansion = get_col("regime_vol_expansion")
            self._regime_funding_extreme = get_col("regime_funding_extreme")
            self._regime_toxic_chop = get_col("regime_toxic_chop")

        if self._use_1h:
            # Restrict signal generation to hour boundaries: close_time % 3600000 == 0
            if self._cached_close_time[i] % 3600000 != 0:
                return None

        if i < 200:
            return None

        close_val = self._close[i]
        atr = self._atr_14[i]
        
        # --- 1. REGIME FILTER CALIBRATION ---
        regime_mode = self.params.get("regime_filter_mode", "soft")
        t_type = self.params["template_type"]
        
        # Soft filter: skip toxic chop
        if regime_mode in ["soft", "strict"] and self._regime_toxic_chop is not None:
            if self._regime_toxic_chop[i]:
                return None
                
        # Strict filter: require matching regimes
        if regime_mode == "strict":
            if t_type in ["trend_pullback", "trend_breakout", "london_continuation", "funding_trend_continuation", "volume_impulse_continuation"]:
                if self._regime_bull_trend is not None and self._regime_bear_trend is not None:
                    if not (self._regime_bull_trend[i] or self._regime_bear_trend[i]):
                        return None
            elif t_type in ["bollinger_mean_reversion", "vwap_mean_reversion", "rsi_exhaustion_reversal", "wick_rejection_reversal", "new_york_reversal"]:
                if self._regime_sideways_range is not None and not self._regime_sideways_range[i]:
                    return None
            elif t_type in ["range_compression_breakout"]:
                if self._regime_vol_compression is not None and not self._regime_vol_compression[i]:
                    return None
            elif t_type in ["bollinger_expansion_breakout", "atr_volatility_expansion"]:
                if self._regime_vol_expansion is not None and not self._regime_vol_expansion[i]:
                    return None
            elif t_type in ["funding_extreme_reversal"]:
                if self._regime_funding_extreme is not None and not self._regime_funding_extreme[i]:
                    return None

        # Day transition for Asia Session & Prior Day tracking
        day_str = self._date_strs[i]
        if self.last_day != day_str:
            self.prior_day_high = self.current_day_high
            self.prior_day_low = self.current_day_low
            self.current_day_high = self._high[i]
            self.current_day_low = self._low[i]
            self.last_day = day_str
            self.asian_high = None
            self.asian_low = None
            self.london_high = None
            self.london_low = None
        else:
            if self.current_day_high is None or self._high[i] > self.current_day_high:
                self.current_day_high = self._high[i]
            if self.current_day_low is None or self._low[i] < self.current_day_low:
                self.current_day_low = self._low[i]
            
        dt_hour = self._hours[i]
        if 0 <= dt_hour < 8:
            if self.asian_high is None or self._high[i] > self.asian_high:
                self.asian_high = self._high[i]
            if self.asian_low is None or self._low[i] < self.asian_low:
                self.asian_low = self._low[i]
                
        if 8 <= dt_hour < 13:
            if self.london_high is None or self._high[i] > self.london_high:
                self.london_high = self._high[i]
            if self.london_low is None or self._low[i] < self.london_low:
                self.london_low = self._low[i]

        # Trend Filter
        trend_long = True
        trend_short = True
        if self.params["trend_filter"] == "ema_200":
            trend_long = close_val > self._ema_200[i]
            trend_short = close_val < self._ema_200[i]
        elif self.params["trend_filter"] == "sma_50_200":
            trend_long = self._ema_50[i] > self._ema_200[i]
            trend_short = self._ema_50[i] < self._ema_200[i]

        # Trigger logic for the 20 raw modules
        side = None
        reason = ""
        stop_loss = 0.0
        take_profit = 0.0
        
        # 1. Trend Pullback
        if t_type == "trend_pullback":
            near_ema50_long = self._low[i] <= self._ema_50[i] and close_val > self._ema_50[i]
            near_ema50_short = self._high[i] >= self._ema_50[i] and close_val < self._ema_50[i]
            if trend_long and near_ema50_long and self._adx[i] >= self.params["adx_thresh"]:
                side = "Long"
                reason = "Trend Pullback Long"
            elif trend_short and near_ema50_short and self._adx[i] >= self.params["adx_thresh"]:
                side = "Short"
                reason = "Trend Pullback Short"
                
        # 2. Trend Breakout
        elif t_type == "trend_breakout":
            if trend_long and close_val > self._swing_high[i]:
                side = "Long"
                reason = "Trend Breakout Long"
            elif trend_short and close_val < self._swing_low[i]:
                side = "Short"
                reason = "Trend Breakout Short"
                
        # 3. Breakout Retest
        elif t_type == "breakout_retest":
            if trend_long and self._high[i-1] > self._bb_upper[i-1] and self._low[i] <= self._bb_mid[i] and close_val > self._bb_mid[i]:
                side = "Long"
                reason = "Breakout Retest Long"
            elif trend_short and self._low[i-1] < self._bb_lower[i-1] and self._high[i] >= self._bb_mid[i] and close_val < self._bb_mid[i]:
                side = "Short"
                reason = "Breakout Retest Short"
                
        # 4. Failed Breakout Reversal
        elif t_type == "failed_breakout_reversal":
            if self._low[i] < self._bb_lower[i] and close_val > self._bb_lower[i] and self._lower_wick_ratio[i] >= self.params["wick_ratio_thresh"]:
                side = "Long"
                reason = "Failed Breakout Reversal Long"
            elif self._high[i] > self._bb_upper[i] and close_val < self._bb_upper[i] and self._upper_wick_ratio[i] >= self.params["wick_ratio_thresh"]:
                side = "Short"
                reason = "Failed Breakout Reversal Short"
                
        # 5. Sweep Reversal
        elif t_type == "sweep_reversal":
            near_funding = (dt_hour in [23, 0, 7, 8, 15, 16])
            if near_funding and not np.isnan(self._swing_low[i]) and self._low[i] < self._swing_low[i] and close_val > self._swing_low[i]:
                side = "Long"
                reason = "Sweep Reversal Long"
            elif near_funding and not np.isnan(self._swing_high[i]) and self._high[i] > self._swing_high[i] and close_val < self._swing_high[i]:
                side = "Short"
                reason = "Sweep Reversal Short"
                
        # 6. VWAP Mean Reversion
        elif t_type == "vwap_mean_reversion":
            if close_val < self._bb_lower[i] and close_val < self._bb_mid[i] - (atr * 1.5) and self._rsi_14[i] < self.params["rsi_oversold"]:
                side = "Long"
                reason = "VWAP MR Long"
                take_profit = self._bb_mid[i]
            elif close_val > self._bb_upper[i] and close_val > self._bb_mid[i] + (atr * 1.5) and self._rsi_14[i] > self.params["rsi_overbought"]:
                side = "Short"
                reason = "VWAP MR Short"
                take_profit = self._bb_mid[i]
                
        # 7. Bollinger Mean Reversion
        elif t_type == "bollinger_mean_reversion":
            if close_val < self._bb_lower[i] and self._rsi_14[i] < self.params["rsi_oversold"]:
                side = "Long"
                reason = "Bollinger MR Long"
                take_profit = self._bb_mid[i]
            elif close_val > self._bb_upper[i] and self._rsi_14[i] > self.params["rsi_overbought"]:
                side = "Short"
                reason = "Bollinger MR Short"
                take_profit = self._bb_mid[i]
                
        # 8. Bollinger Expansion Breakout
        elif t_type == "bollinger_expansion_breakout":
            if self.params.get("wire_parameters", False):
                # Apply full wired logic
                bb_w_thresh = self.params.get("bb_width_thresh", 0.06)
                adx_thresh = self.params.get("adx_thresh", 20)
                
                # ADX filter check
                adx_ok = self._adx[i] >= adx_thresh if self._adx is not None else True
                
                # RSI filter check
                rsi_val = self._rsi_14[i] if self._rsi_14 is not None else 50
                rsi_long_ok = rsi_val <= self.params.get("rsi_overbought", 75)
                rsi_short_ok = rsi_val >= self.params.get("rsi_oversold", 30)

                # Wick rejection check
                upper_wick = self._upper_wick_ratio[i] if self._upper_wick_ratio is not None else 0.0
                lower_wick = self._lower_wick_ratio[i] if self._lower_wick_ratio is not None else 0.0
                wick_limit = self.params.get("wick_ratio_thresh", 0.45)
                wick_long_ok = upper_wick <= wick_limit
                wick_short_ok = lower_wick <= wick_limit

                # Volume confirmation check
                vol_mult = self.params.get("volume_trend_thresh", 1.0)
                vol_ok = self._volume_trend[i] >= vol_mult if self._volume_trend is not None else True

                # Funding extreme skip check
                fund_thresh = self.params.get("funding_threshold", 0.0005)
                fund_ok = abs(self._fundingRate[i]) <= fund_thresh if self._fundingRate is not None else True

                # Session filter check
                allowed_hours = self.params.get("allowed_hours", list(range(24)))
                session_ok = self._hours[i] in allowed_hours

                # Retest Mid-Band Quality check
                retest_depth = self.params.get("retest_depth", 0.0)
                retest_ok = True
                if retest_depth > 0.0:
                    retest_ok = False
                    for k in range(1, 6):
                        if close_val > self._bb_upper[i]:
                            # Long retest check
                            if self._low[max(0, i-k)] <= self._bb_mid[max(0, i-k)] + (atr * retest_depth):
                                retest_ok = True
                                break
                        else:
                            # Short retest check
                            if self._high[max(0, i-k)] >= self._bb_mid[max(0, i-k)] - (atr * retest_depth):
                                retest_ok = True
                                break

                # Trigger Signal
                if self._bb_width[i] > bb_w_thresh and adx_ok and fund_ok and session_ok and retest_ok:
                    if close_val > self._bb_upper[i] and trend_long and rsi_long_ok and wick_long_ok and vol_ok:
                        side = "Long"
                        reason = "BB Expansion Long (Wired)"
                    elif close_val < self._bb_lower[i] and trend_short and rsi_short_ok and wick_short_ok and vol_ok:
                        side = "Short"
                        reason = "BB Expansion Short (Wired)"
            else:
                bb_w_thresh = self.params.get("bb_width_thresh", 0.06)
                if self._bb_width[i] > bb_w_thresh and close_val > self._bb_upper[i] and trend_long:
                    side = "Long"
                    reason = "BB Expansion Long"
                elif self._bb_width[i] > bb_w_thresh and close_val < self._bb_lower[i] and trend_short:
                    side = "Short"
                    reason = "BB Expansion Short"
                
        # 8a. Bollinger Expansion Original (Preserves baseline exactly)
        elif t_type == "bollinger_expansion_original":
            bb_w_thresh = self.params.get("bb_width_thresh", 0.06)
            if self._bb_width[i] > bb_w_thresh and close_val > self._bb_upper[i] and trend_long:
                side = "Long"
                reason = "BB Expansion Original Long"
            elif self._bb_width[i] > bb_w_thresh and close_val < self._bb_lower[i] and trend_short:
                side = "Short"
                reason = "BB Expansion Original Short"
                
        # 8b. Bollinger Expansion Refined (ADX Slope & Volume Trend)
        elif t_type == "bollinger_expansion_refined":
            adx_slope_win = self.params.get("adx_slope_window", 3)
            adx_slope_thresh = self.params.get("adx_slope_thresh", 0.0)
            if adx_slope_win == 1:
                slope_val = self._adx_slope_1[i]
            elif adx_slope_win == 5:
                slope_val = self._adx_slope_5[i]
            else:
                slope_val = self._adx_slope_3[i]
            adx_slope_ok = slope_val >= adx_slope_thresh if slope_val is not None else True
            
            vol_trend_thresh = self.params.get("volume_trend_thresh", 1.0)
            vol_trend_ok = self._volume_trend[i] >= vol_trend_thresh if self._volume_trend is not None else True
            
            bb_w_thresh = self.params.get("bb_width_thresh", 0.06)
            if self._bb_width[i] > bb_w_thresh and close_val > self._bb_upper[i] and trend_long and adx_slope_ok and vol_trend_ok:
                side = "Long"
                reason = "BB Expansion Refined Long"
            elif self._bb_width[i] > bb_w_thresh and close_val < self._bb_lower[i] and trend_short and adx_slope_ok and vol_trend_ok:
                side = "Short"
                reason = "BB Expansion Refined Short"
                
        # 8c. Bollinger Expansion 15m Confirmed
        elif t_type == "bollinger_expansion_15m_confirmed":
            conf_mode = self.params.get("confirmation_mode", "close_confirm")
            use_15m = self.params.get("use_15m_confirmation", True)
            
            conf_long = True
            conf_short = True
            
            if use_15m and self._close_15m is not None:
                close_15m = self._close_15m[i]
                bb_upper_15m = self._bb_upper_15m[i]
                bb_lower_15m = self._bb_lower_15m[i]
                
                if conf_mode == "close_confirm" and bb_upper_15m is not None and bb_lower_15m is not None:
                    conf_long = close_15m > bb_upper_15m
                    conf_short = close_15m < bb_lower_15m
                elif conf_mode == "retest_reclaim" and bb_upper_15m is not None and bb_lower_15m is not None:
                    low_15m = self._low_15m[i]
                    high_15m = self._high_15m[i]
                    conf_long = low_15m <= bb_upper_15m and close_15m > bb_upper_15m
                    conf_short = high_15m >= bb_lower_15m and close_15m < bb_lower_15m
                elif conf_mode == "body_strength" and self._body_ratio_15m is not None:
                    body_limit = self.params.get("body_strength_thresh", 0.6)
                    conf_long = self._body_ratio_15m[i] >= body_limit and close_15m > bb_upper_15m
                    conf_short = self._body_ratio_15m[i] >= body_limit and close_15m < bb_lower_15m
                    
            bb_w_thresh = self.params.get("bb_width_thresh", 0.06)
            if self._bb_width[i] > bb_w_thresh and close_val > self._bb_upper[i] and trend_long and conf_long:
                side = "Long"
                reason = "BB Expansion 15m Confirmed Long"
            elif self._bb_width[i] > bb_w_thresh and close_val < self._bb_lower[i] and trend_short and conf_short:
                side = "Short"
                reason = "BB Expansion 15m Confirmed Short"
                
        # 8d. Bollinger Expansion Volume & ADX Filtered
        elif t_type == "bollinger_expansion_volume_adx_filtered":
            adx_slope_ok = self._adx_slope_3[i] >= self.params.get("adx_slope_thresh", 0.0) if self._adx_slope_3 is not None else True
            vol_trend_ok = self._volume_trend[i] >= self.params.get("volume_trend_thresh", 1.2) if self._volume_trend is not None else True
            
            bb_w_thresh = self.params.get("bb_width_thresh", 0.06)
            if self._bb_width[i] > bb_w_thresh and close_val > self._bb_upper[i] and trend_long and adx_slope_ok and vol_trend_ok:
                side = "Long"
                reason = "BB Expansion Vol ADX Long"
            elif self._bb_width[i] > bb_w_thresh and close_val < self._bb_lower[i] and trend_short and adx_slope_ok and vol_trend_ok:
                side = "Short"
                reason = "BB Expansion Vol ADX Short"
                
        # 9. ATR Volatility Expansion
        elif t_type == "atr_volatility_expansion":
            if self._atr_pct[i] > 0.75 and close_val > self._ema_50[i] and self._close[i-1] <= self._ema_50[i-1]:
                side = "Long"
                reason = "ATR Expansion Long"
            elif self._atr_pct[i] > 0.75 and close_val < self._ema_50[i] and self._close[i-1] >= self._ema_50[i-1]:
                side = "Short"
                reason = "ATR Expansion Short"
                
        # 10. Range Compression Breakout
        elif t_type == "range_compression_breakout":
            if self._bb_width[i] < 0.035 and close_val > self._bb_upper[i] and trend_long:
                side = "Long"
                reason = "Range Compression Long"
            elif self._bb_width[i] < 0.035 and close_val < self._bb_lower[i] and trend_short:
                side = "Short"
                reason = "Range Compression Short"
                
        # 11. Asia Range Breakout
        elif t_type == "asia_range_breakout":
            if dt_hour >= 8 and self.asian_high is not None and close_val > self.asian_high and self._close[i-1] <= self.asian_high:
                side = "Long"
                reason = "Asia Breakout Long"
            elif dt_hour >= 8 and self.asian_low is not None and close_val < self.asian_low and self._close[i-1] >= self.asian_low:
                side = "Short"
                reason = "Asia Breakout Short"
                
        # 12. Asia Range Failure
        elif t_type == "asia_range_failure":
            if dt_hour >= 8 and self.asian_low is not None and self._low[i] < self.asian_low and close_val > self.asian_low:
                side = "Long"
                reason = "Asia Failure Long"
            elif dt_hour >= 8 and self.asian_high is not None and self._high[i] > self.asian_high and close_val < self.asian_high:
                side = "Short"
                reason = "Asia Failure Short"
                
        # 13. London Continuation
        elif t_type == "london_continuation":
            if 8 <= dt_hour < 16:
                if trend_long and close_val > self._ema_50[i]:
                    side = "Long"
                    reason = "London Continuation Long"
                elif trend_short and close_val < self._ema_50[i]:
                    side = "Short"
                    reason = "London Continuation Short"
                    
        # 14. New York Reversal
        elif t_type == "new_york_reversal":
            if 13 <= dt_hour < 21:
                if self._rsi_14[i] < 28:
                    side = "Long"
                    reason = "NY Reversal Long"
                elif self._rsi_14[i] > 72:
                    side = "Short"
                    reason = "NY Reversal Short"
                    
        # 15. Funding Extreme Reversal
        elif t_type == "funding_extreme_reversal":
            if self._fundingRate[i] < -0.0003 and self._rsi_14[i] < 40:
                side = "Long"
                reason = "Funding Reversal Long"
            elif self._fundingRate[i] > 0.0003 and self._rsi_14[i] > 60:
                side = "Short"
                reason = "Funding Reversal Short"
                
        # 16. Funding Trend Continuation
        elif t_type == "funding_trend_continuation":
            if self._fundingRate[i] > 0.0001 and trend_long:
                side = "Long"
                reason = "Funding Trend Long"
            elif self._fundingRate[i] < -0.0001 and trend_short:
                side = "Short"
                reason = "Funding Trend Short"
                
        # 17. RSI Exhaustion Reversal
        elif t_type == "rsi_exhaustion_reversal":
            if self._rsi_14[i] < 20:
                side = "Long"
                reason = "RSI Exhaustion Long"
            elif self._rsi_14[i] > 80:
                side = "Short"
                reason = "RSI Exhaustion Short"
                
        # 18. Wick Rejection Reversal
        elif t_type == "wick_rejection_reversal":
            if self._lower_wick_ratio[i] >= 0.55 and self._low[i] <= self._bb_lower[i]:
                side = "Long"
                reason = "Wick Rejection Long"
            elif self._upper_wick_ratio[i] >= 0.55 and self._high[i] >= self._bb_upper[i]:
                side = "Short"
                reason = "Wick Rejection Short"
                
        # 19. Volume Impulse Continuation
        elif t_type == "volume_impulse_continuation":
            vol_ma = self._volume[max(0, i-20):i].mean() if i > 0 else self._volume[i]
            vol_ok = self._volume[i] > 1.8 * vol_ma
            if vol_ok and trend_long:
                side = "Long"
                reason = "Volume Impulse Long"
            elif vol_ok and trend_short:
                side = "Short"
                reason = "Volume Impulse Short"
                
        # 20. Swing Structure Continuation
        elif t_type == "swing_structure_continuation":
            if not np.isnan(self._swing_high[i]) and close_val > self._swing_high[i]:
                side = "Long"
                reason = "Swing Structure Long"
            elif not np.isnan(self._swing_low[i]) and close_val < self._swing_low[i]:
                side = "Short"
                reason = "Swing Structure Short"
                
        # 21. Low Activity Filler (Trend Reclaim Reversion)
        elif t_type == "low_activity_filler":
            monthly_trades = live_metrics.get("monthly_trade_count", 0) if live_metrics else 0
            day_of_month = self._days_of_month[i]
            if (day_of_month >= 10 and monthly_trades == 0) or (day_of_month >= 15 and monthly_trades < 6):
                trend_long = close_val > self._ema_200[i]
                trend_short = close_val < self._ema_200[i]
                
                # Check for lower/upper BB reclaim
                if trend_long and self._low[i] <= self._bb_lower[i] and close_val > self._bb_lower[i] and self._rsi_14[i] < 35:
                    side = "Long"
                    reason = "Low-Activity Filler Long"
                    stop_loss = close_val - (atr * self.params.get("sl_atr_mult", 2.0))
                    take_profit = close_val + (atr * self.params.get("tp_atr_mult", 3.5))
                elif trend_short and self._high[i] >= self._bb_upper[i] and close_val < self._bb_upper[i] and self._rsi_14[i] > 65:
                    side = "Short"
                    reason = "Low-Activity Filler Short"
                    stop_loss = close_val + (atr * self.params.get("sl_atr_mult", 2.0))
                    take_profit = close_val - (atr * self.params.get("tp_atr_mult", 3.5))

        # 22. MTF Breakout Strategy
        elif t_type == "mtf_breakout":
            # 1h regime filters
            regime_bull_1h = self._regime_bull_trend_1h[i] if (hasattr(self, "_regime_bull_trend_1h") and self._regime_bull_trend_1h is not None) else False
            regime_bear_1h = self._regime_bear_trend_1h[i] if (hasattr(self, "_regime_bear_trend_1h") and self._regime_bear_trend_1h is not None) else False
            regime_vol_1h = self._regime_vol_expansion_1h[i] if (hasattr(self, "_regime_vol_expansion_1h") and self._regime_vol_expansion_1h is not None) else False
            
            # Trend Filter
            ema_200_1h_val = self._ema_200_1h[i] if (hasattr(self, "_ema_200_1h") and self._ema_200_1h is not None) else close_val
            trend_long_1h = regime_bull_1h or regime_vol_1h or (close_val >= ema_200_1h_val)
            trend_short_1h = regime_bear_1h or regime_vol_1h or (close_val <= ema_200_1h_val)
            
            # 15m breakout levels
            bb_upper_15m_val = self._bb_upper_15m[i] if (hasattr(self, "_bb_upper_15m") and self._bb_upper_15m is not None) else None
            bb_lower_15m_val = self._bb_lower_15m[i] if (hasattr(self, "_bb_lower_15m") and self._bb_lower_15m is not None) else None
            close_15m_val = self._close_15m[i] if (hasattr(self, "_close_15m") and self._close_15m is not None) else None
            high_15m_val = self._high_15m[i] if (hasattr(self, "_high_15m") and self._high_15m is not None) else None
            low_15m_val = self._low_15m[i] if (hasattr(self, "_low_15m") and self._low_15m is not None) else None
            
            # Safe guards if multi-timeframe inputs are not aligned
            if bb_upper_15m_val is not None and bb_lower_15m_val is not None and close_15m_val is not None:
                atr_5m = atr
                wick_thresh = self.params.get("wick_ratio_thresh", 0.45)
                
                # Check for 15m Breakout Setup
                breakout_long_setup = close_15m_val > bb_upper_15m_val
                breakout_short_setup = close_15m_val < bb_lower_15m_val
                
                # Tighter stop-loss calculation
                sl_atr_mult = self.params.get("sl_atr_mult", 1.5)
                swing_low_5m = self._swing_low[i]
                swing_high_5m = self._swing_high[i]
                
                long_sl = close_val - (atr_5m * sl_atr_mult)
                if not np.isnan(swing_low_5m):
                    long_sl = max(long_sl, swing_low_5m)
                    
                short_sl = close_val + (atr_5m * sl_atr_mult)
                if not np.isnan(swing_high_5m):
                    short_sl = min(short_sl, swing_high_5m)
                    
                # Default TP
                tp_atr_mult = self.params.get("tp_atr_mult", 2.5)
                long_tp = close_val + (atr_5m * tp_atr_mult)
                short_tp = close_val - (atr_5m * tp_atr_mult)
                
                # --- 1. Delayed Confirmation Breakout Entry ---
                confirm_candles = self.params.get("confirm_candles", 2)
                if confirm_candles <= i:
                    if trend_long_1h and breakout_long_setup:
                        if all(self._close[i - k] > bb_upper_15m_val for k in range(confirm_candles)):
                            side = "Long"
                            reason = "MTF Breakout Confirmed Long"
                            stop_loss = long_sl
                            take_profit = long_tp
                    elif trend_short_1h and breakout_short_setup:
                        if all(self._close[i - k] < bb_lower_15m_val for k in range(confirm_candles)):
                            side = "Short"
                            reason = "MTF Breakout Confirmed Short"
                            stop_loss = short_sl
                            take_profit = short_tp
                
                # --- 2. Failed Breakout Reversal Entry ---
                if side is None and high_15m_val is not None and low_15m_val is not None:
                    failed_upside_breakout = (high_15m_val > bb_upper_15m_val) and (close_15m_val <= bb_upper_15m_val)
                    if failed_upside_breakout and self._upper_wick_ratio[i] >= wick_thresh and close_val < bb_upper_15m_val:
                        side = "Short"
                        reason = "MTF Failed Breakout Reversal Short"
                        stop_loss = short_sl
                        take_profit = short_tp
                        
                    failed_downside_breakout = (low_15m_val < bb_lower_15m_val) and (close_15m_val >= bb_lower_15m_val)
                    if failed_downside_breakout and self._lower_wick_ratio[i] >= wick_thresh and close_val > bb_lower_15m_val:
                        side = "Long"
                        reason = "MTF Failed Breakout Reversal Long"
                        stop_loss = long_sl
                        take_profit = long_tp
                
                # --- 3. Retest Entry ---
                if side is None:
                    if trend_long_1h and breakout_long_setup:
                        retest_low = self._low[i] <= bb_upper_15m_val
                        retest_close = close_val > bb_upper_15m_val
                        if retest_low and retest_close and self._lower_wick_ratio[i] >= wick_thresh:
                            side = "Long"
                            reason = "MTF Breakout Retest Long"
                            stop_loss = long_sl
                            take_profit = long_tp
                    elif trend_short_1h and breakout_short_setup:
                        retest_high = self._high[i] >= bb_lower_15m_val
                        retest_close = close_val < bb_lower_15m_val
                        if retest_high and retest_close and self._upper_wick_ratio[i] >= wick_thresh:
                            side = "Short"
                            reason = "MTF Breakout Retest Short"
                            stop_loss = short_sl
                            take_profit = short_tp

        # =================================================================
        # PHASE 11 NEW TEMPLATES
        # =================================================================

        # P11-A: Trend Pullback EMA Reclaim
        # Hypothesis: After a BB expansion breakout on bar i-1, wait for price to pull back
        # to EMA(50) and reclaim it from the breakout side. Gives tighter stop.
        elif t_type == "trend_pullback_ema_reclaim":
            if i >= 2 and self._ema_50 is not None and self._bb_upper is not None:
                prev_broke_upper = (self._close[i - 1] > self._bb_upper[i - 1]) and (self._bb_width[i - 1] > 0.06)
                prev_broke_lower = (self._close[i - 1] < self._bb_lower[i - 1]) and (self._bb_width[i - 1] > 0.06)
                # Current bar: dip to EMA50 and close above it (long) or bounce to EMA50 and close below it (short)
                ema_reclaim_long = (
                    prev_broke_upper and
                    trend_long and
                    self._low[i] <= self._ema_50[i] and
                    close_val > self._ema_50[i] and
                    self._adx[i] >= self.params.get("adx_thresh", 20)
                )
                ema_reclaim_short = (
                    prev_broke_lower and
                    trend_short and
                    self._high[i] >= self._ema_50[i] and
                    close_val < self._ema_50[i] and
                    self._adx[i] >= self.params.get("adx_thresh", 20)
                )
                if ema_reclaim_long:
                    side = "Long"
                    reason = "Trend Pullback EMA Reclaim Long"
                    stop_loss = self._ema_50[i] - (atr * self.params.get("sl_atr_mult", 1.5))
                    take_profit = close_val + (atr * self.params.get("tp_atr_mult", 2.5))
                elif ema_reclaim_short:
                    side = "Short"
                    reason = "Trend Pullback EMA Reclaim Short"
                    stop_loss = self._ema_50[i] + (atr * self.params.get("sl_atr_mult", 1.5))
                    take_profit = close_val - (atr * self.params.get("tp_atr_mult", 2.5))

        # P11-B: VWAP Reclaim Continuation
        # Hypothesis: Price returns above/below VWAP after being flushed through it.
        # Activated in zero-rescue mode only (low monthly activity).
        elif t_type == "vwap_reclaim_continuation":
            if self._vwap is not None:
                monthly_trades = live_metrics.get("monthly_trade_count", 0) if live_metrics else 0
                day_of_month = self._days_of_month[i]
                rescue_active = (day_of_month >= 10 and monthly_trades == 0) or (day_of_month >= 15 and monthly_trades < 4)
                if rescue_active:
                    vwap_val = self._vwap[i]
                    if not np.isnan(vwap_val):
                        # Long: previous bar was below VWAP, current bar closes above VWAP with RSI > 45
                        vwap_reclaim_long = (
                            self._close[i - 1] < vwap_val and
                            close_val > vwap_val and
                            self._rsi_14[i] > 45 and
                            trend_long
                        )
                        # Short: previous bar was above VWAP, current bar closes below VWAP with RSI < 55
                        vwap_reclaim_short = (
                            self._close[i - 1] > vwap_val and
                            close_val < vwap_val and
                            self._rsi_14[i] < 55 and
                            trend_short
                        )
                        if vwap_reclaim_long:
                            side = "Long"
                            reason = "VWAP Reclaim Long (Zero Rescue)"
                            stop_loss = close_val - (atr * self.params.get("sl_atr_mult", 2.0))
                            take_profit = close_val + (atr * self.params.get("tp_atr_mult", 3.0))
                        elif vwap_reclaim_short:
                            side = "Short"
                            reason = "VWAP Reclaim Short (Zero Rescue)"
                            stop_loss = close_val + (atr * self.params.get("sl_atr_mult", 2.0))
                            take_profit = close_val - (atr * self.params.get("tp_atr_mult", 3.0))

        # P11-C: Volatility Compression Release
        # Hypothesis: When BB width is below the 20th percentile for 5+ consecutive bars
        # (compression), and price then closes outside the band, the release trade follows.
        elif t_type == "volatility_compression_release":
            if self._atr_pct is not None and self._bb_width is not None:
                # Measure how many consecutive bars BB width has been compressed (< 20th pct = atr_pct < 0.25)
                compression_bars = 0
                for k in range(1, min(8, i)):
                    if self._bb_width[i - k] < 0.035:  # tight band threshold
                        compression_bars += 1
                    else:
                        break
                # Release: at least 5 bars of compression, then current bar breaks out
                min_compress = self.params.get("min_compression_bars", 5)
                if compression_bars >= min_compress:
                    if close_val > self._bb_upper[i] and trend_long:
                        side = "Long"
                        reason = "Volatility Compression Release Long"
                    elif close_val < self._bb_lower[i] and trend_short:
                        side = "Short"
                        reason = "Volatility Compression Release Short"

        # P11-D: ADX Slope Momentum Continuation
        # Hypothesis: When ADX is rising steeply (slope > thresh over 5 bars) and
        # price is on the trend side of EMA(50), momentum is accelerating.
        elif t_type == "adx_slope_momentum_continuation":
            if self._adx is not None and self._adx_slope_5 is not None and self._ema_50 is not None:
                adx_slope_thresh = self.params.get("adx_slope_thresh", 2.0)
                adx_min = self.params.get("adx_thresh", 25)
                slope_strong = self._adx_slope_5[i] >= adx_slope_thresh
                adx_active = self._adx[i] >= adx_min
                if slope_strong and adx_active:
                    if trend_long and close_val > self._ema_50[i]:
                        side = "Long"
                        reason = "ADX Slope Momentum Long"
                    elif trend_short and close_val < self._ema_50[i]:
                        side = "Short"
                        reason = "ADX Slope Momentum Short"

        # P11-E: Range Failure Reversal
        # Hypothesis: In the first 4 hours of trading (0-4h UTC), if price spikes above
        # the prior session high (or below session low) and reverses, it is a failed
        # breakout / range failure. Entry is in the direction of the reversal.
        elif t_type == "range_failure_reversal":
            if self._swing_high is not None and self._swing_low is not None:
                hour_val = self._hours[i]
                # Active during London/NY overlap and early sessions only (8-16 UTC)
                session_active = 8 <= hour_val < 16
                if session_active and not np.isnan(self._swing_high[i]) and not np.isnan(self._swing_low[i]):
                    # Failed upside break: spike above swing high then close back inside
                    failed_up = (
                        self._high[i] > self._swing_high[i] and
                        close_val < self._swing_high[i] and
                        self._upper_wick_ratio[i] >= self.params.get("wick_ratio_thresh", 0.45)
                    )
                    # Failed downside break: spike below swing low then close back inside
                    failed_down = (
                        self._low[i] < self._swing_low[i] and
                        close_val > self._swing_low[i] and
                        self._lower_wick_ratio[i] >= self.params.get("wick_ratio_thresh", 0.45)
                    )
                    if failed_up:
                        side = "Short"
                        reason = "Range Failure Reversal Short"
                        stop_loss = self._high[i] + (atr * 0.2)
                        take_profit = close_val - (atr * self.params.get("tp_atr_mult", 2.5))
                    elif failed_down:
                        side = "Long"
                        reason = "Range Failure Reversal Long"
                        stop_loss = self._low[i] - (atr * 0.2)
                        take_profit = close_val + (atr * self.params.get("tp_atr_mult", 2.5))

        # =================================================================
        # PHASE 12 ORTHOGONAL TEMPLATES
        # =================================================================

        # A1. Asian Range Mean Reversion
        elif t_type == "asian_range_mean_reversion":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i]) and (self._adx[i] < 20)
            if is_mr_regime and dt_hour >= 8 and self.asian_high is not None and self.asian_low is not None:
                if self._low[i] <= self.asian_low and close_val > self.asian_low and self._rsi_14[i] < 40:
                    side = "Long"
                    reason = "Asian Mean Reversion Long"
                    stop_loss = self.asian_low - (atr * 1.5)
                    take_profit = (self.asian_high + self.asian_low) / 2.0
                elif self._high[i] >= self.asian_high and close_val < self.asian_high and self._rsi_14[i] > 60:
                    side = "Short"
                    reason = "Asian Mean Reversion Short"
                    stop_loss = self.asian_high + (atr * 1.5)
                    take_profit = (self.asian_high + self.asian_low) / 2.0

        # A2. London Breakout Failure
        elif t_type == "london_breakout_failure":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i])
            if is_mr_regime and 8 <= dt_hour < 12 and self.asian_high is not None and self.asian_low is not None:
                if self._high[i] > self.asian_high and close_val < self.asian_high and self._upper_wick_ratio[i] >= 0.50:
                    side = "Short"
                    reason = "London Breakout Failure Short"
                    stop_loss = self._high[i] + (atr * 0.2)
                    take_profit = close_val - (atr * 2.5)
                elif self._low[i] < self.asian_low and close_val > self.asian_low and self._lower_wick_ratio[i] >= 0.50:
                    side = "Long"
                    reason = "London Breakout Failure Long"
                    stop_loss = self._low[i] - (atr * 0.2)
                    take_profit = close_val + (atr * 2.5)

        # A3. NY Open Sweep and Reclaim
        elif t_type == "ny_open_sweep_reclaim":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i])
            if is_mr_regime and 13 <= dt_hour < 16 and self.london_high is not None and self.london_low is not None:
                if self._high[i] > self.london_high and close_val < self.london_high and self._upper_wick_ratio[i] >= 0.50:
                    side = "Short"
                    reason = "NY Sweep Reclaim Short"
                    stop_loss = self._high[i] + (atr * 0.2)
                    take_profit = close_val - (atr * 2.5)
                elif self._low[i] < self.london_low and close_val > self.london_low and self._lower_wick_ratio[i] >= 0.50:
                    side = "Long"
                    reason = "NY Sweep Reclaim Long"
                    stop_loss = self._low[i] - (atr * 0.2)
                    take_profit = close_val + (atr * 2.5)

        # B1. Prior Day High/Low Sweep and Reclaim
        elif t_type == "prior_day_sweep_reclaim":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i])
            if is_mr_regime and self.prior_day_high is not None and self.prior_day_low is not None:
                if self._low[i] < self.prior_day_low and close_val > self.prior_day_low and self._lower_wick_ratio[i] >= 0.50:
                    side = "Long"
                    reason = "Prior Day Sweep Reclaim Long"
                    stop_loss = self._low[i] - (atr * 0.2)
                    take_profit = close_val + (atr * self.params.get("tp_atr_mult", 2.5))
                elif self._high[i] > self.prior_day_high and close_val < self.prior_day_high and self._upper_wick_ratio[i] >= 0.50:
                    side = "Short"
                    reason = "Prior Day Sweep Reclaim Short"
                    stop_loss = self._high[i] + (atr * 0.2)
                    take_profit = close_val - (atr * self.params.get("tp_atr_mult", 2.5))

        # B2. Swing High/Low Sweep Reversal
        elif t_type == "swing_high_low_sweep":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i])
            if is_mr_regime and not np.isnan(self._swing_high[i]) and not np.isnan(self._swing_low[i]):
                if self._low[i] < self._swing_low[i] and close_val > self._swing_low[i] and self._lower_wick_ratio[i] >= 0.50:
                    side = "Long"
                    reason = "Swing Sweep Long"
                    stop_loss = self._low[i] - (atr * 0.2)
                    take_profit = close_val + (atr * 2.5)
                elif self._high[i] > self._swing_high[i] and close_val < self._swing_high[i] and self._upper_wick_ratio[i] >= 0.50:
                    side = "Short"
                    reason = "Swing Sweep Short"
                    stop_loss = self._high[i] + (atr * 0.2)
                    take_profit = close_val - (atr * 2.5)

        # B3. Wick Rejection Stop Run
        elif t_type == "wick_rejection_stop_run":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i])
            if is_mr_regime and self._bb_upper is not None and self._bb_lower is not None:
                if self._low[i] <= self._bb_lower[i] and self._lower_wick_ratio[i] >= 0.55:
                    side = "Long"
                    reason = "Wick Rejection Stop Run Long"
                    stop_loss = self._low[i] - (atr * 0.2)
                    take_profit = close_val + (atr * 2.5)
                elif self._high[i] >= self._bb_upper[i] and self._upper_wick_ratio[i] >= 0.55:
                    side = "Short"
                    reason = "Wick Rejection Stop Run Short"
                    stop_loss = self._high[i] + (atr * 0.2)
                    take_profit = close_val - (atr * 2.5)

        # B4. Failed Breakdown Reversal
        elif t_type == "failed_breakdown_reversal":
            if i >= 2 and self._bb_lower is not None and self._bb_upper is not None:
                is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i])
                if is_mr_regime:
                    if self._close[i-1] < self._bb_lower[i-1] and close_val > self._bb_lower[i] and self._lower_wick_ratio[i] >= 0.50:
                        side = "Long"
                        reason = "Failed Breakdown Reversal Long"
                        stop_loss = self._low[i] - (atr * 0.2)
                        take_profit = close_val + (atr * 2.5)
                    elif self._close[i-1] > self._bb_upper[i-1] and close_val < self._bb_upper[i] and self._upper_wick_ratio[i] >= 0.50:
                        side = "Short"
                        reason = "Failed Breakout Reversal Short"
                        stop_loss = self._high[i] + (atr * 0.2)
                        take_profit = close_val - (atr * 2.5)

        # C1. Funding Divergence Reversal
        elif t_type == "funding_divergence":
            if self._fundingRate is not None:
                is_funding_regime = self._regime_funding_extreme[i] or self._regime_sideways_range[i]
                if is_funding_regime:
                    lowest_close_10 = self._close[max(0, i-10):i].min()
                    highest_close_10 = self._close[max(0, i-10):i].max()
                    funding_min_10 = self._fundingRate[max(0, i-10):i].min()
                    funding_max_10 = self._fundingRate[max(0, i-10):i].max()
                    if close_val <= lowest_close_10 and self._fundingRate[i] > funding_min_10 + 0.0001:
                        side = "Long"
                        reason = "Funding Divergence Long"
                        stop_loss = close_val - (atr * 1.5)
                        take_profit = close_val + (atr * 2.0)
                    elif close_val >= highest_close_10 and self._fundingRate[i] < funding_max_10 - 0.0001:
                        side = "Short"
                        reason = "Funding Divergence Short"
                        stop_loss = close_val + (atr * 1.5)
                        take_profit = close_val - (atr * 2.0)

        # C2. Funding Price Exhaustion
        elif t_type == "funding_price_exhaustion":
            if self._fundingRate is not None:
                is_sideways = (self._close[max(0, i-10):i].max() - self._close[max(0, i-10):i].min()) <= 2.0 * atr
                is_funding_regime = self._regime_funding_extreme[i] or self._regime_sideways_range[i]
                if is_sideways and is_funding_regime:
                    if all(self._fundingRate[i-k] > 0.0003 for k in range(5)):
                        side = "Short"
                        reason = "Funding Exhaustion Short"
                        stop_loss = self._high[max(0, i-5):i+1].max() + (atr * 0.2)
                        take_profit = close_val - (atr * 2.0)
                    elif all(self._fundingRate[i-k] < -0.0003 for k in range(5)):
                        side = "Long"
                        reason = "Funding Exhaustion Long"
                        stop_loss = self._low[max(0, i-5):i+1].min() - (atr * 0.2)
                        take_profit = close_val + (atr * 2.0)

        # C3. Crowded-Side Unwind Signals
        elif t_type == "crowded_side_unwind":
            if self._fundingRate is not None:
                is_funding_regime = self._regime_funding_extreme[i] or self._regime_sideways_range[i]
                if is_funding_regime:
                    highest_close_10 = self._close[max(0, i-10):i].max()
                    lowest_close_10 = self._close[max(0, i-10):i].min()
                    if self._fundingRate[i] < -0.0003 and close_val > highest_close_10:
                        side = "Long"
                        reason = "Crowded Unwind Long"
                        stop_loss = close_val - (atr * 1.5)
                        take_profit = close_val + (atr * 2.0)
                    elif self._fundingRate[i] > 0.0003 and close_val < lowest_close_10:
                        side = "Short"
                        reason = "Crowded Unwind Short"
                        stop_loss = close_val + (atr * 1.5)
                        take_profit = close_val - (atr * 2.0)

        # D1. VWAP Deviation Return
        elif t_type == "vwap_deviation_return":
            if self._vwap is not None:
                vwap_val = self._vwap[i]
                if not np.isnan(vwap_val):
                    is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i]) and (self._adx[i] < 20)
                    if is_mr_regime:
                        if close_val < vwap_val - (2.5 * atr) and self._rsi_14[i] < 30:
                            side = "Long"
                            reason = "VWAP Deviation Long"
                            stop_loss = close_val - (atr * 1.5)
                            take_profit = vwap_val
                        elif close_val > vwap_val + (2.5 * atr) and self._rsi_14[i] > 70:
                            side = "Short"
                            reason = "VWAP Deviation Short"
                            stop_loss = close_val + (atr * 1.5)
                            take_profit = vwap_val

        # D2. Anchored VWAP Reclaim
        elif t_type == "anchored_vwap_reclaim":
            if self._vwap is not None:
                vwap_val = self._vwap[i]
                if not np.isnan(vwap_val):
                    is_trend_regime = (self._regime_bull_trend[i] or self._regime_bear_trend[i]) and (self._adx[i] >= 25)
                    if is_trend_regime:
                        if self._low[i] <= vwap_val and close_val > vwap_val and self._regime_bull_trend[i]:
                            side = "Long"
                            reason = "Anchored VWAP Reclaim Long"
                            stop_loss = vwap_val - (atr * 1.5)
                            take_profit = close_val + (atr * 2.5)
                        elif self._high[i] >= vwap_val and close_val < vwap_val and self._regime_bear_trend[i]:
                            side = "Short"
                            reason = "Anchored VWAP Reclaim Short"
                            stop_loss = vwap_val + (atr * 1.5)
                            take_profit = close_val - (atr * 2.5)

        # D3. Low-Volatility Range Scalping
        elif t_type == "low_vol_range_scalping":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i]) and (self._adx[i] < 20)
            if is_mr_regime and self._bb_width is not None and self._bb_width[i] < 0.03:
                if self._rsi_14[i] < 30:
                    side = "Long"
                    reason = "Low-Vol Scalping Long"
                    stop_loss = close_val - (atr * 1.5)
                    take_profit = self._bb_mid[i]
                elif self._rsi_14[i] > 70:
                    side = "Short"
                    reason = "Low-Vol Scalping Short"
                    stop_loss = close_val + (atr * 1.5)
                    take_profit = self._bb_mid[i]

        # D4. RSI Exhaustion Regime
        elif t_type == "rsi_exhaustion_regime":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i]) and (self._adx[i] < 20)
            if is_mr_regime:
                if self._rsi_14[i] < 15:
                    side = "Long"
                    reason = "RSI Regime MR Long"
                    stop_loss = close_val - (atr * 1.5)
                    take_profit = close_val + (atr * 2.5)
                elif self._rsi_14[i] > 85:
                    side = "Short"
                    reason = "RSI Regime MR Short"
                    stop_loss = close_val + (atr * 1.5)
                    take_profit = close_val - (atr * 2.5)

        # D5. Range Midpoint Reversion
        elif t_type == "range_midpoint_reversion":
            if self._bb_lower is not None and self._bb_upper is not None:
                is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i]) and (self._adx[i] < 15)
                if is_mr_regime:
                    if close_val < self._bb_lower[i]:
                        side = "Long"
                        reason = "Midpoint Reversion Long"
                        stop_loss = close_val - (atr * 1.5)
                        take_profit = self._bb_mid[i]
                    elif close_val > self._bb_upper[i]:
                        side = "Short"
                        reason = "Midpoint Reversion Short"
                        stop_loss = close_val + (atr * 1.5)
                        take_profit = self._bb_mid[i]

        # E1. Higher-High / Higher-Low Breakout
        elif t_type == "hh_hl_continuation":
            if not np.isnan(self._swing_high[i]) and not np.isnan(self._swing_low[i]):
                is_trend_regime = (self._regime_bull_trend[i] or self._regime_bear_trend[i]) and (self._adx[i] >= 25)
                if is_trend_regime:
                    prev_swing_high = self._swing_high[max(0, i-10)]
                    prev_swing_low = self._swing_low[max(0, i-10)]
                    if close_val > self._swing_high[i] and self._swing_high[i] > prev_swing_high and self._regime_bull_trend[i]:
                        side = "Long"
                        reason = "HH HL Continuation Long"
                        stop_loss = close_val - (atr * 1.5)
                        take_profit = close_val + (atr * 2.5)
                    elif close_val < self._swing_low[i] and self._swing_low[i] < prev_swing_low and self._regime_bear_trend[i]:
                        side = "Short"
                        reason = "HH HL Continuation Short"
                        stop_loss = close_val + (atr * 1.5)
                        take_profit = close_val - (atr * 2.5)

        # E2. Pullback after Volatility Impulse
        elif t_type == "pullback_after_impulse":
            if i >= 4 and self._body_ratio is not None:
                is_trend_regime = (self._regime_bull_trend[i] or self._regime_bear_trend[i]) and (self._adx[i] >= 25)
                if is_trend_regime:
                    impulse_long = False
                    impulse_short = False
                    for k in range(1, 4):
                        vol_ma = self._volume[max(0, i-k-20):i-k].mean() if i-k > 20 else self._volume[i-k]
                        large_body = self._body_ratio[i-k] >= 0.70
                        high_vol = self._volume[i-k] > 1.8 * vol_ma
                        if large_body and high_vol:
                            if self._close[i-k] > self._open[i-k]:
                                impulse_long = True
                            else:
                                impulse_short = True
                            break
                    
                    if impulse_long and close_val > self._high[i-1] and self._regime_bull_trend[i]:
                        side = "Long"
                        reason = "Impulse Pullback Long"
                        stop_loss = close_val - (atr * 1.5)
                        take_profit = close_val + (atr * 2.5)
                    elif impulse_short and close_val < self._low[i-1] and self._regime_bear_trend[i]:
                        side = "Short"
                        reason = "Impulse Pullback Short"
                        stop_loss = close_val + (atr * 1.5)
                        take_profit = close_val - (atr * 2.5)

        # F1. Volatility Exhaustion Reversal
        elif t_type == "volatility_exhaustion_reversal":
            is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i]) and (self._adx[i] < 25)
            if is_mr_regime and self._atr_pct is not None and self._atr_pct[i] > 0.05:
                if self._rsi_14[i] < 25:
                    side = "Long"
                    reason = "Vol Exhaustion MR Long"
                    stop_loss = close_val - (atr * 1.5)
                    take_profit = close_val + (atr * 2.5)
                elif self._rsi_14[i] > 75:
                    side = "Short"
                    reason = "Vol Exhaustion MR Short"
                    stop_loss = close_val + (atr * 1.5)
                    take_profit = close_val - (atr * 2.5)

        # F2. Failed Volatility Expansion Reversal
        elif t_type == "failed_volatility_expansion_reversal":
            if i >= 5 and self._bb_lower is not None:
                is_mr_regime = (self._regime_sideways_range[i] or self._regime_vol_compression[i])
                if is_mr_regime:
                    atr_spiked = atr > 1.8 * self._atr_14[i-5]
                    inside_bands = self._low[i] > self._bb_lower[i] and self._high[i] < self._bb_upper[i]
                    if atr_spiked and inside_bands:
                        if self._rsi_14[i] < 30 and self._lower_wick_ratio[i] >= 0.50:
                            side = "Long"
                            reason = "Failed Vol Reversal Long"
                            stop_loss = close_val - (atr * 1.5)
                            take_profit = self._bb_mid[i]
                        elif self._rsi_14[i] > 70 and self._upper_wick_ratio[i] >= 0.50:
                            side = "Short"
                            reason = "Failed Vol Reversal Short"
                            stop_loss = close_val + (atr * 1.5)
                            take_profit = self._bb_mid[i]

        # =================================================================
        # END PHASE 12 TEMPLATES
        # =================================================================

        if side is not None:
            # Set default SL/TP if not overridden by MR modules
            if stop_loss == 0.0:
                stop_loss = close_val - (atr * self.params["sl_atr_mult"]) if side == "Long" else close_val + (atr * self.params["sl_atr_mult"])
            if take_profit == 0.0:
                take_profit = close_val + (atr * self.params["tp_atr_mult"]) if side == "Long" else close_val - (atr * self.params["tp_atr_mult"])
                
            # Cost-to-ATR filter check (if parameter is active)
            cost_to_atr_mult = self.params.get("cost_to_atr_mult", 0.0)
            if cost_to_atr_mult > 0.0:
                # Read fee and slippage parameters (default values if not specified)
                taker_fee = self.params.get("taker_fee", 0.0005)
                slippage = self.params.get("slippage", 0.0005)
                expected_hold_candles = self.params.get("expected_hold_candles", 10)
                avg_funding = self.params.get("average_absolute_funding_rate", 0.0001)
                
                # Estimate funding drag
                expected_funding_payments = expected_hold_candles / 8.0
                expected_funding_drag = expected_funding_payments * avg_funding
                
                # Worst-case market execution cost
                round_trip_cost_pct = taker_fee + taker_fee + 2.0 * slippage + expected_funding_drag
                round_trip_cost_distance = close_val * round_trip_cost_pct
                
                # Expected target distance (TP distance)
                expected_target_distance = abs(take_profit - close_val)
                
                if expected_target_distance < cost_to_atr_mult * round_trip_cost_distance:
                    return None
                
            return {
                "side": side,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "reason": reason,
                "strategy_name": reason,
                "trail_atr_mult": self.params.get("trail_atr_mult"),
                "breakeven_atr_mult": self.params.get("breakeven_atr_mult"),
                "atr": atr,
                "time_stop": self.params.get("time_stop"),
                "failed_continuation_limit": self.params.get("failed_continuation_limit"),
                "failed_continuation_pnl_thresh": self.params.get("failed_continuation_pnl_thresh", 0.0),
                "dynamic_risk_multiplier": self.params.get("dynamic_risk_multiplier", 1.0)
            }
            
        return None

    def get_param_grid(self) -> dict:
        return {
            "template_type": [
                "trend_pullback", "trend_breakout", "breakout_retest", "failed_breakout_reversal", "sweep_reversal",
                "vwap_mean_reversion", "bollinger_mean_reversion", "bollinger_expansion_breakout", "atr_volatility_expansion",
                "range_compression_breakout", "asia_range_breakout", "asia_range_failure", "london_continuation",
                "new_york_reversal", "funding_extreme_reversal", "funding_trend_continuation", "rsi_exhaustion_reversal",
                "wick_rejection_reversal", "volume_impulse_continuation", "swing_structure_continuation", "low_activity_filler",
                "mtf_breakout", "trend_pullback_ema_reclaim", "vwap_reclaim_continuation", "volatility_compression_release",
                "adx_slope_momentum_continuation", "range_failure_reversal", "asian_range_mean_reversion", "london_breakout_failure",
                "ny_open_sweep_reclaim", "prior_day_sweep_reclaim", "swing_high_low_sweep", "wick_rejection_stop_run",
                "failed_breakdown_reversal", "funding_divergence", "funding_price_exhaustion", "crowded_side_unwind",
                "vwap_deviation_return", "anchored_vwap_reclaim", "low_vol_range_scalping", "rsi_exhaustion_regime",
                "range_midpoint_reversion", "hh_hl_continuation", "pullback_after_impulse", "volatility_exhaustion_reversal",
                "failed_volatility_expansion_reversal"
            ],
            "trend_filter": [None, "ema_200", "sma_50_200"],
            "regime_filter_mode": ["no_filter", "soft", "strict"],
            "tp_atr_mult": [1.5, 2.0, 2.5, 3.0],
            "sl_atr_mult": [1.0, 1.5, 2.0]
        }


class RegimeAdaptiveStrategySystem(BaseStrategy):
    """
    Regime-Adaptive Strategy System that dynamically selects the active module
    based on the current market state (classified by the Regime Engine).
    """
    def __init__(self, params: dict = None):
        default_params = {
            "trend_tp_mult": 2.5,
            "trend_sl_mult": 1.5,
            "range_tp_mult": 2.0,
            "range_sl_mult": 1.5,
            "squeeze_tp_mult": 3.0,
            "squeeze_sl_mult": 1.5,
            "funding_tp_mult": 2.5,
            "funding_sl_mult": 1.5,
            "sweep_tp_mult": 3.0,
            "sweep_sl_mult": 1.5,
            "chop_avoidance": True
        }
        if params:
            default_params.update(params)
        super().__init__(
            name="RegimeAdaptiveStrategySystem",
            hypothesis="Select specialized modules dynamically per regime.",
            params=default_params
        )

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        if i < 200:
            return None
            
        # Cache array references on first call for this DataFrame to optimize speed
        if not hasattr(self, "_cached_df_id") or self._cached_df_id != id(df):
            self._cached_df_id = id(df)
            self._close = df["close"].values
            self._open = df["open"].values
            self._high = df["high"].values
            self._low = df["low"].values
            self._open_time = df["open_time"].values
            self._ema_200 = df["ema_200"].values
            self._ema_50 = df["ema_50"].values
            self._atr_pct = df["atr_pct"].values
            self._bb_width = df["bb_width"].values
            self._bb_upper = df["bb_upper"].values
            self._bb_lower = df["bb_lower"].values
            self._bb_mid = df["bb_mid"].values
            self._rsi_14 = df["rsi_14"].values
            self._lower_wick_ratio = df["lower_wick_ratio"].values
            self._upper_wick_ratio = df["upper_wick_ratio"].values
            self._fundingRate = df["fundingRate"].values
            self._atr_14 = df["atr_14"].values
            self._adx = df["adx"].values
            self._swing_high = df["swing_high"].values
            self._swing_low = df["swing_low"].values
            
            # Regime columns
            self._regime_bull_trend = df["regime_bull_trend"].values
            self._regime_bear_trend = df["regime_bear_trend"].values
            self._regime_sideways_range = df["regime_sideways_range"].values
            self._regime_vol_compression = df["regime_vol_compression"].values
            self._regime_vol_expansion = df["regime_vol_expansion"].values
            self._regime_funding_extreme = df["regime_funding_extreme"].values
            self._regime_toxic_chop = df["regime_toxic_chop"].values

        close_val = self._close[i]
        atr = self._atr_14[i]

        # 1. Chop avoidance
        if self.params["chop_avoidance"] and self._regime_toxic_chop[i]:
            return None

        # 2. Funding Extreme Reversal Module
        if self._regime_funding_extreme[i]:
            funding_val = self._fundingRate[i]
            if funding_val > 0.0005 and self._rsi_14[i] > 65:
                return {
                    "strategy_name": "Regime_Funding_Reversal",
                    "side": "Short",
                    "stop_loss": close_val + (atr * self.params["funding_sl_mult"]),
                    "take_profit": close_val - (atr * self.params["funding_tp_mult"]),
                    "reason": f"High positive funding ({funding_val:.4f}) short reversal"
                }
            elif funding_val < -0.0005 and self._rsi_14[i] < 35:
                return {
                    "strategy_name": "Regime_Funding_Reversal",
                    "side": "Long",
                    "stop_loss": close_val - (atr * self.params["funding_sl_mult"]),
                    "take_profit": close_val + (atr * self.params["funding_tp_mult"]),
                    "reason": f"High negative funding ({funding_val:.4f}) long reversal"
                }

        # 3. Liquidity Sweep Reversal Module
        swing_h = self._swing_high[i]
        swing_l = self._swing_low[i]
        upper_wick_large = self._upper_wick_ratio[i] > 0.45
        lower_wick_large = self._lower_wick_ratio[i] > 0.45
        
        swept_high_reversal = (self._high[i] > swing_h) and (self._close[i] < swing_h) and upper_wick_large
        swept_low_reversal = (self._low[i] < swing_l) and (self._close[i] > swing_l) and lower_wick_large

        if swept_low_reversal and (self._regime_sideways_range[i] or self._rsi_14[i] < 40):
            return {
                "strategy_name": "Regime_Liquidity_Sweep",
                "side": "Long",
                "stop_loss": self._low[i] - (atr * 0.2),
                "take_profit": close_val + (atr * self.params["sweep_tp_mult"]),
                "reason": "Swing Low sweep long rejection"
            }
        elif swept_high_reversal and (self._regime_sideways_range[i] or self._rsi_14[i] > 60):
            return {
                "strategy_name": "Regime_Liquidity_Sweep",
                "side": "Short",
                "stop_loss": self._high[i] + (atr * 0.2),
                "take_profit": close_val - (atr * self.params["sweep_tp_mult"]),
                "reason": "Swing High sweep short rejection"
            }

        # 4. Volatility Squeeze Breakout Module
        if self._regime_vol_compression[i]:
            if close_val > self._bb_upper[i] and self._close[i-1] <= self._bb_upper[i-1]:
                return {
                    "strategy_name": "Regime_Squeeze_Breakout",
                    "side": "Long",
                    "stop_loss": close_val - (atr * self.params["squeeze_sl_mult"]),
                    "take_profit": close_val + (atr * self.params["squeeze_tp_mult"]),
                    "reason": "Squeeze breakout long"
                }
            elif close_val < self._bb_lower[i] and self._close[i-1] >= self._bb_lower[i-1]:
                return {
                    "strategy_name": "Regime_Squeeze_Breakout",
                    "side": "Short",
                    "stop_loss": close_val + (atr * self.params["squeeze_sl_mult"]),
                    "take_profit": close_val - (atr * self.params["squeeze_tp_mult"]),
                    "reason": "Squeeze breakout short"
                }

        # 5. Trend Continuation Module
        if self._regime_bull_trend[i]:
            if self._low[i] <= self._ema_50[i] and close_val > self._ema_50[i] and self._rsi_14[i] < 60:
                return {
                    "strategy_name": "Regime_Trend_Continuation",
                    "side": "Long",
                    "stop_loss": close_val - (atr * self.params["trend_sl_mult"]),
                    "take_profit": close_val + (atr * self.params["trend_tp_mult"]),
                    "reason": "EMA50 pullback long in bull trend"
                }
        elif self._regime_bear_trend[i]:
            if self._high[i] >= self._ema_50[i] and close_val < self._ema_50[i] and self._rsi_14[i] > 40:
                return {
                    "strategy_name": "Regime_Trend_Continuation",
                    "side": "Short",
                    "stop_loss": close_val + (atr * self.params["trend_sl_mult"]),
                    "take_profit": close_val - (atr * self.params["trend_tp_mult"]),
                    "reason": "EMA50 pullback short in bear trend"
                }

        # 6. Sideways Mean Reversion Module
        if self._regime_sideways_range[i]:
            if self._high[i] >= self._bb_upper[i] and close_val < self._bb_upper[i] and self._rsi_14[i] > 60:
                return {
                    "strategy_name": "Regime_Mean_Reversion",
                    "side": "Short",
                    "stop_loss": self._high[i] + (atr * 0.2),
                    "take_profit": self._bb_mid[i],
                    "reason": "BB upper band mean reversion short"
                }
            elif self._low[i] <= self._bb_lower[i] and close_val > self._bb_lower[i] and self._rsi_14[i] < 40:
                return {
                    "strategy_name": "Regime_Mean_Reversion",
                    "side": "Long",
                    "stop_loss": self._low[i] - (atr * 0.2),
                    "take_profit": self._bb_mid[i],
                    "reason": "BB lower band mean reversion long"
                }

        return None

    def get_param_grid(self) -> dict:
        return {
            "trend_tp_mult": [2.0, 2.5, 3.0],
            "trend_sl_mult": [1.5, 2.0],
            "range_tp_mult": [1.5, 2.0, 2.5],
            "range_sl_mult": [1.0, 1.5],
            "squeeze_tp_mult": [2.5, 3.0, 3.5],
            "squeeze_sl_mult": [1.5, 2.0],
            "funding_tp_mult": [2.0, 2.5],
            "funding_sl_mult": [1.5, 2.0],
            "sweep_tp_mult": [2.5, 3.0],
            "sweep_sl_mult": [1.5, 2.0],
            "chop_avoidance": [True, False]
        }


class MTFBreakoutStrategy(BaseStrategy):
    """
    MTF Breakout Strategy utilizing 1h trend/volatility regimes,
    15m Bollinger setups, and 5m confirmation/retests/failed-breakout-reversals.
    """
    def __init__(self, params: dict = None):
        default_params = {
            "confirm_candles": 2,
            "wick_ratio_thresh": 0.45,
            "tp_atr_mult": 2.5,
            "sl_atr_mult": 1.5,
            "trail_atr_mult": 1.5,
            "breakeven_atr_mult": 1.5
        }
        if params:
            default_params.update(params)
        super().__init__(
            name="MTFBreakoutStrategy",
            hypothesis="Utilize 1h regime filters, 15m BB setup, 5m confirmation, retests, failed breakout reversals and tighter stops.",
            params=default_params
        )
        self.template = UniversalStrategyTemplate({
            "template_type": "mtf_breakout",
            "confirm_candles": default_params["confirm_candles"],
            "wick_ratio_thresh": default_params["wick_ratio_thresh"],
            "tp_atr_mult": default_params["tp_atr_mult"],
            "sl_atr_mult": default_params["sl_atr_mult"],
            "trail_atr_mult": default_params["trail_atr_mult"],
            "breakeven_atr_mult": default_params["breakeven_atr_mult"]
        })

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        sig = self.template.get_signal(df, i, live_metrics)
        if sig is not None:
            sig["strategy_name"] = "MTFBreakoutStrategy"
            sig["trail_atr_mult"] = self.params.get("trail_atr_mult")
            sig["breakeven_atr_mult"] = self.params.get("breakeven_atr_mult")
            sig["atr"] = df["atr_14"].values[i] if "atr_14" in df.columns else 0.0
        return sig

    def get_param_grid(self) -> dict:
        return {
            "confirm_candles": [2, 3],
            "wick_ratio_thresh": [0.4, 0.45, 0.5],
            "tp_atr_mult": [2.0, 2.5, 3.0],
            "sl_atr_mult": [1.2, 1.5, 1.8]
        }


