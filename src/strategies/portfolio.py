import pandas as pd
from src.strategies.base import BaseStrategy

class PortfolioStrategy(BaseStrategy):
    """
    A portfolio strategy that combines signals from multiple sub-strategies.
    Implements signal consolidation, conflict resolution, regime filters,
    and adaptive zero-month rescue.
    """
    def __init__(self, strategies: list, conflict_rule: str = "cancel", 
                 fusion_mode: str = "union", min_agreement: int = 2, 
                 regime_switching: bool = False, zero_month_rescue: bool = True):
        super().__init__(
            name=f"Portfolio_{'_'.join([s.name for s in strategies])}",
            hypothesis=f"Combine {len(strategies)} strategies to diversify regimes and smooth returns."
        )
        self.strategies = strategies
        self.conflict_rule = conflict_rule
        self.fusion_mode = fusion_mode
        self.min_agreement = min_agreement
        self.regime_switching = regime_switching
        self.zero_month_rescue = zero_month_rescue

        # Cache signature check for live_metrics to avoid performance bottleneck in loop
        import inspect
        for s in strategies:
            has_lm = "live_metrics" in inspect.signature(s.get_signal).parameters
            s._takes_live_metrics = has_lm

    def get_strategy_regimes(self, template_type: str) -> list:
        # Returns a list of regime flags under which this strategy is active
        if template_type in ["trend_pullback", "trend_breakout", "london_continuation", "funding_trend_continuation", "volume_impulse_continuation", "mtf_breakout"]:
            return ["regime_bull_trend", "regime_bear_trend"]
        elif template_type in ["bollinger_mean_reversion", "vwap_mean_reversion", "rsi_exhaustion_reversal", "wick_rejection_reversal", "new_york_reversal"]:
            return ["regime_sideways_range"]
        elif template_type in ["range_compression_breakout", "volatility_squeeze_breakout"]:
            return ["regime_vol_compression"]
        elif template_type in ["bollinger_expansion_breakout", "atr_volatility_expansion"]:
            return ["regime_vol_expansion"]
        elif template_type in ["funding_extreme_reversal", "liquidity_sweep_funding_reversal", "sweep_reversal"]:
            return ["regime_funding_extreme"]
        return None

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        signals = []
        
        # 1. MTD Adaptive Fusion Check (Zero-Month Rescue)
        monthly_trades = live_metrics.get("monthly_trade_count", 0) if live_metrics else 0
        
        # Determine day of month lookahead-free
        if "days_of_month" in df.columns:
            day_of_month = df["days_of_month"].values[i]
        else:
            # Parse day from open_time
            day_of_month = pd.to_datetime(df["open_time"].values[i], unit="ms", utc=True).day
            
        rescue_active = False
        if self.zero_month_rescue:
            # Activate if day >= 10 and no trades, or day >= 15 and < 6 trades
            rescue_active = (day_of_month >= 10 and monthly_trades == 0) or (day_of_month >= 15 and monthly_trades < 6)

        for strat in self.strategies:
            t_type = getattr(strat, "params", {}).get("template_type", "")
            
            # If it's the low-activity filler strategy, only query it if rescue is active!
            if t_type == "low_activity_filler":
                if not rescue_active:
                    continue
            
            # 2. Priority Routing & Regime-based Switching
            if self.regime_switching:
                active_regimes = self.get_strategy_regimes(t_type)
                if active_regimes:
                    # Check if the market is currently in any of the strategy's preferred regimes
                    in_preferred_regime = False
                    for reg in active_regimes:
                        if reg in df.columns and df[reg].values[i]:
                            in_preferred_regime = True
                            break
                    # If not in preferred regime, and we are not in rescue mode for this filler, skip it
                    if not in_preferred_regime:
                        continue

            if getattr(strat, "_takes_live_metrics", False):
                sig = strat.get_signal(df, i, live_metrics=live_metrics)
            else:
                sig = strat.get_signal(df, i)
                
            if sig is not None:
                signals.append(sig)

        if not signals:
            return None

        # Count Long and Short signals
        longs = [s for s in signals if s["side"] == "Long"]
        shorts = [s for s in signals if s["side"] == "Short"]

        # 3. Signal Fusion Modes: Intersection vs Union
        if self.fusion_mode == "intersection":
            if len(longs) >= self.min_agreement and len(shorts) < self.min_agreement:
                best_sig = max(longs, key=lambda x: x["stop_loss"])
                best_sig["reason"] = f"Portfolio Long (Intersection): {', '.join([s['reason'] for s in longs])}"
                return best_sig
            elif len(shorts) >= self.min_agreement and len(longs) < self.min_agreement:
                best_sig = min(shorts, key=lambda x: x["stop_loss"])
                best_sig["reason"] = f"Portfolio Short (Intersection): {', '.join([s['reason'] for s in shorts])}"
                return best_sig
            else:
                # Conflict or insufficient agreement
                return None
                
        # Default: Union mode
        if longs and shorts:
            if self.conflict_rule == "cancel":
                return None
            elif self.conflict_rule == "long_priority":
                return longs[0]
            elif self.conflict_rule == "short_priority":
                return shorts[0]

        if longs:
            # Consolidate multiple long signals (use the one with the tightest stop loss for safety)
            best_sig = max(longs, key=lambda x: x["stop_loss"])
            best_sig["reason"] = f"Portfolio Long: {', '.join([s['reason'] for s in longs])}"
            return best_sig

        if shorts:
            # Consolidate multiple short signals (use the one with the tightest stop loss for safety)
            best_sig = min(shorts, key=lambda x: x["stop_loss"])
            best_sig["reason"] = f"Portfolio Short: {', '.join([s['reason'] for s in shorts])}"
            return best_sig

        return None

    def get_param_grid(self) -> dict:
        return {}


class FusionOfFusionsStrategy(BaseStrategy):
    """
    Combines multiple sub-portfolios or strategies.
    Implements dynamic routing based on live metrics, conflict handling,
    and logs detailed signal routing decisions.
    """
    def __init__(self, fusions: dict, conflict_rule: str = "cancel", 
                 fusion_mode: str = "union", min_agreement: int = 2):
        super().__init__(
            name=f"FoF_{'_'.join(fusions.keys())}",
            hypothesis="Combine multiple strategy fusions using regime and activity-based dynamic routing."
        )
        self.fusions = fusions
        self.conflict_rule = conflict_rule
        self.fusion_mode = fusion_mode
        self.min_agreement = min_agreement
        self.signal_logs = []

        # Cache signature checks to avoid inspect bottleneck in hot loop
        import inspect
        for name, strat in fusions.items():
            has_lm = "live_metrics" in inspect.signature(strat.get_signal).parameters
            strat._takes_live_metrics = has_lm

    def get_param_grid(self) -> dict:
        return {}

    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        if not i or not hasattr(self, "_cached_days"):
            self.signal_logs = []
            # Cache datetime strings and days vectorized
            self._cached_datetimes = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.strftime("%Y-%m-%d %H:%M:%S").values
            self._cached_days = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.day.values
            
        signals = []
        monthly_trades = live_metrics.get("monthly_trade_count", 0) if live_metrics else 0
        monthly_dd = live_metrics.get("monthly_dd", 0.0) if live_metrics else 0.0
        consec_losses = live_metrics.get("consecutive_losses", 0) if live_metrics else 0
        
        # Day of month lookahead-free cached lookup
        day_of_month = self._cached_days[i]
            
        current_hour = df["hour"].values[i] if "hour" in df.columns else 0
        
        # Determine regime
        regime_state = "Unknown"
        for reg in ["regime_bull_trend", "regime_bear_trend", "regime_sideways_range", "regime_vol_compression", "regime_vol_expansion", "regime_funding_extreme", "regime_toxic_chop"]:
            if reg in df.columns and df[reg].values[i]:
                regime_state = reg
                break

        for name, fusion_strat in self.fusions.items():
            active = True
            reason_inactive = ""
            
            # Rule 1: Toxicity Throttle (disable sub-portfolio if too many losses or too much monthly DD)
            if name in ["trend", "range", "liquidity", "funding"] and consec_losses >= 3:
                active = False
                reason_inactive = f"toxicity throttle: consecutive losses ({consec_losses}) >= 3"
            elif name in ["trend", "range", "liquidity"] and monthly_dd >= 0.02:
                active = False
                reason_inactive = f"toxicity throttle: monthly DD ({monthly_dd:.2%}) >= 2%"
            
            # Rule 1b: Old Activity Rule compatibility
            elif name == "activity":
                if monthly_trades >= 5:
                    active = False
                    reason_inactive = f"monthly trades ({monthly_trades}) >= 5"
            
            # Rule 2: Zero Rescue (only active if zero rescue criteria met)
            elif name == "zero_rescue":
                rescue_needed = (day_of_month >= 10 and monthly_trades == 0) or (day_of_month >= 15 and monthly_trades < 6)
                if not rescue_needed:
                    active = False
                    reason_inactive = "zero-rescue criteria not met"
                elif monthly_dd >= 0.02:
                    active = False
                    reason_inactive = "zero-rescue disabled due to monthly DD >= 2%"
            
            # Rule 3: Defensive Cost-Control (active only if monthly DD >= 1.5%)
            elif name == "defensive":
                if monthly_dd < 0.015:
                    active = False
                    reason_inactive = f"monthly DD ({monthly_dd:.2%}) < 1.5%"
            
            # Rule 4: Regime Gating for Trend & Range sub-portfolios
            elif name == "trend":
                # Only active in trending or expanding regimes
                is_trend = "regime_bull_trend" in df.columns and (df["regime_bull_trend"].values[i] or df["regime_bear_trend"].values[i] or df["regime_vol_expansion"].values[i])
                if not is_trend:
                    active = False
                    reason_inactive = "not in trending regime"
            elif name == "range":
                # Only active in sideways or compressed regimes
                is_range = "regime_sideways_range" in df.columns and (df["regime_sideways_range"].values[i] or df["regime_vol_compression"].values[i])
                if not is_range:
                    active = False
                    reason_inactive = "not in range regime"
                    
            if not active:
                self.signal_logs.append({
                    "time": int(df["open_time"].values[i]),
                    "datetime": self._cached_datetimes[i],
                    "sub_portfolio": name,
                    "signal_type": "None",
                    "action": "Rejected",
                    "reason": f"Skipped: {reason_inactive}",
                    "monthly_trades": int(monthly_trades),
                    "monthly_dd": float(monthly_dd),
                    "regime": regime_state
                })
                continue
                
            takes_metrics = getattr(fusion_strat, "_takes_live_metrics", False)
            if takes_metrics:
                sig = fusion_strat.get_signal(df, i, live_metrics=live_metrics)
            else:
                sig = fusion_strat.get_signal(df, i)
                
            if sig is not None:
                sig["fusion_source"] = name
                signals.append(sig)
                
                self.signal_logs.append({
                    "time": int(df["open_time"].values[i]),
                    "datetime": self._cached_datetimes[i],
                    "sub_portfolio": name,
                    "signal_type": sig["side"],
                    "action": "Pending Fusion",
                    "reason": f"Signal generated: {sig.get('reason','')}",
                    "monthly_trades": int(monthly_trades),
                    "monthly_dd": float(monthly_dd),
                    "regime": regime_state
                })

        if not signals:
            return None

        # Consolidate signals
        longs = [s for s in signals if s["side"] == "Long"]
        shorts = [s for s in signals if s["side"] == "Short"]

        final_sig = None
        conflict_action = "Union"
        
        if longs and shorts:
            conflict_action = "Conflict"
            if self.conflict_rule == "cancel":
                final_sig = None
            elif self.conflict_rule == "long_priority":
                final_sig = longs[0]
            elif self.conflict_rule == "short_priority":
                final_sig = shorts[0]
        else:
            if longs:
                final_sig = max(longs, key=lambda x: x["stop_loss"])
            elif shorts:
                final_sig = min(shorts, key=lambda x: x["stop_loss"])

        action_taken = "Accepted" if final_sig is not None else "Rejected"
        final_reason = f"Executed: {final_sig.get('reason','')}" if final_sig else f"Conflict cancel: {len(longs)}L vs {len(shorts)}S"
        
        self.signal_logs.append({
            "time": int(df["open_time"].values[i]),
            "datetime": self._cached_datetimes[i],
            "sub_portfolio": "FoF_Consolidated",
            "signal_type": final_sig["side"] if final_sig else "None",
            "action": action_taken,
            "reason": final_reason,
            "monthly_trades": int(monthly_trades),
            "monthly_dd": float(monthly_dd),
            "regime": regime_state
        })

        return final_sig


