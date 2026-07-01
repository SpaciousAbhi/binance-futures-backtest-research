import numpy as np
import pandas as pd

class BacktestEngine:
    """
    A bar-by-bar backtesting engine for perpetual futures.
    Executes trades on closed-candle signals only (at next open price).
    Includes trading fees, slippage, and cumulative funding rate costs.
    """
    def __init__(self, initial_capital: float = 10000.0, maker_fee: float = 0.0002, taker_fee: float = 0.0005, slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage = slippage

    def _execute_bar(self, i, active_position, high, low, close, open_price, open_time, df):
        """
        Updates trailing stops and breakeven limits for the active position,
        and checks for stop loss and take profit hits.
        Returns (triggered_exit, exit_price).
        """
        # 1. Update peak price, trailing stops and breakeven
        atr_14_val = df["atr_14"].values[i] if "atr_14" in df.columns else 0.0
        atr_val = active_position.get("atr_at_entry") or atr_14_val
        
        if active_position["side"] == "Long":
            active_position["peak_price"] = max(active_position.get("peak_price", active_position["entry_price"]), high)
            
            be_mult = active_position.get("breakeven_atr_mult")
            if be_mult is not None and be_mult > 0:
                if active_position["peak_price"] >= active_position["entry_price"] + be_mult * atr_val:
                    active_position["stop_loss"] = max(active_position["stop_loss"], active_position["entry_price"])
                    
            trail_mult = active_position.get("trail_atr_mult")
            if trail_mult is not None and trail_mult > 0:
                trail_stop = active_position["peak_price"] - trail_mult * atr_val
                active_position["stop_loss"] = max(active_position["stop_loss"], trail_stop)
                
            # Check exits
            is_sl_hit = low <= active_position["stop_loss"]
            is_tp_hit = high >= active_position["take_profit"]
            
            if is_sl_hit or is_tp_hit:
                if is_sl_hit:
                    return "Stop Loss", active_position["stop_loss"]
                else:
                    return "Take Profit", active_position["take_profit"]
                    
        else:  # Short
            active_position["peak_price"] = min(active_position.get("peak_price", active_position["entry_price"]), low)
            
            be_mult = active_position.get("breakeven_atr_mult")
            if be_mult is not None and be_mult > 0:
                if active_position["peak_price"] <= active_position["entry_price"] - be_mult * atr_val:
                    active_position["stop_loss"] = min(active_position["stop_loss"], active_position["entry_price"])
                    
            trail_mult = active_position.get("trail_atr_mult")
            if trail_mult is not None and trail_mult > 0:
                trail_stop = active_position["peak_price"] + trail_mult * atr_val
                active_position["stop_loss"] = min(active_position["stop_loss"], trail_stop)
                
            # Check exits
            is_sl_hit = high >= active_position["stop_loss"]
            is_tp_hit = low <= active_position["take_profit"]
            
            if is_sl_hit or is_tp_hit:
                if is_sl_hit:
                    return "Stop Loss", active_position["stop_loss"]
                else:
                    return "Take Profit", active_position["take_profit"]
                    
        return None, None

    def run(self, df: pd.DataFrame, strategy, config: dict = None) -> dict:
        """
        Runs the backtest bar-by-bar.
        
        Parameters:
            df: DataFrame containing OHLCV, indicators, and fundingRate.
            strategy: A Strategy instance that implements get_signal().
            config: Optional config dict to override default engine settings or stress tests.
        """
        # Read overrides from config if present
        fee_mult = config.get("fee_mult", 1.0) if config else 1.0
        slip_mult = config.get("slip_mult", 1.0) if config else 1.0
        delay_candles = config.get("delay_candles", 0) if config else 0
        missed_fill_pct = config.get("missed_fill_pct", 0.0) if config else 0.0
        stale_skip = config.get("stale_skip", False) if config else False
        stale_limit_minutes = config.get("stale_limit_minutes", 15) if config else 15
        
        seed = config.get("seed", 42) if config else 42
        rng = np.random.default_rng(seed)
        
        current_maker_fee = self.maker_fee * fee_mult
        current_taker_fee = self.taker_fee * fee_mult
        current_slippage = self.slippage * slip_mult

        capital = self.initial_capital
        active_position = None  # None or dict
        trades = []

        # We will loop through the dataframe.
        # Index i represents the bar that has just closed.
        # We generate signals based on data up to index i (inclusive).
        # We execute trades at index i + 1 + delay_candles.
        n = len(df)
        i = 0
        
        # Pre-extract numpy arrays for instant lookups (100x speedup!)
        open_times = df["open_time"].values
        opens = df["open"].values
        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values
        funding_rates = df["fundingRate"].values

        # Determine timeframe minutes from data
        timeframe_minutes = 60.0
        if len(open_times) > 1:
            timeframe_minutes = (open_times[1] - open_times[0]) / (60 * 1000)

        # Calculate full PeriodIndex of months for monthly reporting
        start_month = pd.to_datetime(df["open_time"].min(), unit="ms", utc=True).tz_localize(None).to_period("M")
        end_month = pd.to_datetime(df["open_time"].max(), unit="ms", utc=True).tz_localize(None).to_period("M")
        all_months = pd.period_range(start=start_month, end=end_month, freq="M")
        
        while i < n - 1:
            # Check funding fee if we have an active position
            if active_position is not None:
                # Apply funding fee if the current candle open time falls on an 8-hour boundary
                # Binance funding occurs every 8 hours: 00:00, 08:00, 16:00 UTC
                open_time = open_times[i]
                if open_time % (8 * 3600 * 1000) == 0:
                    funding_rate = funding_rates[i]
                    # For long positions: we pay if funding rate is positive, receive if negative.
                    # For short positions: we receive if funding rate is positive, pay if negative.
                    # funding_payment = size_in_contracts * price * funding_rate
                    side_factor = 1.0 if active_position["side"] == "Long" else -1.0
                    funding_cost = active_position["size"] * opens[i] * funding_rate * side_factor
                    active_position["cumulative_funding"] += funding_cost
                    # Deduct from capital
                    capital -= funding_cost
                    if capital <= 0:
                        # Bankruptcy stop from funding cost
                        exit_price = opens[i]
                        exit_fee = active_position["size"] * exit_price * current_taker_fee
                        gross_pnl = active_position["size"] * (exit_price - active_position["entry_price"]) * side_factor
                        net_pnl = gross_pnl - active_position["entry_fee"] - exit_fee - active_position["cumulative_funding"]
                        
                        trade_record = {
                            "entry_time": active_position["entry_time"],
                            "entry_datetime": active_position["entry_datetime"],
                            "exit_time": open_times[i],
                            "exit_datetime": str(pd.to_datetime(open_times[i], unit="ms", utc=True)),
                            "side": active_position["side"],
                            "entry_price": active_position["entry_price"],
                            "exit_price": exit_price,
                            "stop_loss": active_position["stop_loss"],
                            "take_profit": active_position["take_profit"],
                            "size": active_position["size"],
                            "gross_pnl": gross_pnl,
                            "fees": active_position["entry_fee"] + exit_fee,
                            "raw_exit_price": exit_price,
                            "entry_slippage": abs(active_position["entry_price"] - active_position["raw_entry_price"]) * active_position["size"],
                            "exit_slippage": 0.0,
                            "slippage": abs(active_position["entry_price"] - active_position["raw_entry_price"]) * active_position["size"],
                            "funding": active_position["cumulative_funding"],
                            "net_pnl": net_pnl,
                            "capital_after": 0.0,
                            "reason": "Bankruptcy (Funding)",
                            "R": gross_pnl / (active_position["size"] * abs(active_position["entry_price"] - active_position["initial_stop_loss"])) if abs(active_position["entry_price"] - active_position["initial_stop_loss"]) > 0 else 0.0,
                            "MFE": active_position["max_mfe"],
                            "MAE": active_position["max_mae"],
                            "hold_candles": i - active_position["entry_idx"]
                        }
                        trades.append(trade_record)
                        active_position = None
                        capital = 0.0
                        break

            # If we have an active position, check for exit conditions (Stop Loss, Take Profit, Trailing Stop)
            if active_position is not None:
                high = highs[i]
                low = lows[i]
                close = closes[i]
                open_price = opens[i]

                # Update MFE and MAE
                entry_price = active_position["entry_price"]
                if active_position["side"] == "Long":
                    trade_high = high
                    trade_low = low
                    mfe_p = (trade_high - entry_price) / entry_price
                    mae_p = (entry_price - trade_low) / entry_price
                else:
                    trade_high = high
                    trade_low = low
                    mfe_p = (entry_price - trade_low) / entry_price
                    mae_p = (trade_high - entry_price) / entry_price

                active_position["max_mfe"] = max(active_position["max_mfe"], mfe_p)
                active_position["max_mae"] = max(active_position["max_mae"], mae_p)

                # Check Stop Loss / Take Profit / Trailing Stop via _execute_bar
                triggered_exit, exit_price = self._execute_bar(i, active_position, high, low, close, open_price, open_times[i], df)

                # Handle exits
                if triggered_exit is not None:
                    # Apply slippage on exit (slippage hurts us)
                    # For Long exit: sell market -> exit_price * (1 - slippage)
                    # For Short exit: buy market -> exit_price * (1 + slippage)
                    exit_slip_factor = 1.0 - current_slippage if active_position["side"] == "Long" else 1.0 + current_slippage
                    final_exit_price = exit_price * exit_slip_factor
                    
                    # Taker fee on market order exit
                    exit_fee = active_position["size"] * final_exit_price * current_taker_fee
                    
                    # Compute Gross PnL
                    side_factor = 1.0 if active_position["side"] == "Long" else -1.0
                    gross_pnl = active_position["size"] * (final_exit_price - entry_price) * side_factor
                    
                    # Compute Net PnL
                    net_pnl = gross_pnl - active_position["entry_fee"] - exit_fee - active_position["cumulative_funding"]
                    capital += gross_pnl - exit_fee # Funding already deducted during hold

                    capital_to_save = capital
                    is_liquidated = False
                    if capital <= 0:
                        capital_to_save = 0.0
                        is_liquidated = True
                        triggered_exit += " (Bankruptcy)"

                    # R-multiple
                    risk_p = abs(entry_price - active_position["initial_stop_loss"])
                    r_multiplier = gross_pnl / (active_position["size"] * risk_p) if risk_p > 0 else 0.0

                    trade_record = {
                        "entry_time": active_position["entry_time"],
                        "entry_datetime": active_position["entry_datetime"],
                        "exit_time": open_times[i],
                        "exit_datetime": str(pd.to_datetime(open_times[i], unit="ms", utc=True)),
                        "side": active_position["side"],
                        "entry_price": entry_price,
                        "exit_price": final_exit_price,
                        "stop_loss": active_position["stop_loss"],
                        "take_profit": active_position["take_profit"],
                        "size": active_position["size"],
                        "gross_pnl": gross_pnl,
                        "fees": active_position["entry_fee"] + exit_fee,
                        "raw_exit_price": exit_price,
                        "entry_slippage": abs(entry_price - active_position["raw_entry_price"]) * active_position["size"],
                        "exit_slippage": abs(final_exit_price - exit_price) * active_position["size"],
                        "slippage": (abs(entry_price - active_position["raw_entry_price"]) * active_position["size"] +
                                     abs(final_exit_price - exit_price) * active_position["size"]),
                        "funding": active_position["cumulative_funding"],
                        "net_pnl": net_pnl,
                        "capital_after": capital_to_save,
                        "reason": triggered_exit,
                        "R": r_multiplier,
                        "MFE": active_position["max_mfe"],
                        "MAE": active_position["max_mae"],
                        "hold_candles": i - active_position["entry_idx"]
                    }
                    trades.append(trade_record)
                    active_position = None
                    if is_liquidated:
                        capital = 0.0
                        break
                    i += 1
                    continue

            # If no active position, check for new entry signals
            if active_position is None:
                signal = strategy.get_signal(df, i) # Returns None or dict
                if signal is not None:
                    # Random missed fill check for stress testing
                    if missed_fill_pct > 0.0 and rng.random() < missed_fill_pct:
                        # Missed fill, continue to next bar
                        i += 1
                        continue

                    # Executing index with delay
                    exec_idx = i + 1 + delay_candles
                    if exec_idx >= n:
                        break

                    # Stale signal check: if the signal took too long to execute (stale skip)
                    if stale_skip:
                        time_delta_mins = (open_times[exec_idx] - open_times[i + 1]) / (60 * 1000)
                        effective_stale_limit = max(stale_limit_minutes, 1.5 * timeframe_minutes)
                        if time_delta_mins > effective_stale_limit:
                            # Stale signal, skip
                            i += 1
                            continue

                    # Execute entry at the open of the exec_idx candle
                    raw_entry_price = opens[exec_idx]
                    
                    # Apply slippage on entry (slippage increases entry price for long, decreases for short)
                    entry_slip_factor = 1.0 + current_slippage if signal["side"] == "Long" else 1.0 - current_slippage
                    entry_price = raw_entry_price * entry_slip_factor

                    # Position sizing by fixed risk (1% of current capital)
                    stop_loss_price = signal["stop_loss"]
                    risk_per_unit = abs(entry_price - stop_loss_price)
                    
                    if risk_per_unit > 0:
                        risk_amount = capital * 0.01 # Risk 1% of capital
                        position_size = risk_amount / risk_per_unit
                    else:
                        # Fallback to simple leverage-based sizing (e.g. 1x leverage)
                        position_size = capital / entry_price

                    # Exchange-like precision and min-notional checks
                    # BTCUSDT min notional is 100 USDT, size precision is 3 decimals, price precision is 1 decimal
                    min_notional = 100.0
                    notional = position_size * entry_price
                    if notional < min_notional:
                        # Boost position size to min notional if we have capital
                        position_size = min_notional / entry_price
                        notional = min_notional
                    
                    # Precision rounding
                    position_size = round(position_size, 3)
                    entry_price = round(entry_price, 1)

                    if position_size * entry_price > capital * 5.0: # Max 5x leverage cap
                        position_size = (capital * 5.0) / entry_price
                        position_size = round(position_size, 3)

                    # Deduct entry taker fee
                    entry_fee = position_size * entry_price * current_taker_fee
                    capital -= entry_fee
                    if capital <= 0:
                        # Bankruptcy stop from entry fee
                        capital = 0.0
                        active_position = None
                        break

                    active_position = {
                        "side": signal["side"],
                        "entry_idx": exec_idx,
                        "entry_time": open_times[exec_idx],
                        "entry_datetime": str(pd.to_datetime(open_times[exec_idx], unit="ms", utc=True)),
                        "raw_entry_price": raw_entry_price,
                        "entry_price": entry_price,
                        "stop_loss": signal["stop_loss"],
                        "initial_stop_loss": signal["stop_loss"],
                        "take_profit": signal["take_profit"],
                        "size": position_size,
                        "entry_fee": entry_fee,
                        "cumulative_funding": 0.0,
                        "max_mfe": 0.0,
                        "max_mae": 0.0,
                        "trail_atr_mult": signal.get("trail_atr_mult"),
                        "breakeven_atr_mult": signal.get("breakeven_atr_mult"),
                        "atr_at_entry": signal.get("atr") or (df["atr_14"].values[exec_idx] if "atr_14" in df.columns else 0.0),
                        "peak_price": entry_price
                    }
                    
                    # Move index forward to execution index so we don't look at candles during delay
                    i = exec_idx
                    continue

            i += 1

        # Force close any open position at the end of the backtest to calculate final metrics
        if active_position is not None:
            last_idx = n - 1
            # Update MFE and MAE for any remaining candles including last_idx
            for idx in range(i, last_idx + 1):
                high = highs[idx]
                low = lows[idx]
                entry_price = active_position["entry_price"]
                if active_position["side"] == "Long":
                    mfe_p = (high - entry_price) / entry_price
                    mae_p = (entry_price - low) / entry_price
                else:
                    mfe_p = (entry_price - low) / entry_price
                    mae_p = (high - entry_price) / entry_price
                active_position["max_mfe"] = max(active_position["max_mfe"], mfe_p)
                active_position["max_mae"] = max(active_position["max_mae"], mae_p)

            exit_price = closes[last_idx]
            exit_fee = active_position["size"] * exit_price * current_taker_fee
            side_factor = 1.0 if active_position["side"] == "Long" else -1.0
            gross_pnl = active_position["size"] * (exit_price - active_position["entry_price"]) * side_factor
            net_pnl = gross_pnl - active_position["entry_fee"] - exit_fee - active_position["cumulative_funding"]
            capital += gross_pnl - exit_fee
            
            capital_to_save = capital
            reason = "Force Close"
            if capital <= 0:
                capital_to_save = 0.0
                reason = "Force Close (Bankruptcy)"

            trade_record = {
                "entry_time": active_position["entry_time"],
                "entry_datetime": active_position["entry_datetime"],
                "exit_time": open_times[last_idx],
                "exit_datetime": str(pd.to_datetime(open_times[last_idx], unit="ms", utc=True)),
                "side": active_position["side"],
                "entry_price": active_position["entry_price"],
                "exit_price": exit_price,
                "stop_loss": active_position["stop_loss"],
                "take_profit": active_position["take_profit"],
                "size": active_position["size"],
                "gross_pnl": gross_pnl,
                "fees": active_position["entry_fee"] + exit_fee,
                "raw_exit_price": exit_price,
                "entry_slippage": abs(active_position["entry_price"] - active_position["raw_entry_price"]) * active_position["size"],
                "exit_slippage": 0.0,
                "slippage": abs(active_position["entry_price"] - active_position["raw_entry_price"]) * active_position["size"],
                "funding": active_position["cumulative_funding"],
                "net_pnl": net_pnl,
                "capital_after": capital_to_save,
                "reason": reason,
                "R": gross_pnl / (active_position["size"] * abs(active_position["entry_price"] - active_position["initial_stop_loss"])) if abs(active_position["entry_price"] - active_position["initial_stop_loss"]) > 0 else 0.0,
                "MFE": active_position["max_mfe"],
                "MAE": active_position["max_mae"],
                "hold_candles": last_idx - active_position["entry_idx"]
            }
            trades.append(trade_record)

        # Calculate metrics
        trades_df = pd.DataFrame(trades)
        metrics = self._calculate_metrics(trades_df, capital, all_months)
        
        return {
            "metrics": metrics,
            "trades": trades_df
        }

    def _calculate_metrics(self, trades_df: pd.DataFrame, final_capital: float, all_months: pd.PeriodIndex = None) -> dict:
        if all_months is None:
            if not trades_df.empty:
                # Need to parser timezone-safely
                parsed_dates = pd.to_datetime(trades_df["exit_datetime"])
                # Handle possible timezone differences
                start_month = parsed_dates.min().tz_localize(None).to_period("M")
                end_month = parsed_dates.max().tz_localize(None).to_period("M")
                all_months = pd.period_range(start=start_month, end=end_month, freq="M")
            else:
                all_months = pd.period_range(start="2020-01", end="2020-01", freq="M")

        if trades_df.empty:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "gross_pnl": 0.0,
                "fees": 0.0,
                "entry_slippage": 0.0,
                "exit_slippage": 0.0,
                "slippage": 0.0,
                "funding": 0.0,
                "net_pnl": 0.0,
                "max_drawdown": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
                "avg_winner": 0.0,
                "avg_loser": 0.0,
                "avg_r": 0.0,
                "avg_hold_time": 0.0,
                "positive_months": 0,
                "zero_months": len(all_months),
                "negative_months": 0,
                "best_month": 0.0,
                "worst_month": 0.0,
                "monthly_pnl": {str(k): 0.0 for k in all_months}
            }

        wins = trades_df[trades_df["net_pnl"] > 0]
        losses = trades_df[trades_df["net_pnl"] <= 0]
        
        total_trades = len(trades_df)
        win_rate = len(wins) / total_trades if total_trades > 0 else 0.0
        
        gross_pnl = trades_df["gross_pnl"].sum()
        fees = trades_df["fees"].sum()
        entry_slip = trades_df["entry_slippage"].sum() if "entry_slippage" in trades_df.columns else trades_df["slippage"].sum()
        exit_slip = trades_df["exit_slippage"].sum() if "exit_slippage" in trades_df.columns else 0.0
        slippage = trades_df["slippage"].sum()
        funding = trades_df["funding"].sum()
        net_pnl = trades_df["net_pnl"].sum()
        
        gross_wins = wins["net_pnl"].sum()
        gross_losses = abs(losses["net_pnl"].sum())
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else (gross_wins if gross_wins > 0 else 1.0)
        
        expectancy = trades_df["net_pnl"].mean()
        avg_winner = wins["net_pnl"].mean() if len(wins) > 0 else 0.0
        avg_loser = losses["net_pnl"].mean() if len(losses) > 0 else 0.0
        avg_r = trades_df["R"].mean()
        avg_hold = trades_df["hold_candles"].mean()

        # Monthly aggregation
        trades_df["exit_datetime_parsed"] = pd.to_datetime(trades_df["exit_datetime"]).dt.tz_localize(None)
        trades_df["month"] = trades_df["exit_datetime_parsed"].dt.to_period("M")
        monthly_groups = trades_df.groupby("month")["net_pnl"].sum()
        
        # Reindex to contain ALL tested months (zero-trade months filled with 0.0)
        monthly_groups = monthly_groups.reindex(all_months, fill_value=0.0)
        
        pos_months = (monthly_groups > 0).sum()
        neg_months = (monthly_groups < 0).sum()
        zero_months = (monthly_groups == 0).sum()

        # Detailed monthly report records
        monthly_report = []
        for m in all_months:
            m_str = str(m)
            m_trades = trades_df[trades_df["month"] == m]
            
            if m_trades.empty:
                monthly_report.append({
                    "month": m_str,
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0.0,
                    "gross_pnl": 0.0,
                    "fees": 0.0,
                    "slippage": 0.0,
                    "funding": 0.0,
                    "net_pnl": 0.0,
                    "drawdown": 0.0,
                    "status": "Zero",
                    "active_module": "None",
                    "regime_note": "None"
                })
            else:
                m_wins = m_trades[m_trades["net_pnl"] > 0]
                m_losses = m_trades[m_trades["net_pnl"] <= 0]
                m_win_rate = len(m_wins) / len(m_trades)
                m_gross = m_trades["gross_pnl"].sum()
                m_fees = m_trades["fees"].sum()
                m_slip = m_trades["slippage"].sum()
                m_fund = m_trades["funding"].sum()
                m_net = m_trades["net_pnl"].sum()
                
                active_modules = m_trades["strategy"].dropna().unique().tolist() if "strategy" in m_trades.columns else []
                m_active_module = ", ".join(active_modules) if active_modules else "Unknown"
                
                # Approximate max drawdown within this month
                prev_trades = trades_df[trades_df["exit_datetime_parsed"] < pd.to_datetime(m_trades["exit_datetime"].min()).tz_localize(None)]
                if "capital_after" in m_trades.columns:
                    caps = m_trades["capital_after"].values
                    m_start_cap = prev_trades.iloc[-1]["capital_after"] if not prev_trades.empty else self.initial_capital
                else:
                    prev_pnl_sum = prev_trades["net_pnl"].sum() if not prev_trades.empty else 0.0
                    m_start_cap = self.initial_capital + prev_pnl_sum
                    caps = m_start_cap + np.cumsum(m_trades["net_pnl"].values)
                
                m_equity = np.insert(caps, 0, m_start_cap)
                m_peaks = np.maximum.accumulate(m_equity)
                with np.errstate(divide='ignore', invalid='ignore'):
                    m_dds = np.where(m_peaks > 0, (m_peaks - m_equity) / m_peaks, 0.0)
                m_dd = m_dds.max() if len(m_dds) > 0 else 0.0
                
                status_str = "Positive" if m_net > 0 else "Negative" if m_net < 0 else "Zero"
                
                monthly_report.append({
                    "month": m_str,
                    "trades": len(m_trades),
                    "wins": len(m_wins),
                    "losses": len(m_losses),
                    "win_rate": float(m_win_rate),
                    "gross_pnl": float(m_gross),
                    "fees": float(m_fees),
                    "slippage": float(m_slip),
                    "funding": float(m_fund),
                    "net_pnl": float(m_net),
                    "drawdown": float(m_dd),
                    "status": status_str,
                    "active_module": m_active_module,
                    "regime_note": "Calibrated"
                })

        # Calculate max drawdown on equity curve
        # Create equity curve
        pnl_series = trades_df["net_pnl"].values
        equity_curve = self.initial_capital + np.cumsum(pnl_series)
        equity_curve = np.insert(equity_curve, 0, self.initial_capital) # Start with initial capital
        
        # Prevent equity curve from going below 0 (capped at bankruptcy)
        equity_curve = np.maximum(equity_curve, 0.0)
        
        peaks = np.maximum.accumulate(equity_curve)
        
        # If peak is 0, drawdown is 0
        with np.errstate(divide='ignore', invalid='ignore'):
            drawdowns = np.where(peaks > 0, (peaks - equity_curve) / peaks, 0.0)
        max_dd = drawdowns.max() if len(drawdowns) > 0 else 0.0
        if max_dd > 1.0:
            max_dd = 1.0 # Cap max drawdown at 100%

        best_month_val = monthly_groups.max() if not monthly_groups.empty else 0.0
        worst_month_val = monthly_groups.min() if not monthly_groups.empty else 0.0

        return {
            "total_trades": total_trades,
            "win_rate": float(win_rate),
            "gross_pnl": float(gross_pnl),
            "fees": float(fees),
            "entry_slippage": float(entry_slip),
            "exit_slippage": float(exit_slip),
            "slippage": float(slippage),
            "funding": float(funding),
            "net_pnl": float(net_pnl),
            "max_drawdown": float(max_dd),
            "profit_factor": float(profit_factor),
            "expectancy": float(expectancy),
            "avg_winner": float(avg_winner),
            "avg_loser": float(avg_loser),
            "avg_r": float(avg_r),
            "avg_hold_time": float(avg_hold),
            "positive_months": int(pos_months),
            "zero_months": int(zero_months),
            "negative_months": int(neg_months),
            "best_month": float(best_month_val),
            "worst_month": float(worst_month_val),
            "monthly_pnl": {str(k): float(v) for k, v in monthly_groups.items()},
            "monthly_report": monthly_report
        }


class MultiPositionBacktestEngine(BacktestEngine):
    """
    Simulates a multi-position backtesting engine with concurrent position caps,
    cooldowns, and portfolio-level risk limits.
    """
    def __init__(self, initial_capital: float = 10000.0, maker_fee: float = 0.0002, taker_fee: float = 0.0005, slippage: float = 0.0005, max_positions: int = 3, cooldown_candles: int = 5):
        super().__init__(initial_capital, maker_fee, taker_fee, slippage)
        self.max_positions = max_positions
        self.cooldown_candles = cooldown_candles
        self.active_positions = []
        self.pending_orders = []
        self.trades = []
        self.cooldown_tracker = {}

    def run(self, df: pd.DataFrame, portfolio_strategy, config: dict = None, risk_limit_pct: float = 0.05) -> dict:
        # Read overrides from config if present
        fee_mult = config.get("fee_mult", 1.0) if config else 1.0
        slip_mult = config.get("slip_mult", 1.0) if config else 1.0
        delay_candles = config.get("delay_candles", 0) if config else 0
        missed_fill_pct = config.get("missed_fill_pct", 0.0) if config else 0.0
        stale_skip = config.get("stale_skip", False) if config else False
        stale_limit_minutes = config.get("stale_limit_minutes", 15) if config else 15
        
        seed = config.get("seed", 42) if config else 42
        rng = np.random.default_rng(seed)
        
        current_maker_fee = self.maker_fee * fee_mult
        current_taker_fee = self.taker_fee * fee_mult
        current_slippage = self.slippage * slip_mult

        capital = self.initial_capital
        self.active_positions = []
        self.pending_orders = []
        self.trades = []
        self.cooldown_tracker = {}
        consecutive_losses_tracker = {}
        
        n = len(df)
        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        open_times = df["open_time"].values
        funding_rates = df["fundingRate"].values
        
        # Determine timeframe minutes from data
        timeframe_minutes = 60.0
        if len(open_times) > 1:
            timeframe_minutes = (open_times[1] - open_times[0]) / (60 * 1000)

        # Pre-calculate month indices lookahead-free to speed up loop
        dt_series = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_localize(None)
        bar_months = dt_series.dt.to_period("M").values
        
        # Calculate full PeriodIndex of months for monthly reporting
        start_month = bar_months[0]
        end_month = bar_months[-1]
        all_months = pd.period_range(start=start_month, end=end_month, freq="M")
        
        # Read risk parameters from config or fallback to defaults
        current_risk_limit_pct = config.get("risk_limit_pct", 1.0) if config else risk_limit_pct
        monthly_risk_limit = config.get("monthly_risk_limit", 0.025) if config else 0.025
        
        current_calendar_month = None
        starting_monthly_capital = capital
        # Pre-inspect strategy signatures to speed up loop
        import inspect
        strategies_to_query = portfolio_strategy.strategies if hasattr(portfolio_strategy, "strategies") else [portfolio_strategy]
        strat_takes_metrics = {}
        for s in strategies_to_query:
            try:
                sig_params = inspect.signature(s.get_signal).parameters
                strat_takes_metrics[id(s)] = "live_metrics" in sig_params
            except Exception:
                strat_takes_metrics[id(s)] = False
                
        for i in range(n):
            # Check month transition lookahead-free
            bar_month = bar_months[i]
            if current_calendar_month != bar_month:
                current_calendar_month = bar_month
                starting_monthly_capital = capital
                current_month_trade_count = 0
                
            # 1a. Process pending orders ready to fill at bar i
            still_pending = []
            
            # Read execution mode configuration from config or default to market
            exec_mode = config.get("execution_mode", "market") if config else "market"
            max_wait_candles = config.get("max_wait_candles", 3) if config else 3
            fallback_to_market = config.get("fallback_to_market", False) if config else False
            queue_prob = config.get("queue_prob", 0.30) if config else 0.30
            partial_fill_prob = config.get("partial_fill_prob", 0.20) if config else 0.20
            partial_fill_factor = config.get("partial_fill_factor", 0.50) if config else 0.50
            
            for order in self.pending_orders:
                # Delay candles check
                if i < order["fill_idx"]:
                    still_pending.append(order)
                    continue
                    
                # Determine if this order should execute as limit or market
                order_is_limit = False
                if exec_mode == "limit":
                    order_is_limit = True
                elif exec_mode == "hybrid":
                    # Get atr_pct at signal bar lookahead-free
                    sig_idx = order["signal_idx"]
                    atr_pct_val = df["atr_pct"].values[sig_idx] if "atr_pct" in df.columns else (df["atr_14"].values[sig_idx] / df["close"].values[sig_idx] if "atr_14" in df.columns else 0.0)
                    # If volatility is low, execute as limit, otherwise market
                    atr_pct_limit = config.get("atr_pct_limit", 0.03) if config else 0.03
                    order_is_limit = (atr_pct_val < atr_pct_limit)
                
                is_filled = False
                fill_price = None
                is_fallback_market = False
                was_adverse_selection = False
                
                if not order_is_limit:
                    # Market mode fills at the first candle after delay
                    if i == order["fill_idx"]:
                        is_filled = True
                        fill_price = opens[i]
                else:
                    # Limit mode checks if touched or below/above
                    limit_price = order.get("limit_price") or closes[order["signal_idx"]]
                    if order["side"] == "Long":
                        if lows[i] < limit_price:
                            is_filled = True
                            fill_price = limit_price
                            was_adverse_selection = True
                        elif lows[i] == limit_price:
                            if rng.random() < queue_prob:
                                is_filled = True
                                fill_price = limit_price
                    else:  # Short
                        if highs[i] > limit_price:
                            is_filled = True
                            fill_price = limit_price
                            was_adverse_selection = True
                        elif highs[i] == limit_price:
                            if rng.random() < queue_prob:
                                is_filled = True
                                fill_price = limit_price
                                
                    if not is_filled:
                        # Check wait timeout
                        wait_count = i - (order["signal_idx"] + 1)
                        if wait_count >= max_wait_candles:
                            if fallback_to_market:
                                is_filled = True
                                fill_price = opens[i]
                                is_fallback_market = True
                            else:
                                # Cancel the order
                                continue
                                
                if is_filled:
                    # Stale signal check: if the signal took too long to execute (stale skip)
                    if stale_skip:
                        time_delta_mins = (open_times[i] - open_times[order["signal_idx"] + 1]) / (60 * 1000)
                        effective_stale_limit = max(stale_limit_minutes, 1.5 * timeframe_minutes)
                        if time_delta_mins > effective_stale_limit:
                            continue
                            
                    # Concurrency check at fill time
                    if len(self.active_positions) >= self.max_positions:
                        continue
                        
                    # Risk limits check at fill time
                    current_monthly_loss = starting_monthly_capital - capital
                    current_monthly_dd = current_monthly_loss / starting_monthly_capital if starting_monthly_capital > 0 else 0.0
                    if current_monthly_dd > monthly_risk_limit:
                        continue
                        
                    current_dd = (self.initial_capital - capital) / self.initial_capital
                    if current_dd > current_risk_limit_pct:
                        continue
                        
                    # Calculate entry price with slippage (only taker market orders incur entry slippage)
                    raw_entry_price = fill_price
                    use_taker_fee = (not order_is_limit) or is_fallback_market
                    
                    if use_taker_fee:
                        entry_slip_factor = 1.0 + current_slippage if order["side"] == "Long" else 1.0 - current_slippage
                        entry_price = raw_entry_price * entry_slip_factor
                    else:
                        entry_price = raw_entry_price  # limit order, no slippage
                        
                    sl_dist = abs(closes[order["signal_idx"]] - order["stop_loss"])
                    
                    # Sizing logic: base risk 1% throttled by consecutive losses streak (exponential decay)
                    consec_losses = consecutive_losses_tracker.get(order["strategy"], 0)
                    base_risk_pct = 0.01
                    risk_pct = base_risk_pct * (0.5 ** (consec_losses // 3))
                    
                    # MTD risk throttle modes
                    risk_throttle_mode = config.get("risk_throttle_mode", "no_throttle") if config else "no_throttle"
                    emergency_pause_threshold = config.get("emergency_pause_threshold", 0.03) if config else 0.03
                    
                    # Apply emergency pause (pause if current monthly dd > threshold)
                    if current_monthly_dd >= emergency_pause_threshold:
                        risk_pct = 0.0
                    else:
                        if current_monthly_dd > 0.015: # Drawdown exceeds 1.5%
                            if risk_throttle_mode == "soft":
                                risk_pct = risk_pct * 0.75
                            elif risk_throttle_mode == "medium":
                                risk_pct = risk_pct * 0.50
                            elif risk_throttle_mode == "hard":
                                risk_pct = risk_pct * 0.25
                                
                    if risk_pct <= 0.0:
                        continue
                    
                    dyn_mult = order.get("dynamic_risk_multiplier", 1.0)
                    size = (capital * risk_pct * dyn_mult) / sl_dist if sl_dist > 0 else (capital / raw_entry_price)
                    
                    # Apply partial fill logic for limit orders
                    was_partial_fill = False
                    if order_is_limit and not is_fallback_market:
                        if rng.random() < partial_fill_prob:
                            size = size * partial_fill_factor
                            was_partial_fill = True
                            
                    if size * entry_price > capital * 5.0:
                        size = (capital * 5.0) / entry_price
                        
                    # Precision rounding
                    size = round(size, 3)
                    entry_price = round(entry_price, 1)
                    
                    fee_rate = current_taker_fee if use_taker_fee else current_maker_fee
                    entry_fee = size * entry_price * fee_rate
                    capital -= entry_fee
                    if capital <= 0:
                        capital = 0.0
                        break
                        
                    self.active_positions.append({
                        "strategy": order["strategy"],
                        "side": order["side"],
                        "entry_price": entry_price,
                        "raw_entry_price": raw_entry_price,
                        "stop_loss": order["stop_loss"],
                        "initial_stop_loss": order["stop_loss"],
                        "take_profit": order["take_profit"],
                        "size": size,
                        "entry_fee": entry_fee,
                        "entry_time": open_times[i],
                        "entry_datetime": str(pd.to_datetime(open_times[i], unit="ms", utc=True)),
                        "entry_idx": i,
                        "cumulative_funding": 0.0,
                        "trail_atr_mult": order.get("trail_atr_mult"),
                        "breakeven_atr_mult": order.get("breakeven_atr_mult"),
                        "atr_at_entry": order.get("atr"),
                        "peak_price": entry_price,
                        "is_limit": order_is_limit and not is_fallback_market,
                        "is_fallback_market": is_fallback_market,
                        "is_partial_fill": was_partial_fill,
                        "is_adverse_selection": was_adverse_selection,
                        "time_stop": order.get("time_stop"),
                        "failed_continuation_limit": order.get("failed_continuation_limit"),
                        "failed_continuation_pnl_thresh": order.get("failed_continuation_pnl_thresh", 0.0),
                        "dynamic_risk_multiplier": order.get("dynamic_risk_multiplier", 1.0)
                    })
                    current_month_trade_count += 1
                else:
                    still_pending.append(order)
            self.pending_orders = still_pending
            
            if capital <= 0:
                capital = 0.0
                break

            # 1b. Update existing positions exits and apply funding fees
            still_active = []
            for pos in self.active_positions:
                side_factor = 1.0 if pos["side"] == "Long" else -1.0
                
                # Apply funding fee if the current candle open time falls on an 8-hour boundary
                open_time = open_times[i]
                if open_time % (8 * 3600 * 1000) == 0:
                    funding_rate = funding_rates[i]
                    funding_cost = pos["size"] * opens[i] * funding_rate * side_factor
                    pos["cumulative_funding"] += funding_cost
                    capital -= funding_cost
                
                # Check for bankruptcy
                if capital <= 0:
                    capital = 0.0
                    break
                
                # Bar-by-bar Breakeven and Trailing Stop Updates on the 5m timeframe
                atr_14_val = df["atr_14"].values[i] if "atr_14" in df.columns else 0.0
                if pos["side"] == "Long":
                    pos["peak_price"] = max(pos.get("peak_price", pos["entry_price"]), highs[i])
                    
                    be_mult = pos.get("breakeven_atr_mult")
                    if be_mult is not None and be_mult > 0:
                        atr_val = pos.get("atr_at_entry") or atr_14_val
                        if pos["peak_price"] >= pos["entry_price"] + be_mult * atr_val:
                            pos["stop_loss"] = max(pos["stop_loss"], pos["entry_price"])
                            
                    trail_mult = pos.get("trail_atr_mult")
                    if trail_mult is not None and trail_mult > 0:
                        atr_val = pos.get("atr_at_entry") or atr_14_val
                        trail_stop = pos["peak_price"] - trail_mult * atr_val
                        pos["stop_loss"] = max(pos["stop_loss"], trail_stop)
                else:  # Short
                    pos["peak_price"] = min(pos.get("peak_price", pos["entry_price"]), lows[i])
                    
                    be_mult = pos.get("breakeven_atr_mult")
                    if be_mult is not None and be_mult > 0:
                        atr_val = pos.get("atr_at_entry") or atr_14_val
                        if pos["peak_price"] <= pos["entry_price"] - be_mult * atr_val:
                            pos["stop_loss"] = min(pos["stop_loss"], pos["entry_price"])
                            
                    trail_mult = pos.get("trail_atr_mult")
                    if trail_mult is not None and trail_mult > 0:
                        atr_val = pos.get("atr_at_entry") or atr_14_val
                        trail_stop = pos["peak_price"] + trail_mult * atr_val
                        pos["stop_loss"] = min(pos["stop_loss"], trail_stop)

                # Check custom time stop and failed continuation exits
                hold_candles = i - pos["entry_idx"]
                time_stop = pos.get("time_stop")
                failed_cont_limit = pos.get("failed_continuation_limit")
                failed_cont_pnl_thresh = pos.get("failed_continuation_pnl_thresh", 0.0)
                
                is_time_stop_hit = time_stop is not None and hold_candles >= time_stop
                is_failed_cont_hit = False
                if failed_cont_limit is not None and hold_candles >= failed_cont_limit:
                    current_close = closes[i]
                    current_gross = pos["size"] * (current_close - pos["entry_price"]) * side_factor
                    if current_gross <= failed_cont_pnl_thresh:
                        is_failed_cont_hit = True

                # Check stop loss and take profit hits (handling gap-ups and gap-downs robustly)
                is_sl_hit = (lows[i] <= pos["stop_loss"]) if pos["side"] == "Long" else (highs[i] >= pos["stop_loss"])
                is_tp_hit = (highs[i] >= pos["take_profit"]) if pos["side"] == "Long" else (lows[i] <= pos["take_profit"])
                
                if is_sl_hit or is_tp_hit or is_time_stop_hit or is_failed_cont_hit:
                    # In case both are hit, we take SL for safety
                    if is_sl_hit or is_tp_hit:
                        raw_exit_price = pos["stop_loss"] if is_sl_hit else pos["take_profit"]
                        reason = "SL Hit" if is_sl_hit else "TP Hit"
                    else:
                        raw_exit_price = closes[i]
                        reason = "Time Stop Hit" if is_time_stop_hit else "Failed Continuation Exit"
                    
                    # Apply exit slippage (slippage hurts us)
                    # For Long exit: sell market -> raw_exit_price * (1 - current_slippage)
                    # For Short exit: buy market -> raw_exit_price * (1 + current_slippage)
                    exit_slip_factor = 1.0 - current_slippage if pos["side"] == "Long" else 1.0 + current_slippage
                    exit_price = raw_exit_price * exit_slip_factor
                    
                    gross_pnl = pos["size"] * (exit_price - pos["entry_price"]) * side_factor
                    exit_fee = pos["size"] * exit_price * current_taker_fee
                    net_pnl = gross_pnl - pos["entry_fee"] - exit_fee - pos["cumulative_funding"]
                    capital_to_save = capital + gross_pnl - exit_fee
                    capital = max(0.0, capital_to_save)
                    
                    # Update consecutive losses tracker
                    strat_name = pos["strategy"]
                    if net_pnl <= 0:
                        consecutive_losses_tracker[strat_name] = consecutive_losses_tracker.get(strat_name, 0) + 1
                    else:
                        consecutive_losses_tracker[strat_name] = 0
                    
                    entry_slip = abs(pos["entry_price"] - pos["raw_entry_price"]) * pos["size"]
                    exit_slip = abs(exit_price - raw_exit_price) * pos["size"]
                    total_slip = entry_slip + exit_slip
                    
                    self.trades.append({
                        "strategy": pos["strategy"],
                        "entry_time": pos["entry_time"],
                        "entry_datetime": pos["entry_datetime"],
                        "exit_time": open_times[i],
                        "exit_datetime": str(pd.to_datetime(open_times[i], unit="ms", utc=True)),
                        "side": pos["side"],
                        "entry_price": pos["entry_price"],
                        "exit_price": exit_price,
                        "raw_exit_price": raw_exit_price,
                        "stop_loss": pos["stop_loss"],
                        "take_profit": pos["take_profit"],
                        "size": pos["size"],
                        "gross_pnl": gross_pnl,
                        "fees": pos["entry_fee"] + exit_fee,
                        "entry_slippage": entry_slip,
                        "exit_slippage": exit_slip,
                        "slippage": total_slip,
                        "funding": pos["cumulative_funding"],
                        "net_pnl": net_pnl,
                        "capital_after": capital,
                        "reason": reason,
                        "R": gross_pnl / (pos["size"] * abs(pos["entry_price"] - pos["initial_stop_loss"])) if abs(pos["entry_price"] - pos["initial_stop_loss"]) > 0 else 0.0,
                        "hold_candles": i - pos["entry_idx"],
                        "is_limit": pos.get("is_limit", False),
                        "is_fallback_market": pos.get("is_fallback_market", False),
                        "is_partial_fill": pos.get("is_partial_fill", False),
                        "is_adverse_selection": pos.get("is_adverse_selection", False)
                    })
                    self.cooldown_tracker[pos["strategy"]] = i
                else:
                    still_active.append(pos)
            
            self.active_positions = still_active
            
            if capital <= 0:
                capital = 0.0
                break
                
            # 2. Check for new signals
            # Compute current monthly loss & drawdown for live_metrics
            current_monthly_loss = starting_monthly_capital - capital
            current_monthly_dd = current_monthly_loss / starting_monthly_capital if starting_monthly_capital > 0 else 0.0
            
            for strat in strategies_to_query:
                strat_name = getattr(strat, "name", "Unknown")
                
                live_metrics = {
                    "monthly_trade_count": current_month_trade_count,
                    "monthly_dd": current_monthly_dd,
                    "consecutive_losses": consecutive_losses_tracker.get(strat_name, 0),
                    "capital": capital
                }
                
                # Query strategy for signal
                if strat_takes_metrics.get(id(strat), False):
                    sig = strat.get_signal(df, i, live_metrics=live_metrics)
                else:
                    sig = strat.get_signal(df, i)
                    
                if sig is not None:
                    strat_name = sig.get("strategy_name", getattr(strat, "name", "Unknown"))
                    
                    # Concurrency limit check
                    if len(self.active_positions) >= self.max_positions:
                        continue
                        
                    # Cooldown check
                    last_exit = self.cooldown_tracker.get(strat_name, -999)
                    if i - last_exit < self.cooldown_candles:
                        continue
                        
                    # Month-to-date risk limit check
                    if current_monthly_dd > monthly_risk_limit:
                        continue
                        
                    # Risk limit check (global drawdown limit)
                    current_dd = (self.initial_capital - capital) / self.initial_capital
                    if current_dd > current_risk_limit_pct:
                        continue
                    
                    # Missed fill check
                    if missed_fill_pct > 0.0 and rng.random() < missed_fill_pct:
                        continue
                        
                    # Queue order in pending orders
                    fill_idx = i + 1 + delay_candles
                    if fill_idx < n:
                        self.pending_orders.append({
                            "strategy": strat_name,
                            "side": sig["side"],
                            "stop_loss": sig["stop_loss"],
                            "take_profit": sig["take_profit"],
                            "fill_idx": fill_idx,
                            "signal_idx": i,
                            "trail_atr_mult": sig.get("trail_atr_mult", getattr(strat, "params", {}).get("trail_atr_mult")),
                            "breakeven_atr_mult": sig.get("breakeven_atr_mult", getattr(strat, "params", {}).get("breakeven_atr_mult")),
                            "atr": df["atr_14"].values[i] if "atr_14" in df.columns else (sig.get("atr") or 0.0),
                            "time_stop": sig.get("time_stop", getattr(strat, "params", {}).get("time_stop")),
                            "failed_continuation_limit": sig.get("failed_continuation_limit", getattr(strat, "params", {}).get("failed_continuation_limit")),
                            "failed_continuation_pnl_thresh": sig.get("failed_continuation_pnl_thresh", getattr(strat, "params", {}).get("failed_continuation_pnl_thresh", 0.0)),
                            "dynamic_risk_multiplier": sig.get("dynamic_risk_multiplier", getattr(strat, "params", {}).get("dynamic_risk_multiplier", 1.0))
                        })
                        
        # Force close remaining open positions at the end of backtest
        for pos in self.active_positions:
            side_factor = 1.0 if pos["side"] == "Long" else -1.0
            exit_price = closes[n-1]
            gross_pnl = pos["size"] * (exit_price - pos["entry_price"]) * side_factor
            exit_fee = pos["size"] * exit_price * current_taker_fee
            net_pnl = gross_pnl - pos["entry_fee"] - exit_fee - pos["cumulative_funding"]
            capital += gross_pnl - exit_fee
            capital = max(0.0, capital)
            
            entry_slip = abs(pos["entry_price"] - pos["raw_entry_price"]) * pos["size"]
            self.trades.append({
                "strategy": pos["strategy"],
                "entry_time": pos["entry_time"],
                "entry_datetime": pos["entry_datetime"],
                "exit_time": open_times[n-1],
                "exit_datetime": str(pd.to_datetime(open_times[n-1], unit="ms", utc=True)),
                "side": pos["side"],
                "entry_price": pos["entry_price"],
                "exit_price": exit_price,
                "raw_exit_price": exit_price,
                "stop_loss": pos["stop_loss"],
                "take_profit": pos["take_profit"],
                "size": pos["size"],
                "gross_pnl": gross_pnl,
                "fees": pos["entry_fee"] + exit_fee,
                "entry_slippage": entry_slip,
                "exit_slippage": 0.0,
                "slippage": entry_slip,
                "funding": pos["cumulative_funding"],
                "net_pnl": net_pnl,
                "capital_after": capital,
                "reason": "Force Close",
                "R": gross_pnl / (pos["size"] * abs(pos["entry_price"] - pos["initial_stop_loss"])) if abs(pos["entry_price"] - pos["initial_stop_loss"]) > 0 else 0.0,
                "hold_candles": n - 1 - pos["entry_idx"]
            })
            
        trades_df = pd.DataFrame(self.trades)
        metrics = self._calculate_metrics(trades_df, capital, all_months)
        
        return {
            "metrics": metrics,
            "trades": trades_df
        }
