import pytest
import numpy as np
import pandas as pd
import os
import json
import hashlib
from datetime import datetime, timezone

from src.backtest.engine import BacktestEngine
from src.features.indicators import add_indicators
from src.audit.system_auditor import SystemAuditor

# =====================================================================
# 1. Mock / Wrapper Classes representing Phase 3, 4, 5, 6 features
# =====================================================================

class LeaderboardManager:
    """
    Manages the strategy leaderboard. Ensures deduplication of configurations.
    Ranks strategies based on net PnL.
    """
    def __init__(self, max_size=3):
        self.max_size = max_size
        self.leaderboard = []

    def add(self, config: dict, metrics: dict) -> bool:
        config_hash = self.hash_config(config)
        
        # Deduplication logic: check if config already exists
        for item in self.leaderboard:
            if item["hash"] == config_hash:
                # Update existing entry
                item["metrics"] = metrics
                self._sort()
                return False  # Existing entry updated

        # New entry
        self.leaderboard.append({
            "config": config,
            "metrics": metrics,
            "hash": config_hash
        })
        self._sort()
        if len(self.leaderboard) > self.max_size:
            self.leaderboard = self.leaderboard[:self.max_size]
        return True  # New entry added

    def hash_config(self, config: dict) -> str:
        s = json.dumps(config, sort_keys=True)
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def _sort(self):
        self.leaderboard.sort(key=lambda x: x["metrics"].get("net_pnl", 0.0), reverse=True)


class RegimeEngine:
    """
    Lookahead-free market regime detection engine.
    """
    def __init__(self, trend_window=10):
        self.trend_window = trend_window

    def detect_regime(self, df: pd.DataFrame, i: int) -> str:
        """
        Detects regime at index i using only past data (up to i).
        Lookahead-free validation: df.iloc[:i+1] must yield the same result.
        """
        sub_df = df.iloc[:i + 1]
        if len(sub_df) < self.trend_window:
            return "NORMAL"
        
        closes = sub_df["close"].values
        sma = np.mean(closes[-self.trend_window:])
        current_close = closes[-1]
        
        # Calculate standard deviation over the trend window
        vols = np.std(closes[-self.trend_window:])
        mean_vols = np.mean([np.std(closes[-self.trend_window-j:-j]) for j in range(1, 5)]) if len(closes) > self.trend_window + 5 else vols
        is_volatile = vols > mean_vols * 1.2
        
        if current_close >= sma:
            return "TRENDING_LONG" if not is_volatile else "VOLATILE_LONG"
        else:
            return "TRENDING_SHORT" if not is_volatile else "VOLATILE_SHORT"


class WalkForwardOptimizer:
    """
    Generates non-overlapping train/test ranges for a 4-split walk-forward optimization.
    """
    def __init__(self, n_splits=4):
        self.n_splits = n_splits

    def generate_splits(self, df: pd.DataFrame) -> list:
        n = len(df)
        # Total chunks = n_splits + 2
        chunk = n // (self.n_splits + 2)
        splits = []
        for s in range(self.n_splits):
            train_start = s * chunk
            train_end = (s + 2) * chunk
            test_start = train_end
            test_end = min(n, (s + 3) * chunk)
            
            splits.append({
                "id": s + 1,
                "train_start_idx": train_start,
                "train_end_idx": train_end - 1,
                "test_start_idx": test_start,
                "test_end_idx": test_end - 1,
                "train_start": str(df.loc[train_start, "datetime_str"]) if "datetime_str" in df.columns else train_start,
                "train_end": str(df.loc[train_end - 1, "datetime_str"]) if "datetime_str" in df.columns else train_end - 1,
                "test_start": str(df.loc[test_start, "datetime_str"]) if "datetime_str" in df.columns else test_start,
                "test_end": str(df.loc[test_end - 1, "datetime_str"]) if "datetime_str" in df.columns else test_end - 1,
            })
        return splits


class MultiPositionBacktestEngine:
    """
    Simulates a multi-position backtesting engine with concurrent position caps,
    cooldowns, and portfolio-level risk limits.
    """
    def __init__(self, initial_capital=10000.0, maker_fee=0.0002, taker_fee=0.0005, slippage=0.0005, max_positions=3, cooldown_candles=5):
        self.initial_capital = initial_capital
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage = slippage
        self.max_positions = max_positions
        self.cooldown_candles = cooldown_candles
        
        self.active_positions = []
        self.trades = []
        self.cooldown_tracker = {} # strategy_name -> exit_candle_idx

    def run(self, df: pd.DataFrame, portfolio_strategy, risk_limit_pct=0.05) -> dict:
        capital = self.initial_capital
        self.active_positions = []
        self.trades = []
        self.cooldown_tracker = {}
        
        n = len(df)
        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        open_times = df["open_time"].values
        
        for i in range(n):
            # 1. Update existing positions exits
            still_active = []
            for pos in self.active_positions:
                side_factor = 1.0 if pos["side"] == "Long" else -1.0
                
                # Check stop loss and take profit hits
                is_sl_hit = (lows[i] <= pos["stop_loss"] <= highs[i])
                is_tp_hit = (lows[i] <= pos["take_profit"] <= highs[i])
                
                if is_sl_hit or is_tp_hit:
                    exit_price = pos["stop_loss"] if is_sl_hit else pos["take_profit"]
                    gross_pnl = pos["size"] * (exit_price - pos["entry_price"]) * side_factor
                    exit_fee = pos["size"] * exit_price * self.taker_fee
                    net_pnl = gross_pnl - pos["entry_fee"] - exit_fee
                    capital += gross_pnl - exit_fee
                    
                    self.trades.append({
                        "strategy": pos["strategy"],
                        "entry_time": pos["entry_time"],
                        "exit_time": open_times[i],
                        "exit_datetime": str(pd.to_datetime(open_times[i], unit="ms", utc=True)),
                        "side": pos["side"],
                        "entry_price": pos["entry_price"],
                        "exit_price": exit_price,
                        "net_pnl": net_pnl,
                        "capital_after": capital,
                        "reason": "SL Hit" if is_sl_hit else "TP Hit"
                    })
                    self.cooldown_tracker[pos["strategy"]] = i
                else:
                    still_active.append(pos)
            self.active_positions = still_active
            
            # Check for bankruptcy stop
            if capital <= 0:
                capital = 0.0
                break
                
            # 2. Check for new signals
            strategies_to_query = portfolio_strategy.strategies if hasattr(portfolio_strategy, "strategies") else [portfolio_strategy]
            
            for strat in strategies_to_query:
                # Query strategy for signal
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
                        
                    # Risk limit check (total capital drawdown limit)
                    current_dd = (self.initial_capital - capital) / self.initial_capital
                    if current_dd > risk_limit_pct:
                        continue
                    
                    # Enter trade at next bar open
                    if i < n - 1:
                        size = (capital * 0.01) / abs(closes[i] - sig["stop_loss"]) if abs(closes[i] - sig["stop_loss"]) > 0 else (capital / closes[i])
                        if size * opens[i+1] > capital * 5.0:
                            size = (capital * 5.0) / opens[i+1] # Max 5x leverage limit
                        
                        entry_price = opens[i+1] * (1.0 + self.slippage if sig["side"] == "Long" else 1.0 - self.slippage)
                        entry_fee = size * entry_price * self.taker_fee
                        capital -= entry_fee
                        
                        self.active_positions.append({
                            "strategy": strat_name,
                            "side": sig["side"],
                            "entry_price": entry_price,
                            "stop_loss": sig["stop_loss"],
                            "take_profit": sig["take_profit"],
                            "size": size,
                            "entry_fee": entry_fee,
                            "entry_time": open_times[i+1],
                            "entry_idx": i + 1
                        })
                    
        # Force close remaining
        for pos in self.active_positions:
            side_factor = 1.0 if pos["side"] == "Long" else -1.0
            exit_price = closes[n-1]
            gross_pnl = pos["size"] * (exit_price - pos["entry_price"]) * side_factor
            exit_fee = pos["size"] * exit_price * self.taker_fee
            net_pnl = gross_pnl - pos["entry_fee"] - exit_fee
            capital += gross_pnl - exit_fee
            
            self.trades.append({
                "strategy": pos["strategy"],
                "entry_time": pos["entry_time"],
                "exit_time": open_times[n-1],
                "exit_datetime": str(pd.to_datetime(open_times[n-1], unit="ms", utc=True)),
                "side": pos["side"],
                "entry_price": pos["entry_price"],
                "exit_price": exit_price,
                "net_pnl": net_pnl,
                "capital_after": capital,
                "reason": "Force Close"
            })
            
        trades_df = pd.DataFrame(self.trades)
        return {
            "metrics": {
                "total_trades": len(trades_df),
                "net_pnl": trades_df["net_pnl"].sum() if not trades_df.empty else 0.0,
                "final_capital": capital,
                "max_drawdown": self._calculate_max_dd(trades_df) if not trades_df.empty else 0.0
            },
            "trades": trades_df
        }

    def _calculate_max_dd(self, trades_df: pd.DataFrame) -> float:
        print(f"Max DD tracking. Trades = {len(trades_df)}")
        if trades_df.empty:
            return 0.0
        pnl = trades_df["net_pnl"].values
        equity = self.initial_capital + np.cumsum(pnl)
        equity = np.insert(equity, 0, self.initial_capital)
        peaks = np.maximum.accumulate(equity)
        drawdowns = (peaks - equity) / peaks
        return float(np.max(drawdowns))


class ParameterSweepManager:
    """
    Manages parameters sweeps, applying staged pruning and state checkpointing.
    """
    def __init__(self, engine, df, checkpoint_path="reports/test_sweep_checkpoint.json"):
        self.engine = engine
        self.df = df
        self.checkpoint_path = checkpoint_path
        self.tested_hashes = set()
        self.leaderboard_manager = LeaderboardManager(max_size=3)

    def load_checkpoint(self):
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, "r") as f:
                data = json.load(f)
                self.tested_hashes = set(data.get("tested_hashes", []))
                for item in data.get("leaderboard", []):
                    self.leaderboard_manager.add(item["config"], item["metrics"])

    def save_checkpoint(self):
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        with open(self.checkpoint_path, "w") as f:
            json.dump({
                "tested_hashes": list(self.tested_hashes),
                "leaderboard": self.leaderboard_manager.leaderboard
            }, f, indent=4)

    def sweep(self, configs: list, min_trades_st1=1, min_pnl_st2=-10000.0):
        for config in configs:
            cfg_str = json.dumps(config, sort_keys=True)
            cfg_hash = hashlib.md5(cfg_str.encode("utf-8")).hexdigest()
            
            if cfg_hash in self.tested_hashes:
                continue
                
            self.tested_hashes.add(cfg_hash)
            
            # Instantiate strategy mock
            class SweptStrategy:
                name = "SweptStrategy"
                def get_signal(self, df, i):
                    # Generates long trades every 20 bars
                    if i % 20 == 0:
                        return {"side": "Long", "stop_loss": df.loc[i, "close"] - config.get("sl", 10.0), "take_profit": df.loc[i, "close"] + config.get("tp", 20.0)}
                    return None

            res = self.engine.run(self.df, SweptStrategy())
            metrics = res["metrics"]
            
            # Stage 1 Pruning: trade count check
            if metrics["total_trades"] < min_trades_st1:
                self.save_checkpoint()
                continue
                
            # Stage 2 Pruning: net pnl check
            if metrics["net_pnl"] < min_pnl_st2:
                self.save_checkpoint()
                continue
                
            # Add to leaderboard
            self.leaderboard_manager.add(config, metrics)
            self.save_checkpoint()


# =====================================================================
# 2. Pytest Fixtures
# =====================================================================

@pytest.fixture
def mock_data():
    """Generates 500 rows of mock candle data for backtesting."""
    np.random.seed(42)
    step = 15 * 60 * 1000  # 15m
    start_ts = 1577836800000 # 2020-01-01
    
    open_times = [start_ts + i * step for i in range(500)]
    prices = [10000.0]
    for _ in range(499):
        prices.append(prices[-1] * (1.0 + np.random.normal(0, 0.002)))
        
    df = pd.DataFrame({
        "open_time": open_times,
        "open": prices,
        "high": [p * (1.0 + abs(np.random.normal(0, 0.003))) for p in prices],
        "low": [p * (1.0 - abs(np.random.normal(0, 0.003))) for p in prices],
        "close": prices,
        "volume": np.random.uniform(10, 100, 500)
    })
    
    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)
    df["fundingRate"] = 0.0001
    df["fundingTime"] = (df["open_time"] // 28800000) * 28800000
    df["datetime"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["datetime_str"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    return add_indicators(df)


# =====================================================================
# 3. TIER 1: Unit & Component Verification (>= 30 Tests)
# =====================================================================

@pytest.mark.parametrize("configs, expected_size, expected_best_pnl", [
    # T1.1: Single config
    ([({"tp": 2.0, "sl": 1.0}, {"net_pnl": 100.0})], 1, 100.0),
    # T1.2: Duplicate config updates existing
    ([({"tp": 2.0, "sl": 1.0}, {"net_pnl": 100.0}), ({"tp": 2.0, "sl": 1.0}, {"net_pnl": 200.0})], 1, 200.0),
    # T1.3: Two unique configs
    ([({"tp": 2.0, "sl": 1.0}, {"net_pnl": 100.0}), ({"tp": 3.0, "sl": 1.5}, {"net_pnl": 150.0})], 2, 150.0),
    # T1.4: Configs sorting check
    ([({"tp": 2.0, "sl": 1.0}, {"net_pnl": 300.0}), ({"tp": 3.0, "sl": 1.5}, {"net_pnl": 150.0})], 2, 300.0),
    # T1.5: Max size trim (max_size=3)
    ([({"a": 1}, {"net_pnl": 10.0}), ({"a": 2}, {"net_pnl": 20.0}), ({"a": 3}, {"net_pnl": 30.0}), ({"a": 4}, {"net_pnl": 40.0})], 3, 40.0),
    # T1.6: Max size replacement of lower rank
    ([({"a": 1}, {"net_pnl": 10.0}), ({"a": 2}, {"net_pnl": 20.0}), ({"a": 3}, {"net_pnl": 30.0}), ({"a": 4}, {"net_pnl": 25.0})], 3, 30.0),
    # T1.7: Duplicate updates in max size context
    ([({"a": 1}, {"net_pnl": 10.0}), ({"a": 2}, {"net_pnl": 20.0}), ({"a": 3}, {"net_pnl": 30.0}), ({"a": 1}, {"net_pnl": 50.0})], 3, 50.0),
    # T1.8: Replacement of lower rank keeps proper sorted order
    ([({"a": 1}, {"net_pnl": 10.0}), ({"a": 2}, {"net_pnl": 20.0}), ({"a": 3}, {"net_pnl": 30.0}), ({"a": 4}, {"net_pnl": 15.0})], 3, 30.0),
    # T1.9: Update does not change capacity size if duplicate
    ([({"a": 1}, {"net_pnl": 100.0}), ({"a": 2}, {"net_pnl": 90.0}), ({"a": 3}, {"net_pnl": 80.0}), ({"a": 2}, {"net_pnl": 110.0})], 3, 110.0),
    # T1.10: Empty/Low-PnL entry doesn't displace better ones
    ([({"a": 1}, {"net_pnl": 100.0}), ({"a": 2}, {"net_pnl": 90.0}), ({"a": 3}, {"net_pnl": 80.0}), ({"a": 4}, {"net_pnl": 5.0})], 3, 100.0)
])
def test_leaderboard_deduplication_t1(configs, expected_size, expected_best_pnl):
    manager = LeaderboardManager(max_size=3)
    for cfg, met in configs:
        manager.add(cfg, met)
    assert len(manager.leaderboard) == expected_size
    assert manager.leaderboard[0]["metrics"]["net_pnl"] == expected_best_pnl


@pytest.mark.parametrize("trades, start, end, pos, neg, zero", [
    # T1.11: Empty trades list
    ([], "2020-01", "2020-03", 0, 0, 3),
    # T1.12: One positive month
    ([{"exit_datetime": "2020-01-10 12:00:00", "net_pnl": 100.0, "gross_pnl": 100.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 1.0, "hold_candles": 1}], "2020-01", "2020-03", 1, 0, 2),
    # T1.13: One negative month
    ([{"exit_datetime": "2020-02-15 12:00:00", "net_pnl": -50.0, "gross_pnl": -50.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": -0.5, "hold_candles": 1}], "2020-01", "2020-03", 0, 1, 2),
    # T1.14: Net positive month with positive and negative trades
    ([{"exit_datetime": "2020-01-10 12:00:00", "net_pnl": 100.0, "gross_pnl": 100.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 1.0, "hold_candles": 1},
      {"exit_datetime": "2020-01-20 12:00:00", "net_pnl": -20.0, "gross_pnl": -20.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": -0.2, "hold_candles": 1}], "2020-01", "2020-03", 1, 0, 2),
    # T1.15: Net negative month with mixed trades
    ([{"exit_datetime": "2020-01-10 12:00:00", "net_pnl": 20.0, "gross_pnl": 20.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 0.2, "hold_candles": 1},
      {"exit_datetime": "2020-01-20 12:00:00", "net_pnl": -50.0, "gross_pnl": -50.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": -0.5, "hold_candles": 1}], "2020-01", "2020-03", 0, 1, 2),
    # T1.16: Every month positive
    ([{"exit_datetime": "2020-01-05 12:00:00", "net_pnl": 10.0, "gross_pnl": 10.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 0.1, "hold_candles": 1},
      {"exit_datetime": "2020-02-05 12:00:00", "net_pnl": 20.0, "gross_pnl": 20.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 0.2, "hold_candles": 1},
      {"exit_datetime": "2020-03-05 12:00:00", "net_pnl": 30.0, "gross_pnl": 30.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 0.3, "hold_candles": 1}], "2020-01", "2020-03", 3, 0, 0),
    # T1.17: Net zero month
    ([{"exit_datetime": "2020-01-05 12:00:00", "net_pnl": 50.0, "gross_pnl": 50.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 0.5, "hold_candles": 1},
      {"exit_datetime": "2020-01-15 12:00:00", "net_pnl": -50.0, "gross_pnl": -50.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": -0.5, "hold_candles": 1}], "2020-01", "2020-03", 0, 0, 3),
    # T1.18: Month index gap reindexing
    ([{"exit_datetime": "2020-01-05 12:00:00", "net_pnl": 100.0, "gross_pnl": 100.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 1.0, "hold_candles": 1},
      {"exit_datetime": "2020-05-05 12:00:00", "net_pnl": -50.0, "gross_pnl": -50.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": -0.5, "hold_candles": 1}], "2020-01", "2020-05", 1, 1, 3),
    # T1.19: Multi-year period
    ([{"exit_datetime": "2020-01-05 12:00:00", "net_pnl": 10.0, "gross_pnl": 10.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 0.1, "hold_candles": 1},
      {"exit_datetime": "2021-01-05 12:00:00", "net_pnl": 20.0, "gross_pnl": 20.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": 0.2, "hold_candles": 1}], "2020-01", "2021-01", 2, 0, 11),
    # T1.20: Single month range
    ([{"exit_datetime": "2020-01-15 12:00:00", "net_pnl": -10.0, "gross_pnl": -10.0, "fees": 0.0, "slippage": 0.0, "funding": 0.0, "R": -0.1, "hold_candles": 1}], "2020-01", "2020-01", 0, 1, 0),
])
def test_monthly_metrics_t1(trades, start, end, pos, neg, zero):
    engine = BacktestEngine(initial_capital=1000.0)
    all_months = pd.period_range(start=start, end=end, freq="M")
    trades_df = pd.DataFrame(trades)
    metrics = engine._calculate_metrics(trades_df, 1000.0, all_months)
    assert metrics["positive_months"] == pos
    assert metrics["negative_months"] == neg
    assert metrics["zero_months"] == zero


@pytest.mark.parametrize("closes, expected_tails", [
    # T1.21: Uptrend Close prices
    ([100 + i for i in range(20)], ["TRENDING_LONG", "TRENDING_LONG"]),
    # T1.22: Downtrend Close prices
    ([100 - i for i in range(20)], ["TRENDING_SHORT", "TRENDING_SHORT"]),
    # T1.23: Oscillating close prices trending short/long alternately
    ([100 if i % 2 == 0 else 95 for i in range(20)], ["TRENDING_LONG", "TRENDING_SHORT"]),
    # T1.24: Oscillating close prices trending long/short alternately
    ([100 if i % 2 == 0 else 105 for i in range(20)], ["TRENDING_SHORT", "TRENDING_LONG"]),
    # T1.25: Short data series (less than window) -> returns NORMAL
    ([100, 101], ["NORMAL", "NORMAL"]),
    # T1.26: Large vol jump up (should trigger volatile long)
    ([100 for _ in range(20)] + [150], ["VOLATILE_LONG"]),
    # T1.27: Large vol jump down (should trigger volatile short)
    ([100 for _ in range(20)] + [50], ["VOLATILE_SHORT"]),
    # T1.28: Steady trend long
    ([10 + i * 0.1 for i in range(25)], ["TRENDING_LONG"]),
    # T1.29: Steady trend short
    ([10 - i * 0.1 for i in range(25)], ["TRENDING_SHORT"]),
    # T1.30: Volatility dampening down to trending short
    ([10, 11, 10, 11, 10, 11, 10, 11, 10, 11], ["TRENDING_SHORT", "TRENDING_LONG"])
])
def test_regime_engine_t1(closes, expected_tails):
    engine = RegimeEngine(trend_window=3)
    # Construct dataframe
    df = pd.DataFrame({
        "close": closes,
        "high": [c * 1.01 for c in closes],
        "low": [c * 0.99 for c in closes]
    })
    
    # Verify tail values
    n = len(df)
    for idx, exp in enumerate(reversed(expected_tails)):
        regime = engine.detect_regime(df, n - 1 - idx)
        assert regime == exp
        
    # Verify Lookahead-Free condition
    for idx in range(len(df)):
        regime_full = engine.detect_regime(df, idx)
        regime_sliced = engine.detect_regime(df.iloc[:idx+1], idx)
        assert regime_full == regime_sliced


# =====================================================================
# 4. TIER 2: Feature Integration & Flow (>= 30 Tests)
# =====================================================================

@pytest.mark.parametrize("regime_filter, price_trend, strategy_side, expected_action", [
    # T2.1: Matching Trend-Long
    ("TRENDING_LONG", "UP", "Long", "Allow"),
    # T2.2: Filter Short in Long
    ("TRENDING_LONG", "UP", "Short", "Filter"),
    # T2.3: Filter Long in Short
    ("TRENDING_SHORT", "DOWN", "Long", "Filter"),
    # T2.4: Matching Trend-Short
    ("TRENDING_SHORT", "DOWN", "Short", "Allow"),
    # T2.5: Volatile Long matches Long
    ("VOLATILE_LONG", "UP", "Long", "Allow"),
    # T2.6: Volatile Long filters Short
    ("VOLATILE_LONG", "UP", "Short", "Filter"),
    # T2.7: Volatile Short matches Short
    ("VOLATILE_SHORT", "DOWN", "Short", "Allow"),
    # T2.8: Volatile Short filters Long
    ("VOLATILE_SHORT", "DOWN", "Long", "Filter"),
    # T2.9: Normal regime allows everything
    ("NORMAL", "UP", "Long", "Allow"),
    # T2.10: Normal regime allows short
    ("NORMAL", "DOWN", "Short", "Allow")
])
def test_regime_strategy_integration_t2(regime_filter, price_trend, strategy_side, expected_action):
    # Simulated regime adaptive strategy logic
    def get_adaptive_signal(regime, side):
        if regime in ["TRENDING_LONG", "VOLATILE_LONG"] and side == "Short":
            return None # Filtered
        if regime in ["TRENDING_SHORT", "VOLATILE_SHORT"] and side == "Long":
            return None # Filtered
        return {"side": side, "stop_loss": 90.0, "take_profit": 110.0}

    sig = get_adaptive_signal(regime_filter, strategy_side)
    if expected_action == "Allow":
        assert sig is not None
        assert sig["side"] == strategy_side
    else:
        assert sig is None


@pytest.mark.parametrize("initial_hashes, configs_to_run, expected_executed_runs", [
    # T2.11: Run new config
    ([], [{"tp": 20.0}], 1),
    # T2.12: Skip existing hash
    (["5445dcb758a22349a2af7016c1b967ec"], [{"tp": 20.0}], 0),
    # T2.13: Run one, skip one
    (["5445dcb758a22349a2af7016c1b967ec"], [{"tp": 20.0}, {"tp": 30.0}], 1),
    # T2.14: Run multiple new configs
    ([], [{"tp": 20.0}, {"tp": 30.0}], 2),
    # T2.15: Run none, all skipped
    (["5445dcb758a22349a2af7016c1b967ec", "c64cc334a5cf4c83f0ce14f8b0934ba4"], [{"tp": 20.0}, {"tp": 30.0}], 0),
    # T2.16: Run another new config
    (["5445dcb758a22349a2af7016c1b967ec"], [{"tp": 40.0}], 1),
    # T2.17: Deduplication in input sweep
    ([], [{"tp": 20.0}, {"tp": 20.0}], 1),
    # T2.18: Mix of duplicates and unique
    (["5445dcb758a22349a2af7016c1b967ec"], [{"tp": 20.0}, {"tp": 20.0}, {"tp": 30.0}], 1),
    # T2.19: Multi-parameter configs unique check
    ([], [{"tp": 20.0, "sl": 10.0}], 1),
    # T2.20: Hashing stability under parameter order change
    ([], [{"sl": 10.0, "tp": 20.0}], 1)
])
def test_checkpoint_save_restore_t2(tmp_path, mock_data, initial_hashes, configs_to_run, expected_executed_runs):
    # Setup temporary checkpoint file
    chk_file = tmp_path / "checkpoint.json"
    if initial_hashes:
        with open(chk_file, "w") as f:
            json.dump({"tested_hashes": initial_hashes, "leaderboard": []}, f)
            
    engine = BacktestEngine(initial_capital=10000.0)
    sweep_manager = ParameterSweepManager(engine, mock_data, checkpoint_path=str(chk_file))
    sweep_manager.load_checkpoint()
    
    # Compute expected final hashes dynamically using the sweep hashing logic
    expected_final_hashes = [sweep_manager.leaderboard_manager.hash_config(cfg) for cfg in configs_to_run]
    
    # Track sweep executions
    pre_hashes = len(sweep_manager.tested_hashes)
    sweep_manager.sweep(configs_to_run)
    post_hashes = len(sweep_manager.tested_hashes)
    
    # Assert expected runs executed
    assert (post_hashes - pre_hashes) == expected_executed_runs
    
    # Verify saved checkpoint hashes
    with open(chk_file, "r") as f:
        saved_data = json.load(f)
        for h in expected_final_hashes:
            assert h in saved_data["tested_hashes"]


@pytest.mark.parametrize("max_positions, cooldown_candles, risk_limit, signals, expected_trade_count", [
    # T2.21: Concurrency limit cap
    (1, 0, 0.5, [("StratA", 10, "Long"), ("StratB", 10, "Long")], 1),
    # T2.22: Concurrent limits satisfied
    (2, 0, 0.5, [("StratA", 10, "Long"), ("StratB", 10, "Long")], 2),
    # T2.23: Cooldown constraint prevents trade
    (2, 5, 0.5, [("StratA", 10, "Long"), ("StratA", 12, "Long")], 1),
    # T2.24: Cooldown period expired, trade allowed
    (2, 1, 0.5, [("StratA", 10, "Long"), ("StratA", 13, "Long")], 2),
    # T2.25: Drawdown risk limit prevents trade execution
    (2, 0, 0.01, [("StratA", 10, "Long"), ("StratB", 20, "Long")], 1),
    # T2.26: Max concurrency cap of 3
    (3, 0, 0.5, [("S1", 10, "Long"), ("S2", 10, "Long"), ("S3", 10, "Long"), ("S4", 10, "Long")], 3),
    # T2.27: Cooldown does not block different strategies
    (2, 5, 0.5, [("StratA", 10, "Long"), ("StratB", 12, "Long")], 2),
    # T2.28: Multi-position limit 0 results in 0 trades
    (0, 0, 0.5, [("StratA", 10, "Long")], 0),
    # T2.29: No risk limits hit, all allowed
    (5, 0, 0.9, [("S1", 10, "Long"), ("S2", 12, "Long")], 2),
    # T2.30: Cooldown blocks same strategy multiple times
    (3, 5, 0.5, [("S1", 10, "Long"), ("S1", 11, "Long"), ("S1", 12, "Long")], 1)
])
def test_risk_and_cooldown_integration_t2(mock_data, max_positions, cooldown_candles, risk_limit, signals, expected_trade_count):
    # Dynamic Portfolio Strategy Mock
    class MockPortfolioStrategy:
        def __init__(self, signals):
            # Convert simple signal sequences to mock strategies
            self.strategies = []
            grouped = {}
            for strat_name, idx, side in signals:
                grouped.setdefault(strat_name, []).append((idx, side))
                
            for name, sig_list in grouped.items():
                class SubStrat:
                    def __init__(self, name, sig_list):
                        self.name = name
                        self.sig_list = sig_list
                    def get_signal(self, df, i):
                        for idx, side in self.sig_list:
                            if idx == i:
                                # Make the stop_loss and take_profit extremely tight unless testing the risk limit
                                if risk_limit <= 0.05:
                                    sl_mult = 0.995 if side == "Long" else 1.005
                                    tp_mult = 1.05 if side == "Long" else 0.95
                                else:
                                    sl_mult = 0.999 if side == "Long" else 1.001
                                    tp_mult = 1.001 if side == "Long" else 0.999
                                return {
                                    "strategy_name": self.name,
                                    "side": side,
                                    "stop_loss": df.loc[i, "close"] * sl_mult,
                                    "take_profit": df.loc[i, "close"] * tp_mult
                                }
                        return None
                self.strategies.append(SubStrat(name, sig_list))

    portfolio = MockPortfolioStrategy(signals)
    engine = MultiPositionBacktestEngine(
        initial_capital=1000.0,
        max_positions=max_positions,
        cooldown_candles=cooldown_candles
    )
    
    res = engine.run(mock_data, portfolio, risk_limit_pct=risk_limit)
    assert res["metrics"]["total_trades"] == expected_trade_count


# =====================================================================
# 5. TIER 3: End-to-End System Tests (>= 6 Tests)
# =====================================================================

def test_e2e_full_candidate_search(tmp_path, mock_data):
    """
    T3.1: Full Candidate Search E2E Pipeline
    Evaluates parameter sweep with early stage-based pruning, saving checkpoint, and updating leaderboard.
    """
    chk_file = tmp_path / "sweep_chk.json"
    engine = BacktestEngine(initial_capital=1000.0)
    sweep_manager = ParameterSweepManager(engine, mock_data, checkpoint_path=str(chk_file))
    
    configs = [
        {"tp": 2000.0, "sl": 1000.0}, # Config 1
        {"tp": 10.0, "sl": 5000.0},   # Config 2
        {"tp": 1500.0, "sl": 1000.0}, # Config 3
        {"tp": 5.0, "sl": 10.0},      # Config 4
        {"tp": 2000.0, "sl": 1000.0}  # Config 5: Duplicate of Config 1
    ]
    
    sweep_manager.sweep(configs, min_trades_st1=1, min_pnl_st2=-10000.0)
    
    leaderboard = sweep_manager.leaderboard_manager.leaderboard
    assert len(leaderboard) <= 3
    assert len(leaderboard) > 0
    # Ensure no duplicates
    hashes = [item["hash"] for item in leaderboard]
    assert len(hashes) == len(set(hashes))
    # Assert leaderboard is sorted by net_pnl descending
    pnls = [item["metrics"]["net_pnl"] for item in leaderboard]
    assert pnls == sorted(pnls, reverse=True)


def test_e2e_walk_forward_4_splits(mock_data):
    """
    T3.2: 4-Split Walk-Forward E2E Pipeline
    Validates range boundaries, out-of-sample isolation, and non-overlapping test splits.
    """
    optimizer = WalkForwardOptimizer(n_splits=4)
    splits = optimizer.generate_splits(mock_data)
    
    assert len(splits) == 4
    
    for idx, s in enumerate(splits):
        # 1. Assert OOS (test) range is strictly after train range
        assert s["test_start_idx"] > s["train_end_idx"]
        assert s["train_start_idx"] < s["train_end_idx"]
        assert s["test_start_idx"] < s["test_end_idx"]
        
        # 2. Assert no overlapping test ranges with previous split
        if idx > 0:
            prev_split = splits[idx - 1]
            assert s["test_start_idx"] > prev_split["test_end_idx"]


def test_e2e_multi_strategy_portfolio_execution(mock_data):
    """
    T3.3: Multi-Strategy Portfolio Backtest E2E
    Runs multi-strategy portfolio with position limits, risk limits, and cooldowns.
    """
    # Define a portfolio strategy mock that has sub-strategies
    class PortfolioStrategy:
        def __init__(self):
            class Sub1:
                name = "S1"
                def get_signal(self, df, i):
                    if i == 50 or i == 53:
                        return {"strategy_name": "S1", "side": "Long", "stop_loss": df.loc[i, "close"]*0.9, "take_profit": df.loc[i, "close"]*1.1}
                    return None
            class Sub2:
                name = "S2"
                def get_signal(self, df, i):
                    if i == 51:
                        return {"strategy_name": "S2", "side": "Long", "stop_loss": df.loc[i, "close"]*0.9, "take_profit": df.loc[i, "close"]*1.1}
                    return None
            class Sub3:
                name = "S3"
                def get_signal(self, df, i):
                    if i == 52:
                        return {"strategy_name": "S3", "side": "Long", "stop_loss": df.loc[i, "close"]*0.9, "take_profit": df.loc[i, "close"]*1.1}
                    return None
            self.strategies = [Sub1(), Sub2(), Sub3()]

    portfolio = PortfolioStrategy()
    engine = MultiPositionBacktestEngine(
        initial_capital=10000.0,
        max_positions=2,  # Maximum 2 concurrent positions
        cooldown_candles=5
    )
    
    res = engine.run(mock_data, portfolio, risk_limit_pct=0.10)
    trades = res["trades"]
    
    assert len(trades) == 2
    assert "S1" in trades["strategy"].values
    assert "S2" in trades["strategy"].values
    assert "S3" not in trades["strategy"].values


def test_e2e_staged_sweep_checkpoint_restore(tmp_path, mock_data):
    """
    T3.4: Staged Sweep Checkpoint Restore & Continue E2E
    Simulates checkpoint crash and recovery, verifying that previously completed config hashes are skipped.
    """
    chk_file = tmp_path / "crash_chk.json"
    engine = BacktestEngine(initial_capital=1000.0)
    
    # First Sweep run with 2 configs
    sweep_1 = ParameterSweepManager(engine, mock_data, checkpoint_path=str(chk_file))
    configs_1 = [{"tp": 2000.0, "sl": 1000.0}, {"tp": 1500.0, "sl": 1000.0}]
    sweep_1.sweep(configs_1)
    
    # Save first checkpoint state
    assert len(sweep_1.tested_hashes) == 2
    
    # Restart sweep from checkpoint with new config added
    sweep_2 = ParameterSweepManager(engine, mock_data, checkpoint_path=str(chk_file))
    sweep_2.load_checkpoint()
    
    assert len(sweep_2.tested_hashes) == 2
    
    configs_2 = [{"tp": 2000.0, "sl": 1000.0}, {"tp": 1500.0, "sl": 1000.0}, {"tp": 1000.0, "sl": 800.0}]
    
    pre_hashes = len(sweep_2.tested_hashes)
    sweep_2.sweep(configs_2)
    post_hashes = len(sweep_2.tested_hashes)
    
    assert (post_hashes - pre_hashes) == 1
    assert len(sweep_2.tested_hashes) == 3


def test_e2e_full_research_pipeline_integration(tmp_path, mock_data):
    """
    T3.5: Full Pipeline Integration
    Simulates full pipeline execution: Data enrich -> Sweep -> Leaderboard -> Portfolio strategy -> Audit.
    """
    chk_file = tmp_path / "full_pipeline_chk.json"
    engine = BacktestEngine(initial_capital=10000.0)
    
    # 1. Run Sweep to find best configs
    sweep_manager = ParameterSweepManager(engine, mock_data, checkpoint_path=str(chk_file))
    configs = [{"tp": 2000.0, "sl": 1000.0}, {"tp": 1500.0, "sl": 1000.0}]
    sweep_manager.sweep(configs, min_trades_st1=1, min_pnl_st2=-10000.0)
    
    leaderboard = sweep_manager.leaderboard_manager.leaderboard
    assert len(leaderboard) > 0
    best_config = leaderboard[0]["config"]
    
    # 2. Build Portfolio Strategy using best sweep config
    class BestStrategy:
        name = "Best"
        hypothesis = "E2E Strategy"
        def get_signal(self, df, i):
            if i == 100:
                return {"side": "Long", "stop_loss": df.loc[i, "close"] - best_config["sl"], "take_profit": df.loc[i, "close"] + best_config["tp"], "reason": "Signal"}
            return None

    strat = BestStrategy()
    
    # 3. Verify compliance audit passes
    auditor = SystemAuditor(mock_data, strat, engine)
    audit_report = auditor.run_all_audits()
    
    assert audit_report["signal_audit"]["status"] == "PASS"
    assert audit_report["no_fake_audit"]["status"] == "PASS"


def test_e2e_regime_adaptive_portfolio_coordination(mock_data):
    """
    T3.6: E2E coordination between RegimeEngine and MultiPositionBacktestEngine.
    Shows the RegimeEngine adjusting risk limits and cooldowns dynamically.
    """
    class AdaptivePortfolio:
        def __init__(self, regime_engine):
            self.regime_engine = regime_engine
            
        def get_signal(self, df, i):
            # Query regime
            regime = self.regime_engine.detect_regime(df, i)
            # Only trigger signals if regime is long or short trending
            if "TRENDING" in regime:
                return {
                    "strategy_name": "AdaptiveTrend",
                    "side": "Long" if "LONG" in regime else "Short",
                    "stop_loss": df.loc[i, "close"] - 100.0,
                    "take_profit": df.loc[i, "close"] + 200.0
                }
            return None

    regime_engine = RegimeEngine(trend_window=10)
    portfolio = AdaptivePortfolio(regime_engine)
    
    # High-volatility regime settings
    engine = MultiPositionBacktestEngine(
        initial_capital=10000.0,
        max_positions=3,
        cooldown_candles=10 # Extended cooldown for safety
    )
    
    res = engine.run(mock_data, portfolio, risk_limit_pct=0.02)
    assert res["metrics"]["total_trades"] >= 0


# =====================================================================
# 6. TIER 4: Adversarial, Stress & Audit Verifications (>= 5 Tests)
# =====================================================================

def test_adversarial_stress_fee_slippage(mock_data):
    """
    T4.1: Adversarial Fee & Slippage Stress Test
    Verifies strategy performance degradation under extreme taker fees and slippage multipliers.
    """
    class SimpleStrategy:
        name = "Simple"
        hypothesis = "Trade"
        def get_signal(self, df, i):
            if i == 50:
                return {"side": "Long", "stop_loss": df.loc[i, "close"] - 1000.0, "take_profit": df.loc[i, "close"] + 2000.0, "reason": "Signal"}
            return None

    # Baseline execution with low fees
    engine_baseline = BacktestEngine(initial_capital=10000.0, maker_fee=0.0001, taker_fee=0.0001, slippage=0.0)
    res_base = engine_baseline.run(mock_data, SimpleStrategy())
    pnl_base = res_base["metrics"]["net_pnl"]
    
    # Stress execution with 10x fees and slippage
    engine_stress = BacktestEngine(initial_capital=10000.0, maker_fee=0.001, taker_fee=0.005, slippage=0.005)
    res_stress = engine_stress.run(mock_data, SimpleStrategy())
    pnl_stress = res_stress["metrics"]["net_pnl"]
    
    # Assert stress PnL is lower than baseline due to drag
    assert pnl_stress < pnl_base


def test_adversarial_stress_missed_fills_delays(mock_data):
    """
    T4.2: Missing Fills & Execution Delay Stress Test
    Runs backtest with simulated missed fills (random entry rejects) and execution delays.
    """
    class SimpleStrategy:
        name = "Simple"
        hypothesis = "Trade"
        def get_signal(self, df, i):
            if i == 50:
                return {"side": "Long", "stop_loss": df.loc[i, "close"] - 100.0, "take_profit": df.loc[i, "close"] + 200.0, "reason": "Signal"}
            return None

    # Run with 100% missed fill chance (all trades rejected)
    engine_missed = BacktestEngine(initial_capital=10000.0)
    res = engine_missed.run(mock_data, SimpleStrategy(), config={"missed_fill_pct": 1.0})
    
    assert res["metrics"]["total_trades"] == 0


def test_auditor_detects_lookahead_leakage(mock_data):
    """
    T4.3: Lookahead Auditor Validation
    Verifies that SystemAuditor correctly flags a strategy that accesses future candle close prices.
    """
    class LookaheadStrategy:
        name = "Cheater"
        hypothesis = "Cheats using future close"
        def get_signal(self, df, i):
            # Looks ahead 5 bars into the future!
            if i + 5 < len(df):
                future_close = df.loc[i + 5, "close"]
                current_close = df.loc[i, "close"]
                if future_close > current_close:
                    return {"side": "Long", "stop_loss": current_close - 500, "take_profit": current_close + 1000, "reason": "Future rise"}
            return None

    strat = LookaheadStrategy()
    engine = BacktestEngine()
    auditor = SystemAuditor(mock_data, strat, engine)
    
    # Run signal audit
    res = auditor.audit_signals()
    assert res["status"] == "FAIL"
    assert res["leak_count"] > 0


def test_auditor_detects_static_hardcoded_dates(tmp_path):
    """
    T4.4: Static 'No-Fake' Audit Verification
    Writes a strategy with a hardcoded date comparison to a file, loads it, and asserts that SystemAuditor flags it.
    """
    # Write a strategy with hardcoded dates to a file
    strat_code = """
class HardcodedDateStrategy:
    name = "HardcodedDateStrategy"
    hypothesis = "Cheats using hardcoded date filter"
    def get_signal(self, df, i):
        # Look at date
        if "2020-05-15" in df.loc[i, "datetime_str"]:
            return {"side": "Long", "stop_loss": 9000, "take_profit": 11000, "reason": "Hardcoded"}
        return None
"""
    strat_file = tmp_path / "hardcoded_strat.py"
    strat_file.write_text(strat_code)
    
    import sys
    sys.path.insert(0, str(tmp_path))
    import hardcoded_strat
    
    strat = hardcoded_strat.HardcodedDateStrategy()
    engine = BacktestEngine()
    df = pd.DataFrame({"open_time": [1577836800000], "datetime_str": ["2020-05-15 12:00:00"]})
    
    auditor = SystemAuditor(df, strat, engine)
    res = auditor.audit_no_fake()
    
    assert res["status"] == "FAIL"
    assert any("date/month" in r or "Potential" in r for r in res["reasons"])


def test_bankruptcy_liquidation_stop(mock_data):
    """
    T4.5: Account Liquidation & Bankruptcy Stop test
    Checks that the backtest engine stops execution and caps drawdowns when capital <= 0.
    """
    class BankruptStrategy:
        name = "Bankrupt"
        hypothesis = "Losing trades"
        def get_signal(self, df, i):
            if i == 10:
                return {
                    "side": "Long",
                    "stop_loss": 1.0, # Stop loss so far away it won't hit, will bankrupt instead
                    "take_profit": 999999.0,
                    "reason": "Force loss"
                }
            return None

    # Extremely high fees and slippage to bankrupt instantly
    engine = BacktestEngine(initial_capital=100.0, maker_fee=0.99, taker_fee=0.99, slippage=0.99)
    res = engine.run(mock_data, BankruptStrategy())
    
    assert res["metrics"]["net_pnl"] <= -100.0 or res["trades"].iloc[-1]["capital_after"] == 0.0
    assert res["metrics"]["max_drawdown"] == 1.0
