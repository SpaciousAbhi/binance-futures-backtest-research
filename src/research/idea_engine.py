"""
ResearchIdeaEngine — Phase 11

Automatically generates, ranks, and tests new strategy ideas from:
- Negative-month forensics
- Trade logs
- Candidate overlap matrices
- Failure category patterns

Each idea includes: hypothesis, expected benefit, failure category, live-compat check,
no-lookahead risk, implementation plan, acceptance metrics, rejection criteria.
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


class ResearchIdea:
    """Represents a single generated research idea with full metadata."""

    def __init__(
        self,
        idea_id: str,
        name: str,
        hypothesis: str,
        failure_category: str,
        expected_benefit: str,
        affected_months: List[str],
        live_compatible: bool,
        lookahead_risk: str,
        implementation_plan: str,
        acceptance_metrics: Dict[str, Any],
        rejection_criteria: Dict[str, Any],
        required_data: List[str],
        priority_score: float = 0.0,
        status: str = "GENERATED",
        complexity_score: float = 3.0,
        overfit_risk_score: float = 3.0,
        live_compatibility_score: float = 4.0,
        when_it_fails: str = "Chop/flat regimes",
        regime_gate: str = "ADX > 20",
        entry_rule: str = "Close above breakout level",
        exit_rule: str = "Trailing stop",
        stop_rule: str = "2.0x ATR",
        expected_frequency: str = "10 trades/month",
        cost_sensitivity: str = "Low"
    ):
        self.idea_id = idea_id
        self.name = name
        self.hypothesis = hypothesis
        self.failure_category = failure_category
        self.expected_benefit = expected_benefit
        self.affected_months = affected_months
        self.live_compatible = live_compatible
        self.lookahead_risk = lookahead_risk
        self.implementation_plan = implementation_plan
        self.acceptance_metrics = acceptance_metrics
        self.rejection_criteria = rejection_criteria
        self.required_data = required_data
        self.priority_score = priority_score
        self.status = status
        self.complexity_score = complexity_score
        self.overfit_risk_score = overfit_risk_score
        self.live_compatibility_score = live_compatibility_score
        self.test_result = None  # Populated after testing
        self.when_it_fails = when_it_fails
        self.regime_gate = regime_gate
        self.entry_rule = entry_rule
        self.exit_rule = exit_rule
        self.stop_rule = stop_rule
        self.expected_frequency = expected_frequency
        self.cost_sensitivity = cost_sensitivity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "idea_id": self.idea_id,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "failure_category": self.failure_category,
            "expected_benefit": self.expected_benefit,
            "affected_months": self.affected_months,
            "live_compatible": self.live_compatible,
            "lookahead_risk": self.lookahead_risk,
            "implementation_plan": self.implementation_plan,
            "acceptance_metrics": self.acceptance_metrics,
            "rejection_criteria": self.rejection_criteria,
            "required_data": self.required_data,
            "priority_score": self.priority_score,
            "status": self.status,
            "complexity_score": self.complexity_score,
            "overfit_risk_score": self.overfit_risk_score,
            "live_compatibility_score": self.live_compatibility_score,
            "test_result": self.test_result,
            "when_it_fails": self.when_it_fails,
            "regime_gate": self.regime_gate,
            "entry_rule": self.entry_rule,
            "exit_rule": self.exit_rule,
            "stop_rule": self.stop_rule,
            "expected_frequency": self.expected_frequency,
            "cost_sensitivity": self.cost_sensitivity
        }


class ResearchIdeaEngine:
    """
    Generates, ranks, and tracks testable research ideas from forensics data.
    Produces research_ideas.json and research_ideas_leaderboard.md.
    """

    FAILURE_CATEGORIES = {
        "false_breakout": "Price broke out but immediately reversed — signal triggered but trade lost.",
        "chop": "Low-conviction sideways price action with many small whipsaws.",
        "cost_erosion": "Gross PnL positive but fees+slippage+funding consumed all profit.",
        "low_activity": "Zero or very few trades in the month — no opportunity captured.",
        "trend_exhaustion": "Trade entered at end of trend; reversal immediately followed.",
        "weak_adx": "ADX < 20 at signal time — low directional conviction.",
        "volume_weakness": "Volume not confirming breakout — breakout lacked participation.",
        "stop_issue": "Stop-loss too tight — hit by normal volatility before target reached.",
        "target_issue": "Take-profit too far — never reached; trade timed out or reversed.",
        "funding_drag": "Positive funding rate eroded PnL for long positions (or vice versa).",
        "wrong_fusion_priority": "FoF routed signal to wrong sub-portfolio given market conditions.",
        "risk_too_high": "Standard risk sizing too aggressive given low-quality setup.",
    }

    def __init__(self):
        self.ideas: List[ResearchIdea] = []
        self._idea_counter = 0

    def _make_id(self, prefix: str) -> str:
        self._idea_counter += 1
        return f"IDEA_{prefix}_{self._idea_counter:03d}"

    def classify_negative_month(self, month_data: Dict[str, Any]) -> str:
        """
        Classifies the failure category of a negative month based on forensics data.
        Uses only live-known information (no future candles).
        """
        trades = month_data.get("trades", 0)
        gross_pnl = month_data.get("gross_pnl", 0.0)
        net_pnl = month_data.get("net_pnl", 0.0)
        fees = month_data.get("fees", 0.0)
        slippage = month_data.get("slippage", 0.0)
        drawdown = month_data.get("drawdown", 0.0)

        if trades == 0:
            return "low_activity"

        # Cost erosion: gross was positive but net is negative
        if gross_pnl > 0 and net_pnl < 0:
            if (fees + slippage) > abs(gross_pnl) * 0.8:
                return "cost_erosion"

        # Few trades, high per-trade loss
        if trades <= 3 and net_pnl < -200:
            return "false_breakout"

        # Many trades, small per-trade loss
        if trades >= 10 and drawdown < 3.0:
            return "chop"

        # Default: false breakout
        return "false_breakout"

    def generate_ideas_from_negative_months(
        self,
        negative_months: List[Dict[str, Any]],
        candidate_name: str = "FoF Champion"
    ) -> List[ResearchIdea]:
        """
        Generates ideas for each failure category found across negative months.
        """
        generated = []

        # Classify all months
        category_months: Dict[str, List[str]] = {}
        for m in negative_months:
            cat = self.classify_negative_month(m)
            month_label = m.get("month", "unknown")
            category_months.setdefault(cat, []).append(month_label)

        # Generate one idea per category
        for cat, months in category_months.items():
            ideas = self._generate_ideas_for_category(cat, months, candidate_name)
            generated.extend(ideas)

        return generated

    def _generate_ideas_for_category(
        self, category: str, affected_months: List[str], candidate_name: str
    ) -> List[ResearchIdea]:
        """Returns a list of concrete, testable ideas for the given failure category."""
        ideas = []

        if category == "false_breakout":
            ideas.append(ResearchIdea(
                idea_id=self._make_id("FB"),
                name="ADX Slope Gate for Breakouts",
                hypothesis=(
                    "False breakouts occur when ADX slope is flat or declining. "
                    "Adding a minimum ADX slope (>0.5 over 3 bars) before taking BB expansion signals "
                    "should reduce false breakout frequency without eliminating quality signals."
                ),
                failure_category="false_breakout",
                expected_benefit="Reduce losing trades in false-breakout months by 30-50%",
                affected_months=affected_months,
                live_compatible=True,
                lookahead_risk="LOW: ADX computed on closed candles only, slope uses previous bars",
                implementation_plan=(
                    "Modify bollinger_expansion_breakout template: require adx_slope_3 > 0.5. "
                    "Test adx_slope_window=[1,3,5] and adx_slope_thresh=[0.0,0.5,1.0]. "
                    "Metric: fewer false-breakout months, same or better PF."
                ),
                acceptance_metrics={
                    "negative_month_delta": "< 0",
                    "pf_delta": "> 0.0",
                    "oos_pnl_delta": "> -500",
                    "trade_count_delta": "> -50"
                },
                rejection_criteria={
                    "oos_pf": "< 1.0",
                    "trade_count": "< 350",
                    "negative_months_increase": "> 3"
                },
                required_data=["adx_14", "adx_slope_3", "bb_width", "bb_upper", "bb_lower"],
                priority_score=9.5
            ))

            ideas.append(ResearchIdea(
                idea_id=self._make_id("FB"),
                name="Volume Trend Confirmation Gate",
                hypothesis=(
                    "False breakouts lack volume conviction. Requiring current volume >= 1.3x the 20-bar MA "
                    "before taking BB expansion signals should filter out low-participation breakouts. "
                    "Expected to reduce false breakouts by 25-40%."
                ),
                failure_category="false_breakout",
                expected_benefit="Reduce false-breakout month losses, improve PF",
                affected_months=affected_months,
                live_compatible=True,
                lookahead_risk="LOW: Volume and MA computed on closed candles only",
                implementation_plan=(
                    "Test volume_trend_thresh=[1.0, 1.2, 1.3, 1.5] on bollinger_expansion_breakout. "
                    "Measure negative month reduction vs trade count reduction. "
                    "Accept if negative months drop without major trade count loss."
                ),
                acceptance_metrics={
                    "negative_month_delta": "<= -2",
                    "trade_count_min": 380,
                    "pf_min": 1.25
                },
                rejection_criteria={
                    "oos_pf": "< 1.0",
                    "trade_count": "< 300"
                },
                required_data=["volume", "volume_trend"],
                priority_score=8.5
            ))

            ideas.append(ResearchIdea(
                idea_id=self._make_id("FB"),
                name="EMA Reclaim Entry (Pullback After Breakout)",
                hypothesis=(
                    "Instead of entering immediately on the BB breakout candle, "
                    "wait for price to pull back to EMA(50) and reclaim it from the breakout side. "
                    "This gives a tighter stop and confirms the breakout is not a false break."
                ),
                failure_category="false_breakout",
                expected_benefit="Tighter stops, better R/R, fewer false-breakout entries",
                affected_months=affected_months,
                live_compatible=True,
                lookahead_risk="LOW: Entry is a separate candle after the signal candle",
                implementation_plan=(
                    "New template type: trend_pullback_ema_reclaim. "
                    "Signal: previous candle broke BB upper/lower + current candle touches EMA(50) and reclaims. "
                    "Test standalone and as complement to FoF champion."
                ),
                acceptance_metrics={
                    "standalone_pf_min": 1.10,
                    "standalone_pnl_min": 2000.0,
                    "oos_pnl_min": 500.0
                },
                rejection_criteria={
                    "trade_count": "< 50",
                    "oos_pf": "< 1.0"
                },
                required_data=["ema_50", "bb_upper", "bb_lower", "close"],
                priority_score=8.0
            ))

        elif category == "cost_erosion":
            ideas.append(ResearchIdea(
                idea_id=self._make_id("CE"),
                name="Cost-Aware TP Minimum Filter",
                hypothesis=(
                    "Cost-erosion months have positive gross PnL but negative net PnL. "
                    "Adding a minimum TP distance of 2.5x expected cost (fees+slippage) "
                    "before entering should prevent taking trades where costs will consume profits."
                ),
                failure_category="cost_erosion",
                expected_benefit="Eliminate cost-erosion losses without major trade count reduction",
                affected_months=affected_months,
                live_compatible=True,
                lookahead_risk="NONE: Cost calculation uses only entry price and parameters",
                implementation_plan=(
                    "Activate cost_to_atr_mult parameter (already exists in UniversalStrategyTemplate). "
                    "Test cost_to_atr_mult=[1.5, 2.0, 2.5] on FoF champion configuration."
                ),
                acceptance_metrics={
                    "cost_erosion_months_eliminated": "> 0",
                    "pf_delta": "> 0.02",
                    "oos_pnl_delta": "> -300"
                },
                rejection_criteria={
                    "trade_count": "< 400",
                    "negative_months_increase": "> 5"
                },
                required_data=["atr_14", "close"],
                priority_score=7.0
            ))

        elif category == "low_activity":
            ideas.append(ResearchIdea(
                idea_id=self._make_id("LA"),
                name="VWAP Reclaim Zero-Month Rescue",
                hypothesis=(
                    "Zero-activity months occur when BB expansion signals don't trigger "
                    "because price stays inside the bands. A VWAP reclaim signal (price returning "
                    "from below VWAP back above it with RSI confirmation) provides a complementary "
                    "entry mechanism active only in low-activity periods."
                ),
                failure_category="low_activity",
                expected_benefit="Eliminate 1 remaining zero month (2023-07)",
                affected_months=affected_months,
                live_compatible=True,
                lookahead_risk="LOW: VWAP computed on daily-reset cumsum, no future data",
                implementation_plan=(
                    "New template: vwap_reclaim_continuation. "
                    "Signal: day >= 10, monthly_trades == 0, close crosses above VWAP, RSI > 45. "
                    "Only activates in zero-rescue mode (live_metrics check). "
                    "Standalone expectancy must be positive or proven complement."
                ),
                acceptance_metrics={
                    "zero_months_eliminated": 1,
                    "standalone_pnl": "> 0",
                    "pf_delta": "> -0.05"
                },
                rejection_criteria={
                    "negative_months_increase": "> 5",
                    "dd_delta": "> 3.0"
                },
                required_data=["vwap", "rsi_14", "close", "days_of_month", "monthly_trade_count"],
                priority_score=9.0
            ))

        elif category == "chop":
            ideas.append(ResearchIdea(
                idea_id=self._make_id("CH"),
                name="Chop Regime Risk Halving",
                hypothesis=(
                    "Chop months have many small losing trades. Instead of skipping chop entirely, "
                    "halving the position size when regime_toxic_chop is active should reduce losses "
                    "while preserving the few winning trades that still occur."
                ),
                failure_category="chop",
                expected_benefit="Reduce chop-month losses by 40-60%",
                affected_months=affected_months,
                live_compatible=True,
                lookahead_risk="LOW: regime_toxic_chop flag computed on closed candles",
                implementation_plan=(
                    "Add regime_risk_mult parameter to MultiPositionBacktestEngine. "
                    "When regime_toxic_chop=True, apply risk_mult=0.5 to position sizing. "
                    "Test on FoF champion and measure chop-month P&L delta."
                ),
                acceptance_metrics={
                    "chop_month_pnl_delta": "> 0",
                    "dd_delta": "< 2.0",
                    "oos_pnl_delta": "> -200"
                },
                rejection_criteria={
                    "pf_delta": "< -0.10",
                    "trade_count_delta": "< -100"
                },
                required_data=["regime_toxic_chop"],
                priority_score=7.5
            ))

        return ideas

    def generate_ideas_for_zero_month_elimination(self, zero_month: str) -> List[ResearchIdea]:
        """Generates specific ideas for eliminating a known zero-trade month."""
        ideas = []

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ZM"),
            name="Volatility Compression Release for Zero Months",
            hypothesis=(
                f"Month {zero_month} had zero trades because BB expansion never triggered. "
                "A volatility compression release signal (BB width below 20th percentile for 5+ bars, "
                "then first close outside bands) should catch range compressions that "
                "precede expansion moves."
            ),
            failure_category="low_activity",
            expected_benefit=f"Eliminate zero-trade month {zero_month}",
            affected_months=[zero_month],
            live_compatible=True,
            lookahead_risk="LOW: BB width percentile computed on rolling historical window",
            implementation_plan=(
                "New template: volatility_compression_release. "
                "Signal: bb_width_pct < 0.20 for >= 5 consecutive bars, then close > bb_upper "
                "or close < bb_lower. Activate in zero-rescue mode only. "
                "Test standalone and as FoF zero_rescue sub-portfolio."
            ),
            acceptance_metrics={
                "zero_month_resolved": True,
                "standalone_pf": "> 1.0",
                "negative_month_delta": "<= 0"
            },
            rejection_criteria={
                "standalone_pnl": "< 0",
                "dd_delta": "> 5.0"
            },
            required_data=["bb_width", "bb_upper", "bb_lower", "atr_pct"],
            priority_score=9.0
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ZM"),
            name="ADX Slope Momentum Continuation",
            hypothesis=(
                "Zero months may occur when EMA/BB signals don't trigger but momentum is building. "
                "ADX rising steeply (slope > 2.0 over 5 bars) with price above EMA(50) "
                "indicates a trend is accelerating. Entering on this condition "
                "provides activity in otherwise quiet months."
            ),
            failure_category="low_activity",
            expected_benefit="Add quality trades in low-BB-expansion months",
            affected_months=[zero_month],
            live_compatible=True,
            lookahead_risk="LOW: ADX and EMA computed on closed candles",
            implementation_plan=(
                "New template: adx_slope_momentum_continuation. "
                "Signal: adx_slope_5 > 2.0, close > ema_50, adx > 25. "
                "Test standalone first. Accept only if PF > 1.0 and positive OOS."
            ),
            acceptance_metrics={
                "standalone_pf": "> 1.0",
                "standalone_pnl": "> 0",
                "oos_pnl": "> 0"
            },
            rejection_criteria={
                "standalone_pf": "< 0.95",
                "oos_pf": "< 1.0"
            },
            required_data=["adx_14", "adx_slope_5", "ema_50"],
            priority_score=7.5
        ))

        return ideas

    def generate_regime_risk_ideas(self) -> List[ResearchIdea]:
        """Generates ideas for regime-adjusted risk sizing."""
        ideas = []

        ideas.append(ResearchIdea(
            idea_id=self._make_id("RR"),
            name="Regime-Conditional Risk Multiplier",
            hypothesis=(
                "Trades in bull/bear trend regimes have higher expectancy than trades in "
                "sideways/chop regimes. Dynamically scaling risk (1.2x in trend, 0.6x in chop) "
                "should improve PF and reduce drawdown without reducing total trades."
            ),
            failure_category="wrong_fusion_priority",
            expected_benefit="Improve PF by 0.05-0.15, reduce drawdown by 1-3%",
            affected_months=[],
            live_compatible=True,
            lookahead_risk="LOW: Regime flags computed on closed candles at signal time",
            implementation_plan=(
                "Add regime_risk_mult dict to MultiPositionBacktestEngine. "
                "Map: bull_trend->1.2, bear_trend->1.2, sideways->0.8, vol_compression->0.7, "
                "toxic_chop->0.5, vol_expansion->1.0, funding_extreme->0.9. "
                "Sweep multiplier values and measure impact on key metrics."
            ),
            acceptance_metrics={
                "pf_delta": "> 0.0",
                "dd_delta": "< 2.0",
                "oos_pnl_delta": "> -300"
            },
            rejection_criteria={
                "pf_delta": "< -0.05",
                "negative_months_increase": "> 3"
            },
            required_data=["regime_bull_trend", "regime_bear_trend", "regime_toxic_chop"],
            priority_score=8.0
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("RR"),
            name="Monthly-DD Throttle",
            hypothesis=(
                "After losing 1.5% or more in the current month, risk should be halved "
                "to prevent runaway monthly drawdowns from compounding. "
                "This should directly reduce the magnitude of negative months."
            ),
            failure_category="risk_too_high",
            expected_benefit="Reduce worst negative months by 30-50%, reduce max DD",
            affected_months=[],
            live_compatible=True,
            lookahead_risk="NONE: Uses live_metrics.monthly_dd which is computed from closed trades",
            implementation_plan=(
                "Test risk_throttle_mode='monthly_dd_halfed' with emergency_pause_threshold=0.015. "
                "When MTD DD >= 1.5%, apply risk_mult=0.5 to all subsequent trades in the month. "
                "Compare positive/negative/zero month distribution vs no_throttle baseline."
            ),
            acceptance_metrics={
                "negative_month_pnl_improvement": "> 0 on average",
                "max_dd_delta": "< -0.5%",
                "oos_pnl_delta": "> -500"
            },
            rejection_criteria={
                "negative_months_increase": "> 5",
                "trade_count_delta": "< -100"
            },
            required_data=["live_metrics.monthly_dd"],
            priority_score=8.5
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("RR"),
            name="Loss-Streak Risk Reduction",
            hypothesis=(
                "After 3 consecutive losing trades, the next trade is more likely a recovery trade "
                "than continuing a loss streak. But to avoid compounding losses, "
                "halving risk after 3 consecutive losses should reduce drawdown in bad streaks."
            ),
            failure_category="risk_too_high",
            expected_benefit="Reduce drawdown in loss clusters",
            affected_months=[],
            live_compatible=True,
            lookahead_risk="NONE: Consecutive loss count computed from closed trades only",
            implementation_plan=(
                "Already implemented in engine as consecutive_loss_half (half risk after >= 3 losses). "
                "Test activation with risk_throttle_mode='consecutive_loss_half'. "
                "Measure DD delta and negative month delta."
            ),
            acceptance_metrics={
                "max_dd_delta": "< -0.5%",
                "negative_months_improvement": "> 0"
            },
            rejection_criteria={
                "pf_delta": "< -0.10"
            },
            required_data=["live_metrics.consecutive_losses"],
            priority_score=7.0
        ))

        return ideas

    def generate_5m_mtf_ideas(self) -> List[ResearchIdea]:
        """Generates ideas for 5m micro pullback / precision entry research."""
        ideas = []

        ideas.append(ResearchIdea(
            idea_id=self._make_id("MTF"),
            name="5m Pullback Reclaim After 1h Signal",
            hypothesis=(
                "After a 1h BB expansion signal, price often pulls back to the breakout level "
                "within the next 1-3 bars. Waiting for a 5m close back above the breakout level "
                "(after a pullback) gives a better entry price, tighter stop, and better R/R. "
                "This reduces stop distance and should improve PF."
            ),
            failure_category="stop_issue",
            expected_benefit="Improve R/R ratio, reduce stop hits on first move",
            affected_months=[],
            live_compatible=True,
            lookahead_risk="LOW: 5m entry uses closed 5m candles only, 1h signal already known",
            implementation_plan=(
                "In mtf_breakout template: add 5m_pullback_reclaim mode. "
                "1h signal triggers; wait up to 3 1h bars for 5m close to pull back to "
                "bb_upper_15m level then reclaim above it. If not achieved, skip trade. "
                "Compare trades, PF, stop distance vs immediate entry."
            ),
            acceptance_metrics={
                "pf_delta": "> 0.02",
                "avg_stop_distance_reduction": "> 10%",
                "oos_pnl_delta": "> -200"
            },
            rejection_criteria={
                "trade_count": "< 100",
                "oos_pf": "< 1.0"
            },
            required_data=["close_5m", "bb_upper_15m", "bb_lower_15m", "atr_5m"],
            priority_score=7.5
        ))

        return ideas

    def generate_phase12_orthogonal_ideas(self) -> List[ResearchIdea]:
        """Generates 25 Phase 12-ready orthogonal strategy ideas representing all required families."""
        ideas = []

        # Category A: Session Range Systems
        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Session Range Mean Reversion",
            hypothesis="Price reverts to mean inside low-volatility session ranges (e.g. Asian session). Entering at range boundaries with tight stops reduces drawdown.",
            failure_category="chop", expected_benefit="Provides profit in range regimes with low correlation to trend breakouts",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Measure range high/low in Asian session (00:00-08:00 UTC). Place limit orders at boundaries in next session. Cancel if breakout.",
            acceptance_metrics={"standalone_pf": "> 1.10", "oos_pnl": "> 500"},
            rejection_criteria={"standalone_pf": "< 1.00"}, required_data=["asian_high", "asian_low"],
            priority_score=9.0, status="DEFERRED_TO_PHASE_12", complexity_score=3.5, overfit_risk_score=2.5, live_compatibility_score=4.5
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Session Range Failure Reversal",
            hypothesis="Breakouts from session boundaries often fail and reverse. Entering on the reclaim of the range boundary yields high R/R reversals.",
            failure_category="false_breakout", expected_benefit="Exploits false breakout mechanics directly instead of filtering them",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Monitor breakout of London/Asian range. If price reclaims range within 2 bars, trigger reversal entry.",
            acceptance_metrics={"standalone_pf": "> 1.12", "oos_pnl": "> 400"},
            rejection_criteria={"standalone_pf": "< 1.02"}, required_data=["session_high", "session_low"],
            priority_score=8.5, status="DEFERRED_TO_PHASE_12", complexity_score=3.8, overfit_risk_score=3.0, live_compatibility_score=4.2
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="NY Open Sweep and Reclaim",
            hypothesis="NY open (13:30-14:30 UTC) sweeps liquidity of the London session high/low. Entering on reclaim of these levels captures the true daily direction.",
            failure_category="false_breakout", expected_benefit="High win rate at daily turning points",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Define London high/low (08:00-13:00 UTC). Monitor NY open hour for a sweep of these levels and enter on close back inside.",
            acceptance_metrics={"standalone_pf": "> 1.15", "oos_pnl": "> 600"},
            rejection_criteria={"trade_count": "< 100"}, required_data=["london_high", "london_low", "hour"],
            priority_score=8.7, status="DEFERRED_TO_PHASE_12", complexity_score=3.6, overfit_risk_score=2.8, live_compatibility_score=4.4
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Session High/Low Rejection",
            hypothesis="At major session transitions (e.g., NY close), price tests boundaries and rejects. Entering on wick rejections at session extremes yields high R/R.",
            failure_category="chop", expected_benefit="Mean reversion edge during low-volatility session handovers",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Identify session high/low dynamically. Trigger mean reversion on wick ratio > 0.60 at boundaries.",
            acceptance_metrics={"standalone_pf": "> 1.08"}, rejection_criteria={"oos_pnl": "< 0"},
            required_data=["session_high", "session_low", "wick_ratio"],
            priority_score=7.8, status="DEFERRED_TO_PHASE_12", complexity_score=3.2, overfit_risk_score=2.5, live_compatibility_score=4.5
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Time-of-Day Volatility Behavior",
            hypothesis="Breakouts during low-volatility timeframes (e.g. 22:00-01:00 UTC) are mostly noise. Gating signals by timezone saves fee erosion.",
            failure_category="cost_erosion", expected_benefit="Saves unprofitable breakout trades during illiquid periods",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Restrict breakout triggers to 08:00-21:00 UTC. Sweep allowed hour brackets to optimize PF.",
            acceptance_metrics={"pf_delta": "> 0.05"}, rejection_criteria={"trade_reduction": "> 50%"},
            required_data=["hour"],
            priority_score=7.0, status="DEFERRED_TO_PHASE_12", complexity_score=2.0, overfit_risk_score=1.5, live_compatibility_score=5.0
        ))

        # Category B: Liquidity Sweep Systems
        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Prior Day High/Low Sweep and Reclaim",
            hypothesis="Stop-hunting sweeps below previous daily lows/highs flush out retail. Reclaiming the daily low/high is a high-win-rate entry trigger.",
            failure_category="false_breakout", expected_benefit="Captures major reversal pivot points before trend expansion",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Identify previous day's high/low lookahead-free. Monitor 1h frame for sweep (low < prior_day_low but close > prior_day_low). Enter long.",
            acceptance_metrics={"standalone_pf": "> 1.15", "oos_pnl": "> 600"},
            rejection_criteria={"standalone_pf": "< 1.05"}, required_data=["prior_day_high", "prior_day_low"],
            priority_score=9.2, status="DEFERRED_TO_PHASE_12", complexity_score=3.2, overfit_risk_score=2.2, live_compatibility_score=4.6
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Swing High/Low Sweep Reversal",
            hypothesis="Swing high/low points represent key local resistance/support. Sweeping these levels and reverting represents exhaustion.",
            failure_category="false_breakout", expected_benefit="Captures swing pivots lookahead-free",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Identify local 20-bar swing highs/lows. Trigger reversal if price breaches swing point but closes back within it.",
            acceptance_metrics={"standalone_pf": "> 1.12"}, rejection_criteria={"trade_count": "< 120"},
            required_data=["swing_high", "swing_low"],
            priority_score=8.6, status="DEFERRED_TO_PHASE_12", complexity_score=3.0, overfit_risk_score=2.0, live_compatibility_score=4.7
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Wick Rejection after Stop Run",
            hypothesis="Large wicks (>=55% of candle) breaching support/resistance are signatures of stop-runs. Entering immediately on the close captures the reversal.",
            failure_category="false_breakout", expected_benefit="High win rate reversal entries",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Detect when high > bb_upper or low < bb_lower, and wick ratio is >= 0.55. Enter in opposite direction of wick.",
            acceptance_metrics={"standalone_pf": "> 1.10"}, rejection_criteria={"max_dd": "> 6.0%"},
            required_data=["upper_wick_ratio", "lower_wick_ratio", "bb_upper", "bb_lower"],
            priority_score=8.4, status="DEFERRED_TO_PHASE_12", complexity_score=2.5, overfit_risk_score=2.0, live_compatibility_score=4.8
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Failed Breakdown Reversal",
            hypothesis="Breakdowns below range support that fail to gather follow-through within 2 bars are highly bullish squeeze setups.",
            failure_category="false_breakout", expected_benefit="Exploits short squeeze dynamics",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="If close < bb_lower but reclaims bb_lower within 2 bars, enter Long with stop below breakdown low.",
            acceptance_metrics={"standalone_pf": "> 1.14", "oos_pnl": "> 450"},
            rejection_criteria={"standalone_pf": "< 1.00"}, required_data=["bb_lower"],
            priority_score=8.8, status="DEFERRED_TO_PHASE_12", complexity_score=3.3, overfit_risk_score=2.4, live_compatibility_score=4.4
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Failed Breakout Reversal",
            hypothesis="Breakouts above range resistance that fail within 2 bars are highly bearish liquidation traps.",
            failure_category="false_breakout", expected_benefit="Exploits long liquidation traps",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="If close > bb_upper but reclaims bb_upper within 2 bars, enter Short with stop above breakout high.",
            acceptance_metrics={"standalone_pf": "> 1.14", "oos_pnl": "> 450"},
            rejection_criteria={"standalone_pf": "< 1.00"}, required_data=["bb_upper"],
            priority_score=8.8, status="DEFERRED_TO_PHASE_12", complexity_score=3.3, overfit_risk_score=2.4, live_compatibility_score=4.4
        ))

        # Category C: Funding and Crowd Positioning Systems
        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Funding Extreme Reversal",
            hypothesis="Extremely high funding rates lead to leverage exhaustion and cascading liquidations. Trading reversals at funding peaks captures extreme liquidations.",
            failure_category="false_breakout", expected_benefit="High-expectancy reversals with zero correlation to Bollinger indicators",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Trigger reversal when fundingRate > 0.1% or < -0.1% on the 8h mark, coupled with 15m RSI divergence.",
            acceptance_metrics={"standalone_pf": "> 1.20", "oos_pnl": "> 800"},
            rejection_criteria={"trade_count": "< 30"}, required_data=["fundingRate", "rsi_14"],
            priority_score=8.0, status="DEFERRED_TO_PHASE_12", complexity_score=3.0, overfit_risk_score=2.0, live_compatibility_score=4.8
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Funding Divergence",
            hypothesis="When price makes higher highs but funding rate is flat/declining, it indicates spot-driven movement or lack of retail chase. Reversals here are cleaner.",
            failure_category="false_breakout", expected_benefit="Identifies institutional vs retail breakout quality",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Check for price-funding divergence over 20 bars. Enter reversal if price shows exhaustion.",
            acceptance_metrics={"standalone_pf": "> 1.10"}, rejection_criteria={"trade_count": "< 50"},
            required_data=["fundingRate", "close"],
            priority_score=7.6, status="DEFERRED_TO_PHASE_12", complexity_score=3.4, overfit_risk_score=2.2, live_compatibility_score=4.7
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Funding Price Exhaustion",
            hypothesis="When funding is highly positive and price has been sideways for 10+ bars, longs are paying heavy funding fees and will capitulate if support breaks.",
            failure_category="false_breakout", expected_benefit="High probability breakdown triggers",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Check if fundingRate > 0.05% and close has been in 1% range for 12 bars. Enter short on breach of range low.",
            acceptance_metrics={"standalone_pf": "> 1.18", "oos_pnl": "> 500"},
            rejection_criteria={"standalone_pf": "< 1.05"}, required_data=["fundingRate", "close"],
            priority_score=8.2, status="DEFERRED_TO_PHASE_12", complexity_score=3.1, overfit_risk_score=2.1, live_compatibility_score=4.6
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Crowded-Side Unwind Signals",
            hypothesis="When funding is negative and price begins to tick up, shorts are forced to cover. Entering on this unwind captures explosive squeeze action.",
            failure_category="low_activity", expected_benefit="Captures quick squeeze PnL with low holding time",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Check if fundingRate < -0.03% and close crosses above 20-bar high. Enter long.",
            acceptance_metrics={"standalone_pf": "> 1.12"}, rejection_criteria={"trade_count": "< 40"},
            required_data=["fundingRate", "close"],
            priority_score=7.9, status="DEFERRED_TO_PHASE_12", complexity_score=2.8, overfit_risk_score=2.0, live_compatibility_score=4.7
        ))

        # Category D: Range and Mean-Reversion Systems
        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Low-Volatility Range Scalping",
            hypothesis="When BB width is extremely compressed, market maker flows dominate. Scalping mean reversion on 5m candles captures minor fluctuations.",
            failure_category="chop", expected_benefit="Smooths equity curves during prolonged consolidation periods",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Check if 1h BB width < 0.02. Enter 5m RSI mean reversion trades with trailing stop-loss.",
            acceptance_metrics={"standalone_pf": "> 1.08", "oos_pnl": "> 300"},
            rejection_criteria={"max_dd": "> 5.0%"}, required_data=["bb_width", "rsi_5m"],
            priority_score=7.5, status="DEFERRED_TO_PHASE_12", complexity_score=4.0, overfit_risk_score=3.5, live_compatibility_score=3.5
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="VWAP Deviation Return",
            hypothesis="Price is highly mean-reverting to VWAP in non-trending environments. Deviation beyond 2.5x ATR is unsustainable and reverts.",
            failure_category="chop", expected_benefit="Generates steady cash flow in sideways months",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="If ADX < 20 and distance(close, VWAP) > 2.5 * ATR, enter mean reversion trade toward VWAP.",
            acceptance_metrics={"standalone_pf": "> 1.11", "oos_pnl": "> 500"},
            rejection_criteria={"standalone_pf": "< 1.02"}, required_data=["vwap", "adx_14", "atr_14"],
            priority_score=8.5, status="DEFERRED_TO_PHASE_12", complexity_score=3.4, overfit_risk_score=2.5, live_compatibility_score=4.6
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Anchored VWAP Reclaim",
            hypothesis="VWAP anchored at key dates (e.g. week start) acts as institutional average cost. Reclaiming it after deviation indicates a trend reset.",
            failure_category="low_activity", expected_benefit="High win rate trend-onset entries",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Anchor VWAP lookahead-free on weekly boundary. Enter on close crossing back over weekly VWAP with RSI > 45.",
            acceptance_metrics={"standalone_pf": "> 1.10", "oos_pnl": "> 500"},
            rejection_criteria={"standalone_pf": "< 1.00"}, required_data=["vwap_weekly"],
            priority_score=8.7, status="DEFERRED_TO_PHASE_12", complexity_score=3.0, overfit_risk_score=2.0, live_compatibility_score=4.7
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Range Midpoint Reversion",
            hypothesis="Sideways ranges have high gravity at the midpoint. Buying the range low for a move to the midpoint offers high win probability.",
            failure_category="chop", expected_benefit="High win rate short-term scalp trades",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Define range high/low based on 48h swing points. Buy low with TP at range midpoint and SL below range low.",
            acceptance_metrics={"standalone_pf": "> 1.06"}, rejection_criteria={"trade_count": "< 80"},
            required_data=["swing_high", "swing_low"],
            priority_score=7.4, status="DEFERRED_TO_PHASE_12", complexity_score=3.2, overfit_risk_score=2.6, live_compatibility_score=4.5
        ))

        # Category E: Trend Continuation Systems
        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Trend Pullback Continuation Without BB Dependence",
            hypothesis="Strong trends pull back to key EMAs (e.g. EMA 50) without expanding the BB. Entering on EMA reclaims captures continuation at lower risk.",
            failure_category="low_activity", expected_benefit="Significantly increases trade count in strong trending markets",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Check if ADX > 25. Enter on reclaim of 1h EMA 50 with SL below previous 1h swing low.",
            acceptance_metrics={"standalone_pf": "> 1.15", "oos_pnl": "> 700", "trade_count": "> 150"},
            rejection_criteria={"standalone_pf": "< 1.05"}, required_data=["ema_50", "adx_14", "swing_low"],
            priority_score=9.5, status="DEFERRED_TO_PHASE_12", complexity_score=2.8, overfit_risk_score=2.2, live_compatibility_score=4.8
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Higher-High / Higher-Low Breakout",
            hypothesis="Breakouts that create clear market structure higher highs in trending markets have higher success rates than arbitrary BB breakout levels.",
            failure_category="low_activity", expected_benefit="Captures clean structural trend breakouts",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Trigger entry when price breaks above a swing high that was itself higher than the prior swing high.",
            acceptance_metrics={"standalone_pf": "> 1.13", "oos_pnl": "> 550"},
            rejection_criteria={"trade_count": "< 90"}, required_data=["swing_high"],
            priority_score=8.9, status="DEFERRED_TO_PHASE_12", complexity_score=3.0, overfit_risk_score=2.0, live_compatibility_score=4.7
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Pullback after Volatility Impulse",
            hypothesis="An impulse move on high volume followed by a 30-50% pullback of the impulse body represents institutional accumulation. Entering on reclaim is low-risk.",
            failure_category="low_activity", expected_benefit="Tighter stops on trend entry setups",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Identify body_ratio > 0.70 and volume > 1.8x MA. Wait 1-3 bars for pullback, then enter when close > prior high.",
            acceptance_metrics={"standalone_pf": "> 1.16", "oos_pnl": "> 650"},
            rejection_criteria={"standalone_pf": "< 1.05"}, required_data=["body_ratio", "volume", "close"],
            priority_score=9.1, status="DEFERRED_TO_PHASE_12", complexity_score=3.3, overfit_risk_score=2.3, live_compatibility_score=4.6
        ))

        # Category F: Volatility Systems
        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Volatility Exhaustion Reversal",
            hypothesis="When ATR reaches extreme multi-week percentiles, momentum is exhausted. Trading reversals back toward the mean captures market exhaustion.",
            failure_category="false_breakout", expected_benefit="High-win-rate reversion at local tops and bottoms",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Check if 1h ATR(14) > 95th percentile of past 500 hours. Trigger reversal entry on 15m candle pinbar reclaim.",
            acceptance_metrics={"standalone_pf": "> 1.14", "oos_pnl": "> 400"},
            rejection_criteria={"max_dd": "> 7.0%"}, required_data=["atr_14", "high_low_ratio"],
            priority_score=7.8, status="DEFERRED_TO_PHASE_12", complexity_score=3.4, overfit_risk_score=2.8, live_compatibility_score=4.1
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Failed Volatility Expansion Reversal",
            hypothesis="If ATR expands rapidly but price fails to break range boundaries, it indicates heavy institutional absorption. Reversal is highly expected.",
            failure_category="false_breakout", expected_benefit="Captures major reversal peaks during false news spikes",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Identify ATR spike > 2x average, with close remaining within Bollinger Bands. Enter reversal trade.",
            acceptance_metrics={"standalone_pf": "> 1.12"}, rejection_criteria={"trade_count": "< 40"},
            required_data=["atr_14", "bb_upper", "bb_lower"],
            priority_score=8.1, status="DEFERRED_TO_PHASE_12", complexity_score=3.5, overfit_risk_score=2.6, live_compatibility_score=4.2
        ))

        # Category G: Execution Alpha Systems
        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="5m Microstructure Trigger after 1h Bias",
            hypothesis="Entering immediately on 1h close incurs high slip. Waiting for 5m candle microstructure confirmation (e.g. order flow block) reduces stop distance.",
            failure_category="stop_issue", expected_benefit="Tighter stops, higher average R-multiple",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="1h breakout signal sets entry bias. Execute trigger on 5m close reclaiming the 5m EMA(20) in the direction of the 1h bias.",
            acceptance_metrics={"pf_delta": "> 0.06", "avg_stop_distance_reduction": "> 15%"},
            rejection_criteria={"trade_count": "< 120"}, required_data=["close_5m", "ema_20_5m"],
            priority_score=8.9, status="DEFERRED_TO_PHASE_12", complexity_score=4.2, overfit_risk_score=2.8, live_compatibility_score=4.0
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Stop Distance Optimization",
            hypothesis="Hard SL distances are vulnerable to volatility spikes. Dynamic stop distance scaled by recent 15m ATR prevents premature stop outs.",
            failure_category="stop_issue", expected_benefit="Reduces stop outs during market noise",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Wired SL to 2.2x 15m ATR instead of static percentage or 1h ATR. Verify reduction of stop-loss hit rate.",
            acceptance_metrics={"pf_delta": "> 0.04", "max_dd_delta": "< -0.5%"},
            rejection_criteria={"standalone_pf": "< 1.02"}, required_data=["atr_15m"],
            priority_score=8.3, status="DEFERRED_TO_PHASE_12", complexity_score=2.9, overfit_risk_score=2.2, live_compatibility_score=4.5
        ))

        ideas.append(ResearchIdea(
            idea_id=self._make_id("ORTH"),
            name="Cost-Aware Trade Gating",
            hypothesis="When spreads/fees are high, or historical slippage is spiked, gating trades saves cost drag. Only taking signals when conditions are favorable protects floor.",
            failure_category="cost_erosion", expected_benefit="Protects floor during illiquid market shocks",
            affected_months=[], live_compatible=True, lookahead_risk="NONE",
            implementation_plan="Monitor rolling execution slippage. If average slippage > 0.1%, gate all new trend breakout trades.",
            acceptance_metrics={"pf_delta": "> 0.05"}, rejection_criteria={"trade_count": "< 200"},
            required_data=["slippage_history"],
            priority_score=8.0, status="DEFERRED_TO_PHASE_12", complexity_score=3.2, overfit_risk_score=2.4, live_compatibility_score=4.6
        ))

        return ideas

    def generate_phase13_ideas(self) -> List[ResearchIdea]:
        """Generates 112 distinct hypotheses across 14 strategy research categories."""
        ideas = []
        
        # 1. Trend Continuation
        tc_details = [
            ("EMA50 Pullback in Trend", "EMA50 pullback touch in strong EMA200 bull/bear trend", "trend_exhaustion", "Reduce losses at trend end", ["ema_50", "ema_200"], "ADX > 25", "Close crosses EMA50", "Trailing stop at swing high/low", "2.0x ATR", "12 trades/month", "Low", 8.5),
            ("VWAP Pullback Reclaim", "VWAP reclaim touch from below in long trend", "false_breakout", "Exploit pullbacks in strong trend", ["vwap", "close"], "ADX > 20", "Close reclaim VWAP", "Close below VWAP", "1.8x ATR", "10 trades/month", "Medium", 8.0),
            ("ADX Slope Continuation", "ADX slope acceleration continuation during breakout", "trend_exhaustion", "Catch momentum acceleration", ["adx_slope", "close"], "ADX > 30", "ADX slope > 0.5", "RSI divergence exit", "2.2x ATR", "8 trades/month", "Low", 8.2),
            ("EMA10 Momentum Rider", "EMA10 short-term momentum rider in high-volatility expansions", "chop", "Ride fast momentum moves", ["ema_10", "close"], "ATR_pct > 0.04", "Close above EMA10", "Trailing ATR exit", "1.5x ATR", "15 trades/month", "High", 7.8),
            ("Impulse Pullback EMA20", "Impulse spike followed by 3-bar pullback to EMA20", "chop", "Enter pullback after volume spike", ["ema_20", "close"], "ADX > 15", "Close reclaim EMA20", "Time stop 10 bars", "1.8x ATR", "11 trades/month", "Medium", 7.9),
            ("Higher-High Continuation", "Breakout above 24h high with rising volume support", "trend_exhaustion", "Exploit breakouts above daily highs", ["high_24h", "volume"], "Volume > 1.2x MA", "Close above high_24h", "Trailing stop 2x ATR", "2.0x ATR", "9 trades/month", "Low", 8.1),
            ("Trend Pullback Failed Breakdown", "EMA50 pullback reclaim after a failed breakdown of daily low", "false_breakout", "Enter pullback on failed ranges", ["low_daily", "ema_50"], "ADX > 25", "Reclaim daily low", "EMA50 cross exit", "2.0x ATR", "7 trades/month", "Low", 8.3),
            ("RSI Pullback Rider", "RSI pulling back to 50 in a strong trend before continuation", "chop", "Oscillator pullback in trend", ["rsi_14", "close"], "ADX > 20", "RSI crosses 50", "RSI overbought exit", "1.8x ATR", "10 trades/month", "Low", 7.7)
        ]
        
        # 2. Breakout Retest
        br_details = [
            ("Breakout Level Retest", "Price breaks BB band and retests the exact band breakout price", "false_breakout", "Verify breakout support/resistance", ["bb_upper", "bb_lower"], "ADX > 20", "Limit order at breakout level", "Target 2.5x ATR", "2.0x ATR", "10 trades/month", "Low", 8.8),
            ("Breakout 15m Retest", "1h breakout verified by 15m pullback and support reclaim", "false_breakout", "Reduce whipsaws on breakout confirmation", ["close_15m", "close_1h"], "ADX > 15", "15m reclaim close_1h", "Trailing stop 15m ATR", "1.8x ATR", "9 trades/month", "Low", 8.4),
            ("Breakout 5m Retest", "1h breakout verified by 5m pullback to VWAP and reclaim", "chop", "Tighter entry stops on 5m", ["vwap_5m", "close_1h"], "ADX > 20", "5m reclaim VWAP", "Target 3.0x ATR", "1.5x ATR", "12 trades/month", "Medium", 8.2),
            ("Retest Limit Entry", "Pullback limit entry placed at 1h breakout level to avoid slippage", "cost_erosion", "Capture maker rebate and eliminate entry slip", ["close_1h"], "ATR_pct < 0.03", "Limit order at breakout level", "Taker stop-loss", "2.0x ATR", "11 trades/month", "Low", 8.6),
            ("Breakout Skip No Retest", "Skip entry if price moves too fast without any retest within 3 candles", "low_activity", "Avoid chasing running extensions", ["close_1h"], "ADX > 20", "Pulled back to breakout level", "Trailing exit", "2.0x ATR", "8 trades/month", "Low", 8.0),
            ("Failed Retest Reversal", "Enter reversal if breakout level retest fails and closes back inside range", "chop", "Fade failed breakout levels", ["close_1h"], "ADX < 20", "Close back inside range", "Target 2.0x ATR", "2.0x ATR", "9 trades/month", "Low", 8.1),
            ("Close Above Level Continuation", "Enter continuation only after two consecutive closes above breakout level", "false_breakout", "Filter out single-candle spike traps", ["close_1h"], "ADX > 25", "2 closes above level", "Target 2.5x ATR", "1.8x ATR", "7 trades/month", "Low", 8.3),
            ("Retest with Volume Surge", "Confirm breakout level retest only if volume is rising on the reclaim", "volume_weakness", "Filter breakouts with no participation", ["volume", "close_1h"], "ADX > 20", "Reclaim with volume > MA", "Target 3.0x ATR", "2.0x ATR", "8 trades/month", "Low", 8.5)
        ]
        
        # 3. Volatility Expansion
        ve_details = [
            ("ATR Percentile Expansion", "ATR rising above 80th percentile on 1h timeframe", "chop", "Avoid breakouts in low volatility", ["atr_pct"], "ADX > 20", "ATR crosses 80th percentile", "Trailing stop 1.5x ATR", "1.5x ATR", "12 trades/month", "Medium", 8.3),
            ("Bollinger Width Expansion", "Bollinger Band width rising above 70th percentile", "chop", "Identify range contraction release", ["bb_width_pct"], "ADX > 20", "BB width rises", "Target 2.5x ATR", "2.0x ATR", "11 trades/month", "Low", 8.2),
            ("Range Contraction Breakout", "Entering breakout after a long range contraction period (width < 0.02)", "low_activity", "Exploit low volatility compression moves", ["bb_width"], "ADX < 15", "Close outside contraction bands", "Target 3.0x ATR", "2.5x ATR", "6 trades/month", "Low", 8.6),
            ("Volatility Exhaustion Reversal", "Fading extreme volatility expansions when volume drops", "trend_exhaustion", "Capture peak exhaustion reversals", ["volume", "atr_pct"], "ATR_pct > 0.05", "Volume drop + wick rejection", "Reversal stop", "1.8x ATR", "5 trades/month", "Low", 8.4),
            ("Failed Volatility Expansion", "Reversal entry when volatility spike fails to follow through", "false_breakout", "Fade fake news spikes", ["atr_pct", "close"], "ADX < 20", "Close back inside bands", "Target 2.0x ATR", "2.0x ATR", "8 trades/month", "Low", 8.1),
            ("High-Vol Trend Continuation", "Adding to positions when ATR rises in trend direction", "chop", "Pyramid during high-conviction trends", ["atr_14", "ema_50"], "ADX > 30", "ATR rising + trend touch", "Target 2.5x ATR", "2.0x ATR", "10 trades/month", "Low", 8.0),
            ("Low-Vol Fakeout Avoidance", "Gating all breakout signals if ATR is below 15th percentile", "chop", "Skip fake breakouts in flat ranges", ["atr_pct"], "ADX < 15", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.5),
            ("Volatility Channel Breakout", "Close outside a Keltner Channel with rising ATR", "false_breakout", "Rely on dual-channel filters", ["keltner_channel", "atr"], "ADX > 20", "Close outside channel", "Target 2.5x ATR", "1.8x ATR", "10 trades/month", "Low", 8.2)
        ]
        
        # 4. Liquidity Sweep
        ls_details = [
            ("Prior Day High Sweep", "Price sweeps prior day high and closes back inside daily range", "false_breakout", "Fade daily high stop runs", ["prior_day_high", "close"], "ADX < 20", "Close below prior day high", "Reversal target", "2.0x ATR", "10 trades/month", "Low", 8.9),
            ("Prior Day Low Sweep", "Price sweeps prior day low and closes back above daily range", "false_breakout", "Fade daily low stop runs", ["prior_day_low", "close"], "ADX < 20", "Close above prior day low", "Reversal target", "2.0x ATR", "10 trades/month", "Low", 8.9),
            ("Session High Sweep Reclaim", "Sweeping Asian session high and reclaiming inside London session", "chop", "Capture session sweep reclaims", ["asian_high", "close"], "ADX < 20", "London close below asian_high", "Target 2.0x ATR", "1.8x ATR", "8 trades/month", "Low", 8.4),
            ("Session Low Sweep Reclaim", "Sweeping Asian session low and reclaiming inside London session", "chop", "Capture session sweep reclaims", ["asian_low", "close"], "ADX < 20", "London close above asian_low", "Target 2.0x ATR", "1.8x ATR", "8 trades/month", "Low", 8.4),
            ("Swing High Sweep", "Sweeping local swing high and reclaiming with wick rejection >= 0.50", "chop", "Fade local swing high stop run", ["swing_high", "wick_ratio"], "ADX < 20", "Close below swing_high", "Target 2.0x ATR", "2.0x ATR", "9 trades/month", "Low", 8.2),
            ("Swing Low Sweep", "Sweeping local swing low and reclaiming with wick rejection >= 0.50", "chop", "Fade local swing low stop run", ["swing_low", "wick_ratio"], "ADX < 20", "Close above swing_low", "Target 2.0x ATR", "2.0x ATR", "9 trades/month", "Low", 8.2),
            ("Wick Rejection Stop Run", "Large wick rejection at swing high/low indicating liquidity sweep", "stop_issue", "Exploit institutional stop absorption", ["wick_ratio", "close"], "ADX < 25", "Wick ratio >= 0.50", "Target 2.5x ATR", "2.0x ATR", "12 trades/month", "Low", 8.5),
            ("Sweep with Volume Surge", "Confirming liquidity sweep only if volume is extremely high on sweep bar", "volume_weakness", "Filter out low-participation sweeps", ["volume", "close"], "ADX < 20", "Sweep close with volume > 2x MA", "Target 2.0x ATR", "1.8x ATR", "8 trades/month", "Low", 8.3)
        ]

        # 5. Session Behavior
        sb_details = [
            ("Asian Range Breakout", "Breakout above/below Asian range during London Open", "false_breakout", "Ride London momentum breakouts", ["asian_high", "asian_low"], "ADX > 20", "London close outside range", "Trailing exit", "2.0x ATR", "10 trades/month", "Medium", 8.5),
            ("Asian Range Fade", "Fading Asian boundaries during low-volatility Asian Session", "chop", "Fade range boundaries at night", ["asian_high", "asian_low"], "ADX < 15", "Touch boundary", "Target 1.5x ATR", "1.5x ATR", "15 trades/month", "Medium", 8.0),
            ("London Open Continuation", "Ride London open trend expansion after 08:00 UTC", "trend_exhaustion", "Capture early session momentum", ["close", "volume"], "ADX > 25", "Time is 08:00 UTC + trend", "Target 3.0x ATR", "2.2x ATR", "12 trades/month", "Low", 8.2),
            ("London Fakeout Reversal", "London breakout fails and price reverses back below Asian range", "false_breakout", "Fade false London open breakouts", ["asian_high", "close"], "ADX < 20", "Reenter Asian range", "Target 2.0x ATR", "1.8x ATR", "9 trades/month", "Low", 8.3),
            ("NY Open Sweep Reclaim", "NY session sweeps daily high/low and reclaims", "chop", "Fade NY open volatility spikes", ["daily_high", "daily_low"], "ADX < 20", "NY open sweep reclaim", "Target 2.0x ATR", "2.0x ATR", "11 trades/month", "Low", 8.6),
            ("NY Trend Continuation", "NY session continuation after pullback to London VWAP", "trend_exhaustion", "Add to trend during NY session", ["vwap_london", "close"], "ADX > 25", "NY open pullback to VWAP", "Target 3.0x ATR", "2.5x ATR", "9 trades/month", "Low", 8.1),
            ("Post-NY Volatility Fade", "Fading late NY ranges (after 20:00 UTC) as volatility decays", "chop", "Range scalp quiet late NY session", ["close"], "ATR_pct < 0.02", "Touch local boundary", "Target 1.0x ATR", "1.2x ATR", "13 trades/month", "Low", 7.8),
            ("Session-Specific Sizing", "Scale down position sizes in notoriously fakeout-heavy Asian sessions", "chop", "Reduce Asian session exposure", ["close"], "Time is 00:00-08:00", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.4)
        ]

        # 6. Funding Behavior
        fb_details = [
            ("Extreme Funding Reversal", "Fade breakouts when absolute funding rate is >= 0.03%", "funding_drag", "Exploit overleveraged funding exhaustion", ["fundingRate"], "ADX < 20", "Extreme funding + wick rejection", "Target 2.0x ATR", "2.0x ATR", "6 trades/month", "Low", 8.7),
            ("Funding Divergence Reversal", "Price rising while funding rate drops, indicating spot-driven sweep", "false_breakout", "Spots spot-futures divergence", ["fundingRate", "close"], "ADX < 20", "Price rising + funding falling", "Target 2.5x ATR", "2.0x ATR", "8 trades/month", "Low", 8.3),
            ("Funding plus Sideways Range", "Mean reversion at range boundaries when funding rate is flat", "chop", "Filter mean reversion by funding rate", ["fundingRate", "close"], "ADX < 15", "Touch range boundary + funding flat", "Target 1.5x ATR", "1.5x ATR", "12 trades/month", "Low", 8.0),
            ("Funding Extreme Pullback", "EMA50 pullback touch when funding rate is in trend direction", "trend_exhaustion", "Enter pullback aligned with funding bias", ["fundingRate", "ema_50"], "ADX > 25", "Touch EMA50 + funding aligned", "Target 3.0x ATR", "2.5x ATR", "9 trades/month", "Low", 8.2),
            ("Funding Exhaustion Reversal", "Extreme negative funding rate reversals in sideways consolidation", "chop", "Fade capitulation shorts at range lows", ["fundingRate"], "ADX < 20", "Extreme negative funding + consolidate", "Target 2.0x ATR", "2.0x ATR", "7 trades/month", "Low", 8.4),
            ("Funding Cost Avoidance", "Skip entries 1 hour before funding boundary if expected hold is short", "cost_erosion", "Avoid funding fee payments", ["fundingRate"], "Hold crosses boundary", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.5),
            ("Funding-Window Skip", "Close positions 15 mins before funding rate payment if PnL is flat", "cost_erosion", "Avoid funding fee payments", ["fundingRate"], "Hold crosses boundary", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.1),
            ("Funding Carry Filter", "Filter out trend breakouts that would pay extreme funding fees", "cost_erosion", "Filter breakouts by carry drag", ["fundingRate"], "Breakout pays extreme fee", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.2)
        ]

        # 7. Range Behavior
        rb_details = [
            ("Asian Range Mean Reversion", "Price reverts to mean inside low-volatility session ranges", "chop", "Mean reversion in session range", ["asian_high", "asian_low"], "ADX < 20", "Touch boundary", "Target 2.0x ATR", "1.5x ATR", "15 trades/month", "Medium", 8.9),
            ("VWAP Deviation Return", "Reverting back to VWAP after price deviates past 2.0x ATR", "chop", "Scale deviation return trades", ["vwap", "atr_14"], "ADX < 15", "Price deviates > 2.0x ATR", "Return to VWAP", "2.0x ATR", "12 trades/month", "Medium", 8.3),
            ("Low Vol Range Scalping", "Scalping range boundaries during low volatility ATR periods", "chop", "Low-vol range mean reversion", ["close"], "ATR_pct < 0.02", "Touch range boundary", "Target 1.5x ATR", "1.5x ATR", "14 trades/month", "Medium", 8.0),
            ("RSI Exhaustion MR", "Mean reversion at boundaries when RSI is overbought/oversold", "false_breakout", "RSI extreme mean reversion", ["rsi_14"], "ADX < 20", "RSI > 75 or < 25", "Target 2.0x ATR", "1.8x ATR", "11 trades/month", "Low", 8.2),
            ("Range Midpoint Reversion", "Entering reversion trades targeting the 24h range midpoint", "chop", "Revert to range center", ["close"], "ADX < 20", "Touch range extreme", "Midpoint take profit", "2.0x ATR", "10 trades/month", "Low", 8.1),
            ("Volatility Exhaustion MR", "Mean reversion when ATR is extreme but price stays inside bands", "false_breakout", "Reversion after fakeout expansions", ["atr_pct"], "ADX < 15", "Extreme ATR + inside bands", "Target 2.0x ATR", "2.0x ATR", "8 trades/month", "Low", 8.4),
            ("Failed Volatility Expansion MR", "Fading volatility expansion attempts that return to range", "false_breakout", "Revert after breakout failure", ["close"], "ADX < 20", "Reenter Bollinger Bands", "Target 2.0x ATR", "2.0x ATR", "9 trades/month", "Low", 8.3),
            ("RSI Divergence MR", "Range reversion entry on 1h RSI divergence at swing high/low", "trend_exhaustion", "Exploit range exhaustions", ["rsi_14", "close"], "ADX < 20", "RSI divergence at extreme", "Target 2.5x ATR", "2.2x ATR", "7 trades/month", "Low", 8.5)
        ]

        # 8. Execution Alpha
        ea_details = [
            ("5m Micro Trigger after 1h Bias", "Triggering entry on 5m close reclaiming EMA20 to reduce slippage", "stop_issue", "Tighter entry stops on 5m", ["close_5m", "ema_20_5m"], "ADX > 20", "5m close reclaim EMA20", "Target 3.0x ATR", "1.5x ATR", "12 trades/month", "Medium", 8.9),
            ("Stop Distance Optimization", "Dynamic stop distance scaled by recent 15m ATR to avoid noise hits", "stop_issue", "Reduce premature stop hit rate", ["atr_15m"], "ADX < 25", "Dynamic SL 2.2x 15m ATR", "Target 2.5x ATR", "2.2x ATR", "10 trades/month", "Low", 8.3),
            ("Cost-Aware Trade Gating", "Skip breakout trades when historical slippage is spiked", "cost_erosion", "Gate trades during illiquid periods", ["slippage_history"], "Slippage > 0.1%", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.0),
            ("Post-Only Entry No Fallback", "Entering breakouts with post-only limit orders to avoid taker fees", "cost_erosion", "Capture maker rebate on all entries", ["close"], "ATR_pct < 0.03", "Limit post-only order", "Taker stop-loss", "2.0x ATR", "10 trades/month", "Low", 8.4),
            ("Post-Only Timed Fallback", "Post-only entry; if not filled in 3 bars, fallback to taker market", "cost_erosion", "Capture maker fills with taker fallback safety", ["close"], "ATR_pct < 0.03", "Limit order with 3 bar fallback", "Taker stop-loss", "2.0x ATR", "11 trades/month", "Low", 8.5),
            ("Passive Entry Market SL", "Passive limit entry at breakout price, with market taker SL protection", "cost_erosion", "Capture maker rebate, preserve stop safety", ["close"], "ATR_pct < 0.03", "Limit entry + market SL", "Market stop-loss", "2.0x ATR", "11 trades/month", "Low", 8.6),
            ("Passive Entry and TP", "Limit entry and limit TP to capture maker fees on both sides", "cost_erosion", "Maker execution on both entry and exit", ["close"], "ATR_pct < 0.03", "Limit entry + limit TP", "Taker stop-loss", "2.0x ATR", "9 trades/month", "Low", 8.7),
            ("Spread-Aware Limit Offset", "Limit order offset by half the spread to improve queue priority", "cost_erosion", "Improve limit fill rates", ["spread"], "ATR_pct < 0.03", "Limit order + offset", "Taker stop-loss", "2.0x ATR", "11 trades/month", "Low", 8.2)
        ]

        # 9. Risk Routing
        rr_details = [
            ("Chop Regime Risk Halving", "Halving risk (0.5x) when regime_toxic_chop is active", "chop", "Reduce losses in sideways chop", ["regime_toxic_chop"], "Chop active", "Apply risk_mult=0.5", "N/A", "N/A", "0 trades/month", "Low", 8.0),
            ("Regime-Conditional Risk Multiplier", "Dynamic risk multiplier based on active market regime", "wrong_fusion_priority", "Scale risk in high-conviction trends", ["regime_bull_trend", "regime_bear_trend", "regime_toxic_chop"], "Filter active", "Apply scale_risk dict", "N/A", "N/A", "0 trades/month", "Low", 8.0),
            ("Monthly-DD Throttle", "Halving risk when MTD DD is >= 1.5% to prevent compounding", "risk_too_high", "Prevent runaway monthly drawdowns", ["live_metrics.monthly_dd"], "MTD DD >= 1.5%", "Apply risk_mult=0.5", "N/A", "N/A", "0 trades/month", "Low", 8.5),
            ("Loss-Streak Risk Reduction", "Halving risk after 3 consecutive losses to protect capital", "risk_too_high", "Protect capital during bad streaks", ["live_metrics.consecutive_losses"], "Consecutive losses >= 3", "Apply risk_mult=0.5", "N/A", "N/A", "0 trades/month", "Low", 7.0),
            ("Vol-Adjusted Sizing", "Scale position size inversely to 14-bar ATR to keep dollar risk constant", "stop_issue", "Keep dollar risk constant across volatility regimes", ["atr_14"], "Filter active", "Scale size by ATR", "N/A", "N/A", "0 trades/month", "Low", 8.2),
            ("High-Expectancy Risk Boost", "Increase risk to 1.25x in proven high-expectancy trend regimes", "wrong_fusion_priority", "Maximize profit in high-conviction regimes", ["regime_bull_trend"], "Bull trend active", "Apply risk_mult=1.25", "N/A", "N/A", "0 trades/month", "Low", 8.1),
            ("Funding Drag Risk Reduction", "Halving risk when entering trades that carry high funding fee rates", "funding_drag", "Minimize funding fee exposure", ["fundingRate"], "Absolute funding >= 0.02%", "Apply risk_mult=0.5", "N/A", "N/A", "0 trades/month", "Low", 8.3),
            ("Selectivity Throttle", "Increase entry selectivity thresholds after monthly drawdown exceeds 2%", "risk_too_high", "Recover monthly drawdown safely", ["live_metrics.monthly_dd"], "MTD DD >= 2.0%", "Selectivity filter active", "N/A", "N/A", "0 trades/month", "Low", 8.4)
        ]

        # 10. Exit Optimization
        eo_details = [
            ("Static TP/SL Optimization", "Optimizing static TP and SL ATR multipliers dynamically", "target_issue", "Verify best baseline targets", ["close"], "Filter active", "Static SL/TP", "Static target", "Static stop", "10 trades/month", "Low", 8.0),
            ("ATR-Scaled TP/SL", "TP and SL scaled dynamically by 14-bar ATR", "stop_issue", "Adjust targets to current volatility", ["atr_14"], "Filter active", "ATR SL/TP", "ATR take profit", "ATR stop", "10 trades/month", "Low", 8.0),
            ("Regime-Dependent Exits", "asymmetric TP and SL multipliers based on volatility regimes", "target_issue", "Adjust exits to market regime", ["regime_bull_trend", "regime_toxic_chop"], "Filter active", "Regime SL/TP", "Regime take profit", "Regime stop", "10 trades/month", "Low", 8.3),
            ("Breakeven after MFE", "Move stop to breakeven after price reaches 1.5x ATR profit (MFE)", "stop_issue", "Protect profitable trades from reversing", ["close", "atr_14"], "MFE >= 1.5x ATR", "Move SL to entry", "N/A", "N/A", "0 trades/month", "Low", 8.5),
            ("Trailing in Trends Only", "Trailing stops active only in proven trend regimes (ADX >= 25)", "trend_exhaustion", "Avoid premature exits in range regimes", ["adx_14"], "ADX >= 25", "Trailing stop active", "Trailing exit", "N/A", "0 trades/month", "Low", 8.2),
            ("Partial Profit Take", "Close 50% of position at 1.5x ATR and trail remaining 50%", "target_issue", "Lock in profits on partial targets", ["close"], "Price reaches 1.5x ATR", "Close 50%", "Trail 50%", "N/A", "0 trades/month", "Low", 8.1),
            ("Time Stop Exit", "Exit trade after 24 candles if target or stop has not been hit", "chop", "Free capital from sideways dead trades", ["close"], "Hold >= 24 bars", "Exit market", "N/A", "N/A", "0 trades/month", "Low", 7.9),
            ("Funding Window Exit", "Exit trade 10 minutes before funding payment if price is consolidating", "funding_drag", "Minimize carry cost drag", ["fundingRate"], "Sideways + boundary close", "Exit market", "N/A", "N/A", "0 trades/month", "Low", 8.4)
        ]

        # 11. Portfolio Fusion
        pf_details = [
            ("Signal Union Router", "Union routing of signals where portfolios combine allocations", "wrong_fusion_priority", "Maximize trade opportunity safely", ["close"], "Filter active", "Union routing", "N/A", "N/A", "0 trades/month", "Low", 8.0),
            ("Conflict Cancellation Router", "Cancel signals when sub-strategies have opposite directions", "wrong_fusion_priority", "Avoid trading against complementary models", ["close"], "Opposite direction signals", "Cancel signals", "N/A", "N/A", "0 trades/month", "Low", 8.0),
            ("Regime-Based Fusion Routing", "Dynamically route candidates into trend/range sub-portfolios", "wrong_fusion_priority", "Map candidates to their target regimes", ["regime_sideways_range", "regime_bull_trend"], "Filter active", "Regime routing", "N/A", "N/A", "0 trades/month", "Low", 8.5),
            ("MTD Adaptive Fusion", "Activate filler strategies only when core strategy is in monthly DD", "low_activity", "Zero month rescue via adaptive activation", ["live_metrics.monthly_dd"], "Core monthly DD > 0", "Adaptive sleeve active", "N/A", "N/A", "0 trades/month", "Low", 8.7),
            ("Voting-Based Sizing Ensemble", "Scale position sizing based on voting agreement across candidates", "wrong_fusion_priority", "Confirm setups with ensemble voting", ["close"], "Multiple candidate signals", "Ensemble sizing scale", "N/A", "N/A", "0 trades/month", "Low", 8.2),
            ("Toxicity Shutdown Router", "Disable specific sub-portfolios during prolonged drawdowns", "risk_too_high", "Shut down underperforming portfolios", ["live_metrics.portfolio_dd"], "Portfolio DD >= 3.0%", "Disable portfolio", "N/A", "N/A", "0 trades/month", "Low", 8.4),
            ("Correlation-Based Sizing", "Scale down position sizes when signal correlation across strategies is high", "risk_too_high", "Reduce systemic correlation exposure", ["close"], "Correlated signals active", "Apply risk_mult=0.7", "N/A", "N/A", "0 trades/month", "Low", 8.1),
            ("Taker Fallback Execution", "Route all limit orders to market fallback when volatility spikes", "cost_erosion", "Avoid missed entries on fast breakouts", ["atr_pct"], "Volatility spikes", "Market fallback active", "N/A", "N/A", "0 trades/month", "Low", 8.3)
        ]

        # 12. Negative-Month Repair
        nmr_details = [
            ("False Breakout ADX Gate", "Filter breakout signals in false breakout months using ADX slope", "false_breakout", "Cushion false breakout months", ["adx_slope_3"], "ADX slope <= 0.5", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.5),
            ("Volume confirmation gate", "Require volume trend confirmation in negative months", "volume_weakness", "Cushion low-participation months", ["volume_trend"], "Volume <= 1.2x MA", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.3),
            ("EMA Reclaim Pullback Entry", "Enter pullback reclaim after breakout in negative months", "false_breakout", "Tighter stops in false breakout months", ["ema_50"], "ADX > 20", "Close reclaim EMA50", "Target 2.5x ATR", "1.8x ATR", "8 trades/month", "Low", 8.2),
            ("Cost-Aware TP Minimum Filter", "Gate entries in cost-erosion months with minimum TP filter", "cost_erosion", "Eliminate cost erosion in bad months", ["close", "atr_14"], "Target distance < 2.5x cost", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.0),
            ("Chop Regime Risk Halving", "Apply risk halving in chop-heavy negative months", "chop", "Halve losses in negative chop months", ["regime_toxic_chop"], "Chop active", "Apply risk_mult=0.5", "N/A", "N/A", "0 trades/month", "Low", 8.0),
            ("Funding Window Reversal Skip", "Skip negative month reversal trades near extreme funding rates", "funding_drag", "Cushion funding drag in negative months", ["fundingRate"], "Absolute funding >= 0.02%", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.1),
            ("Stop-Run Reclaim Reversal", "Fade breakouts that reclaim inside session ranges in negative months", "false_breakout", "Capture reversals in bad breakout months", ["close", "daily_high"], "ADX < 20", "Reenter daily range", "Target 2.0x ATR", "2.0x ATR", "7 trades/month", "Low", 8.4),
            ("ADX Slope Momentum Continuation", "Require accelerating momentum in low-activity negative months", "low_activity", "Ensure momentum in low activity months", ["adx_slope_5"], "ADX slope <= 1.5", "Filter active", "No entry", "2.0x ATR", "0 trades/month", "Low", 8.2)
        ]

        # 13. Zero-Month Rescue
        zmr_details = [
            ("VWAP Reclaim Zero-Month Rescue", "A VWAP reclaim signal active only in low-activity months", "low_activity", "Eliminate zero trade months", ["vwap", "close"], "monthly_trades == 0", "Close crosses above VWAP", "Target 2.5x ATR", "2.0x ATR", "5 trades/month", "Low", 9.0),
            ("Volatility Compression ZMR", "Volatility compression release signal to resolve zero months", "low_activity", "Zero-trade month rescue", ["bb_width"], "monthly_trades == 0", "Compression release close", "Target 3.0x ATR", "2.5x ATR", "4 trades/month", "Low", 9.0),
            ("ADX Slope Momentum ZMR", "Momentum continuation entry to resolve zero months", "low_activity", "Zero-trade month rescue", ["adx_slope_5"], "monthly_trades == 0", "ADX slope > 2.0", "Target 2.5x ATR", "2.0x ATR", "5 trades/month", "Low", 8.5),
            ("RSI Divergence MR ZMR", "RSI divergence mean reversion active in zero months", "low_activity", "Zero-trade month rescue", ["rsi_14", "close"], "monthly_trades == 0", "RSI divergence at extreme", "Target 2.0x ATR", "2.0x ATR", "4 trades/month", "Low", 8.3),
            ("EMA50 Pullback ZMR", "EMA50 pullback continuation active in zero months", "low_activity", "Zero-trade month rescue", ["ema_50"], "monthly_trades == 0", "EMA50 touch reclaim", "Target 2.5x ATR", "2.0x ATR", "4 trades/month", "Low", 8.2),
            ("London Open ZMR", "London open breakout continuation active in zero months", "low_activity", "Zero-trade month rescue", ["close"], "monthly_trades == 0", "London breakout close", "Target 3.0x ATR", "2.2x ATR", "5 trades/month", "Low", 8.4),
            ("NY Open ZMR", "NY open sweep reclaim active in zero months", "low_activity", "Zero-trade month rescue", ["close"], "monthly_trades == 0", "NY open sweep reclaim", "Target 2.0x ATR", "2.0x ATR", "5 trades/month", "Low", 8.6),
            ("Extreme Funding ZMR", "Extreme funding reversal active in zero months", "low_activity", "Zero-trade month rescue", ["fundingRate"], "monthly_trades == 0", "Extreme funding + reclaim", "Target 2.0x ATR", "2.0x ATR", "3 trades/month", "Low", 8.1)
        ]

        # 14. Trade Count Expansion
        tce_details = [
            ("Low-Activity Trend Sleeves", "Trend continuation sleeves active in low-activity months", "low_activity", "Expand trade count in quiet trends", ["close"], "monthly_trades < 10", "EMA pullback entry", "Target 3.0x ATR", "2.2x ATR", "6 trades/month", "Low", 8.5),
            ("Low-Activity Range Sleeves", "Range mean reversion sleeves active in low-activity months", "low_activity", "Expand trade count in quiet ranges", ["close"], "monthly_trades < 10", "Range boundary touch", "Target 2.0x ATR", "1.5x ATR", "8 trades/month", "Low", 8.5),
            ("Low-Volatility Sleeves", "Scalping sleeves active in low-volatility compression months", "low_activity", "Expand trade count in quiet volatility", ["atr_pct"], "monthly_trades < 10", "Volatility breakout", "Target 2.5x ATR", "2.0x ATR", "7 trades/month", "Low", 8.2),
            ("Post-Breakout Consolidation Sleeves", "Consolidation sleeves active after major trend breakouts", "low_activity", "Expand trade count in consolidation periods", ["close"], "monthly_trades < 10", "Consolidation range touch", "Target 2.0x ATR", "1.8x ATR", "6 trades/month", "Low", 8.0),
            ("High-Funding Sideways Sleeves", "Sideways sleeves active during high funding rate regimes", "low_activity", "Expand trade count during sideways carry", ["fundingRate"], "monthly_trades < 10", "Funding extreme touch", "Target 2.0x ATR", "2.0x ATR", "5 trades/month", "Low", 8.1),
            ("Quiet Session Sleeves", "Quiet session sleeves active during overnight Asian session", "low_activity", "Expand trade count during overnight quiet sessions", ["close"], "monthly_trades < 10", "Asian range boundary touch", "Target 1.5x ATR", "1.5x ATR", "9 trades/month", "Low", 8.3),
            ("High-Quality Filler", "Broad-market high-quality filler signals active in low activity", "low_activity", "Expand trade count with general filler", ["close"], "monthly_trades < 10", "Filler setup trigger", "Target 2.5x ATR", "2.0x ATR", "8 trades/month", "Low", 8.4),
            ("Activity Sleeve Router", "Router that activates secondary sleeves when monthly trades < 10", "low_activity", "Expand trade count to benchmark target", ["monthly_trade_count"], "monthly_trades < 10", "Activate secondary sleeves", "N/A", "N/A", "0 trades/month", "Low", 8.6)
        ]

        # Combine all details
        all_details = [
            ("TC", tc_details),
            ("BR", br_details),
            ("VE", ve_details),
            ("LS", ls_details),
            ("SB", sb_details),
            ("FB", fb_details),
            ("RB", rb_details),
            ("EA", ea_details),
            ("RR", rr_details),
            ("EO", eo_details),
            ("PF", pf_details),
            ("NMR", nmr_details),
            ("ZMR", zmr_details),
            ("TCE", tce_details)
        ]
        
        for prefix, details_list in all_details:
            for name, hyp, fail_cat, expected, req_data, r_gate, ent, ex, st, freq, cost_sens, prio in details_list:
                idea_id = self._make_id(prefix)
                ideas.append(ResearchIdea(
                    idea_id=idea_id,
                    name=name,
                    hypothesis=hyp,
                    failure_category=fail_cat,
                    expected_benefit=expected,
                    affected_months=[],
                    live_compatible=True,
                    lookahead_risk="NONE",
                    implementation_plan=f"Implement in candidate factory under {prefix} group, run search and verify metrics.",
                    acceptance_metrics={"pf_delta": ">= 0.0", "negative_month_delta": "<= 0"},
                    rejection_criteria={"trade_count": "< 10"},
                    required_data=req_data,
                    priority_score=prio,
                    status="GENERATED",
                    complexity_score=3.0,
                    overfit_risk_score=2.5,
                    live_compatibility_score=4.5,
                    when_it_fails="Sideways chop or trend exhaustion",
                    regime_gate=r_gate,
                    entry_rule=ent,
                    exit_rule=ex,
                    stop_rule=st,
                    expected_frequency=freq,
                    cost_sensitivity=cost_sens
                ))
                
        return ideas

    def rank_ideas(self) -> List[ResearchIdea]:
        """Returns ideas sorted by priority_score descending."""
        return sorted(self.ideas, key=lambda x: x.priority_score, reverse=True)

    def add_idea(self, idea: ResearchIdea):
        self.ideas.append(idea)

    def add_ideas(self, ideas: List[ResearchIdea]):
        self.ideas.extend(ideas)

    def mark_idea_result(self, idea_id: str, result: Dict[str, Any]):
        """Records a test result against an idea and updates status."""
        for idea in self.ideas:
            if idea.idea_id == idea_id:
                idea.test_result = result
                # Automatically promote status based on result status
                if result.get("status") in ["ACCEPTED", "REJECTED", "TESTED"]:
                    idea.status = result.get("status")
                return

    def save_ideas_json(self, output_path: str):
        """Saves all ideas with their test results to JSON."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Calculate distinct counts
        total_ideas = len(self.ideas)
        tested_ideas = sum(1 for i in self.ideas if i.status in ["TESTED", "ACCEPTED", "REJECTED"])
        generated_ideas = sum(1 for i in self.ideas if i.status == "GENERATED")
        deferred_ideas = sum(1 for i in self.ideas if i.status == "DEFERRED_TO_PHASE_12")
        
        failure_months = set()
        for i in self.ideas:
            failure_months.update(i.affected_months)
        failure_month_count = len(failure_months)
        
        status_counts = {}
        for s in ["GENERATED", "IMPLEMENTED", "TESTED", "REJECTED", "ACCEPTED", "DEFERRED_TO_PHASE_12", "NEEDS_DATA", "NEEDS_ENGINE_SUPPORT"]:
            status_counts[s] = sum(1 for i in self.ideas if i.status == s)
            
        data = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_ideas": total_ideas,
            "total_ideas_count": total_ideas,
            "generated_ideas_count": generated_ideas,
            "tested_ideas_count": tested_ideas,
            "deferred_ideas_count": deferred_ideas,
            "failure_month_count": failure_month_count,
            "lifecycle_status_counts": status_counts,
            "ideas": [idea.to_dict() for idea in self.ideas]
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def save_leaderboard_md(self, output_path: str):
        """Saves a ranked markdown leaderboard of all ideas."""
        ranked = self.rank_ideas()
        
        # Calculate distinct counts
        total_ideas = len(ranked)
        tested_ideas = sum(1 for i in ranked if i.status in ["TESTED", "ACCEPTED", "REJECTED"])
        generated_ideas = sum(1 for i in ranked if i.status == "GENERATED")
        deferred_ideas = sum(1 for i in ranked if i.status == "DEFERRED_TO_PHASE_12")
        
        failure_months = set()
        for i in ranked:
            failure_months.update(i.affected_months)
        failure_month_count = len(failure_months)
        
        status_counts = {}
        for s in ["GENERATED", "IMPLEMENTED", "TESTED", "REJECTED", "ACCEPTED", "DEFERRED_TO_PHASE_12", "NEEDS_DATA", "NEEDS_ENGINE_SUPPORT"]:
            status_counts[s] = sum(1 for i in ranked if i.status == s)

        lines = [
            "# Research Ideas Leaderboard — Phase 11.1",
            f"\n**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Total Ideas:** {total_ideas}",
            "",
            "## Summary Metrics",
            f"- **Generated Idea Count:** {generated_ideas}",
            f"- **Tested Idea Count:** {tested_ideas}",
            f"- **Deferred Idea Count:** {deferred_ideas}",
            f"- **Failure-Month Count:** {failure_month_count}",
            "",
            "### Lifecycle Status Breakdown",
        ]
        for s, count in status_counts.items():
            if count > 0:
                lines.append(f"- **{s}:** {count}")
                
        lines.extend([
            "",
            "| Rank | ID | Name | Category | Priority | Complexity | Overfit Risk | Live Compat Score | Status | PF Delta | Neg Month Delta |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ])
        
        for rank, idea in enumerate(ranked, 1):
            result = idea.test_result or {}
            pf_delta = f"{result.get('pf_delta', 0.0):+.3f}" if result else "—"
            neg_delta = f"{result.get('neg_month_delta', 0):+d}" if result else "—"
            lines.append(
                f"| {rank} | {idea.idea_id} | {idea.name} | {idea.failure_category} "
                f"| {idea.priority_score:.1f} | {idea.complexity_score:.1f} | {idea.overfit_risk_score:.1f} | {idea.live_compatibility_score:.1f} "
                f"| **{idea.status}** | {pf_delta} | {neg_delta} |"
            )

        lines.append("\n## Detail Entries")
        for idea in ranked:
            lines.append(f"\n### {idea.idea_id} — {idea.name}")
            lines.append(f"**Hypothesis:** {idea.hypothesis}")
            lines.append(f"**Failure Category:** {idea.failure_category}")
            lines.append(f"**Expected Benefit:** {idea.expected_benefit}")
            lines.append(f"**Affected Months:** {', '.join(idea.affected_months) or 'General'}")
            lines.append(f"**Live Compatibility Score:** {idea.live_compatibility_score:.1f}/5.0")
            lines.append(f"**Complexity Score:** {idea.complexity_score:.1f}/5.0")
            lines.append(f"**Overfit Risk Score:** {idea.overfit_risk_score:.1f}/5.0")
            lines.append(f"**Lookahead Risk:** {idea.lookahead_risk}")
            lines.append(f"**Implementation Plan:** {idea.implementation_plan}")

            if idea.test_result:
                r = idea.test_result
                lines.append(f"\n**Test Result:** {r.get('status', 'N/A')}")
                lines.append(f"- PnL Delta: {r.get('pnl_delta', 0.0):+.2f}")
                lines.append(f"- PF Delta: {r.get('pf_delta', 0.0):+.3f}")
                lines.append(f"- Neg Month Delta: {r.get('neg_month_delta', 0):+d}")
                lines.append(f"- Zero Month Delta: {r.get('zero_month_delta', 0):+d}")
                lines.append(f"- Trade Count Delta: {r.get('trade_delta', 0):+d}")
                lines.append(f"- OOS PnL Delta: {r.get('oos_pnl_delta', 0.0):+.2f}")
                lines.append(f"- Verdict: {r.get('verdict', 'N/A')}")
            else:
                lines.append(f"\n**Test Result:** PENDING ({idea.status})")

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
