# Phase 35 Signal-Level Sleeve Specifications

## STRAT2_P35_COST_ATR_BREAKOUT

- Source building block: `P34_0217`

- Family: `cost_to_atr_breakout`

- Parameters: `{"adx_min": 15, "bb_width_min": 0.03, "funding_abs_max": 0.0015, "max_bad_wick": 0.55, "max_cost_to_risk": 0.1, "session_mode": "NO_OFF_HOURS", "sl_atr_mult": 1.8, "time_stop": 96, "tp_atr_mult": 2.35, "volume_trend_min": 0.85}`

- Live-known inputs: closed 1h OHLCV, Bollinger Bands, ATR, ATR percentile, RSI, ADX, wick/body ratios, volume trend, funding rate, UTC hour/session, EMA trend state.

- Entry timing: evaluate after candle close; engine enters on next candle open.

- Exit timing: engine SL/TP/time-stop path with conservative SL-first same-candle priority.

- Not allowed: no trade-log filtering, no labels from completed outcomes, no copied Phase 34 trades.

## STRAT3_P35_PROJECTED_NET_R

- Source building block: `P34_0007`

- Family: `projected_net_r_breakout`

- Parameters: `{"adx_min": 16, "atr_pct_min": 0.35, "max_bad_wick": 0.52, "max_cost_to_risk": 0.1, "min_projected_net_R": 0.9, "rsi_long_max": 72, "rsi_short_min": 28, "session_mode": "NO_OFF_HOURS", "sl_atr_mult": 1.75, "time_stop": 96, "tp_atr_mult": 2.45}`

- Live-known inputs: closed 1h OHLCV, Bollinger Bands, ATR, ATR percentile, RSI, ADX, wick/body ratios, volume trend, funding rate, UTC hour/session, EMA trend state.

- Entry timing: evaluate after candle close; engine enters on next candle open.

- Exit timing: engine SL/TP/time-stop path with conservative SL-first same-candle priority.

- Not allowed: no trade-log filtering, no labels from completed outcomes, no copied Phase 34 trades.

## STRAT4_P35_SESSION_EXPANSION

- Source building block: `P34_0219`

- Family: `session_expansion`

- Parameters: `{"adx_min": 14, "bb_width_min": 0.028, "funding_abs_max": 0.0015, "max_cost_to_risk": 0.13, "min_body_ratio": 0.2, "min_expected_R": 1.1, "min_projected_net_R": 0.7, "session_mode": "NO_OFF_HOURS", "sl_atr_mult": 1.85, "time_stop": 72, "tp_atr_mult": 2.45, "volume_trend_min": 0.85}`

- Live-known inputs: closed 1h OHLCV, Bollinger Bands, ATR, ATR percentile, RSI, ADX, wick/body ratios, volume trend, funding rate, UTC hour/session, EMA trend state.

- Entry timing: evaluate after candle close; engine enters on next candle open.

- Exit timing: engine SL/TP/time-stop path with conservative SL-first same-candle priority.

- Not allowed: no trade-log filtering, no labels from completed outcomes, no copied Phase 34 trades.

## STRAT5_P35_STRESS_HARDENED

- Source building block: `P34_0218`

- Family: `same_candle_hardened`

- Parameters: `{"adx_min": 18, "bb_width_min": 0.035, "funding_abs_max": 0.0012, "max_bad_wick": 0.35, "max_cost_to_risk": 0.1, "min_body_ratio": 0.22, "min_expected_R": 1.0, "min_mid_distance_atr": 0.2, "session_mode": "NO_OFF_HOURS", "sl_atr_mult": 1.9, "time_stop": 72, "tp_atr_mult": 2.55, "volume_trend_min": 0.95}`

- Live-known inputs: closed 1h OHLCV, Bollinger Bands, ATR, ATR percentile, RSI, ADX, wick/body ratios, volume trend, funding rate, UTC hour/session, EMA trend state.

- Entry timing: evaluate after candle close; engine enters on next candle open.

- Exit timing: engine SL/TP/time-stop path with conservative SL-first same-candle priority.

- Not allowed: no trade-log filtering, no labels from completed outcomes, no copied Phase 34 trades.

## STRAT6_P35_LOW_R_FRICTION

- Source building block: `P34_0002`

- Family: `low_friction_momentum`

- Parameters: `{"atr_pct_min": 0.3, "bb_width_min": 0.035, "funding_abs_max": 0.0018, "max_cost_to_risk": 0.18, "min_expected_R": 1.1, "rsi_long_max": 76, "rsi_short_min": 24, "session_mode": "ALL", "sl_atr_mult": 1.8, "time_stop": 120, "tp_atr_mult": 2.25, "volume_trend_min": 0.8}`

- Live-known inputs: closed 1h OHLCV, Bollinger Bands, ATR, ATR percentile, RSI, ADX, wick/body ratios, volume trend, funding rate, UTC hour/session, EMA trend state.

- Entry timing: evaluate after candle close; engine enters on next candle open.

- Exit timing: engine SL/TP/time-stop path with conservative SL-first same-candle priority.

- Not allowed: no trade-log filtering, no labels from completed outcomes, no copied Phase 34 trades.

## P35_CONSERVATIVE_QUALITY_PLUS

- Source building block: `Phase33`

- Family: `conservative_quality`

- Parameters: `{"adx_min": 20, "atr_pct_min": 0.45, "bb_width_min": 0.04, "dynamic_risk_multiplier": 0.85, "funding_abs_max": 0.0008, "max_bad_wick": 0.42, "max_cost_to_risk": 0.12, "min_body_ratio": 0.2, "min_expected_R": 1.25, "session_mode": "NO_OFF_HOURS", "sl_atr_mult": 1.9, "time_stop": 72, "tp_atr_mult": 2.75, "volume_trend_min": 1.0}`

- Live-known inputs: closed 1h OHLCV, Bollinger Bands, ATR, ATR percentile, RSI, ADX, wick/body ratios, volume trend, funding rate, UTC hour/session, EMA trend state.

- Entry timing: evaluate after candle close; engine enters on next candle open.

- Exit timing: engine SL/TP/time-stop path with conservative SL-first same-candle priority.

- Not allowed: no trade-log filtering, no labels from completed outcomes, no copied Phase 34 trades.
