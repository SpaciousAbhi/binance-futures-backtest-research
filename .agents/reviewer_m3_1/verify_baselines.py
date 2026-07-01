import os
import sys

# Add root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import yaml
from src.data.downloader import BinanceDownloader
from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

# Load configs
def load_config(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)
    return {}

project_cfg = load_config("configs/project.yaml")
costs_cfg = load_config("configs/costs.yaml")

symbol = project_cfg.get("symbol", "BTCUSDT")
start_date = project_cfg.get("start_date", "2020-01-01")
end_date = project_cfg.get("end_date", "2026-06-28")
raw_dir = project_cfg.get("raw_data_dir", "data/raw")
processed_dir = project_cfg.get("processed_data_dir", "data/processed")

downloader = BinanceDownloader(raw_dir)
processor = DataProcessor(raw_dir, processed_dir)

# Download and load data
downloader.download_funding_rates(symbol, start_date, end_date)

datasets = {}
for tf in ["5m", "15m", "1h"]:
    downloader.download_candles(symbol, tf, start_date, end_date)
    df_processed = processor.process_and_align(symbol, tf)
    df_enriched = add_indicators(df_processed)
    datasets[tf] = df_enriched

# Align
df_tf = processor.align_multitimeframe_data(
    datasets["5m"],
    datasets["15m"],
    datasets["1h"]
)

# Engines
engine = BacktestEngine(
    initial_capital=costs_cfg.get("initial_capital", 10000.0),
    maker_fee=costs_cfg.get("maker_fee", 0.0002),
    taker_fee=costs_cfg.get("taker_fee", 0.0005),
    slippage=costs_cfg.get("slippage", 0.0005)
)

multi_engine = MultiPositionBacktestEngine(
    initial_capital=costs_cfg.get("initial_capital", 10000.0),
    maker_fee=costs_cfg.get("maker_fee", 0.0002),
    taker_fee=costs_cfg.get("taker_fee", 0.0005),
    slippage=costs_cfg.get("slippage", 0.0005),
    max_positions=3,
    cooldown_candles=5
)

# Baseline configs
p4_strat_1_cfg = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": "ema_200",
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 2.5,
    "sl_atr_mult": 1.8,
    "rsi_overbought": 75,
    "rsi_oversold": 30,
    "adx_thresh": 20,
    "wick_ratio_thresh": 0.45
}
p4_strat_2_cfg = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "atr_volatility_expansion",
    "trend_filter": None,
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 2.5,
    "sl_atr_mult": 1.5,
    "rsi_overbought": 75,
    "rsi_oversold": 30,
    "adx_thresh": 20,
    "wick_ratio_thresh": 0.45
}
p5_best_single_cfg = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "strict",
    "tp_atr_mult": 2.5,
    "sl_atr_mult": 1.8,
    "rsi_overbought": 75,
    "rsi_oversold": 30,
    "adx_thresh": 20,
    "wick_ratio_thresh": 0.45
}
rebuilt_filler_cfg = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "low_activity_filler",
    "trend_filter": "ema_200",
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 3.5,
    "sl_atr_mult": 2.0,
    "rsi_overbought": 75,
    "rsi_oversold": 25,
    "adx_thresh": 20,
    "wick_ratio_thresh": 0.45
}
p6_strat_3_cfg = {
    "strategy_class": "UniversalStrategyTemplate",
    "template_type": "bollinger_expansion_breakout",
    "trend_filter": None,
    "regime_filter_mode": "no_filter",
    "tp_atr_mult": 2.5,
    "sl_atr_mult": 1.8,
    "rsi_overbought": 75,
    "rsi_oversold": 30,
    "adx_thresh": 20,
    "wick_ratio_thresh": 0.45
}

# 1. Evaluate on datasets["1h"]
print("=== RUNNING ON 1H DATA ===")
res_b_1h = engine.run(datasets["1h"], UniversalStrategyTemplate(p5_best_single_cfg))
res_c_1h = engine.run(datasets["1h"], UniversalStrategyTemplate(rebuilt_filler_cfg))

portfolio_1h = PortfolioStrategy([
    UniversalStrategyTemplate(p5_best_single_cfg),
    UniversalStrategyTemplate(p4_strat_1_cfg),
    UniversalStrategyTemplate(p6_strat_3_cfg)
], conflict_rule="cancel")
res_a_1h = multi_engine.run(datasets["1h"], portfolio_1h, {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0})

print(f"Baseline B (Best Single) 1H PnL: ${res_b_1h['metrics']['net_pnl']:.2f} | Trades: {res_b_1h['metrics']['total_trades']} | Max DD: {res_b_1h['metrics']['max_drawdown']*100:.2f}%")
print(f"Baseline C (Filler) 1H PnL: ${res_c_1h['metrics']['net_pnl']:.2f} | Trades: {res_c_1h['metrics']['total_trades']} | Max DD: {res_c_1h['metrics']['max_drawdown']*100:.2f}%")
print(f"Baseline A (Portfolio) 1H PnL: ${res_a_1h['metrics']['net_pnl']:.2f} | Trades: {res_a_1h['metrics']['total_trades']} | Max DD: {res_a_1h['metrics']['max_drawdown']*100:.2f}%")

# 2. Evaluate on df_tf (5m aligned data)
print("\n=== RUNNING ON 5M ALIGNED DATA ===")
res_b_5m = engine.run(df_tf, UniversalStrategyTemplate(p5_best_single_cfg))
res_c_5m = engine.run(df_tf, UniversalStrategyTemplate(rebuilt_filler_cfg))
res_a_5m = multi_engine.run(df_tf, PortfolioStrategy([
    UniversalStrategyTemplate(p5_best_single_cfg),
    UniversalStrategyTemplate(p4_strat_1_cfg),
    UniversalStrategyTemplate(p6_strat_3_cfg)
], conflict_rule="cancel"), {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0})

print(f"Baseline B (Best Single) 5M PnL: ${res_b_5m['metrics']['net_pnl']:.2f} | Trades: {res_b_5m['metrics']['total_trades']} | Max DD: {res_b_5m['metrics']['max_drawdown']*100:.2f}%")
print(f"Baseline C (Filler) 5M PnL: ${res_c_5m['metrics']['net_pnl']:.2f} | Trades: {res_c_5m['metrics']['total_trades']} | Max DD: {res_c_5m['metrics']['max_drawdown']*100:.2f}%")
print(f"Baseline A (Portfolio) 5M PnL: ${res_a_5m['metrics']['net_pnl']:.2f} | Trades: {res_a_5m['metrics']['total_trades']} | Max DD: {res_a_5m['metrics']['max_drawdown']*100:.2f}%")
