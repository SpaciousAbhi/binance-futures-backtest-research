import os
import sys
import pandas as pd
import pickle
from concurrent.futures import ProcessPoolExecutor

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy, FusionOfFusionsStrategy

def run_in_worker(args):
    s_name, s_cfg, df, strat_bytes, engine_settings, base_risk = args
    strat = pickle.loads(strat_bytes)
    engine = MultiPositionBacktestEngine(**engine_settings)
    res = engine.run(df, strat, base_risk)
    return res["metrics"]["net_pnl"], res["trades"]

def main():
    df = pd.read_csv("data/processed/BTCUSDT_1h_processed.csv")
    df = add_indicators(df)
    
    settings = {
        "initial_capital": 10000.0,
        "maker_fee": 0.0002,
        "taker_fee": 0.0005,
        "slippage": 0.0005,
        "max_positions": 1,
        "cooldown_candles": 5
    }
    base_risk = {
        "risk_limit_pct": 1.0,
        "monthly_risk_limit": 0.025,
        "risk_throttle_mode": "no_throttle",
        "emergency_pause_threshold": 0.025
    }

    CAND_C_CFG = {
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": None, "regime_filter_mode": "strict",
        "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
        "rsi_overbought": 100, "rsi_oversold": 0,
        "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h", "bb_width_thresh": 0.06
    }
    CAND_D_CFG = {
        "template_type": "low_activity_filler",
        "trend_filter": "ema_200", "regime_filter_mode": "no_filter",
        "tp_atr_mult": 3.5, "sl_atr_mult": 2.0,
        "rsi_overbought": 75, "rsi_oversold": 25,
        "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h"
    }
    CAND_F_CFG = {
        "template_type": "atr_volatility_expansion",
        "trend_filter": None, "regime_filter_mode": "strict",
        "tp_atr_mult": 3.0, "sl_atr_mult": 2.0,
        "rsi_overbought": 75, "rsi_oversold": 30,
        "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h"
    }
    CAND_G_CFG = {
        "template_type": "funding_extreme_reversal",
        "trend_filter": None, "regime_filter_mode": "strict",
        "tp_atr_mult": 2.0, "sl_atr_mult": 2.0,
        "rsi_overbought": 75, "rsi_oversold": 30,
        "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h"
    }
    cfg_a = {
        "template_type": "bollinger_expansion_breakout",
        "trend_filter": None, "regime_filter_mode": "no_filter",
        "tp_atr_mult": 2.5, "sl_atr_mult": 1.8,
        "rsi_overbought": 75, "rsi_oversold": 30,
        "adx_thresh": 20, "wick_ratio_thresh": 0.45, "timeframe": "1h", "bb_width_thresh": 0.06
    }

    s_a = UniversalStrategyTemplate(cfg_a)
    s_c = UniversalStrategyTemplate(CAND_C_CFG)
    s_d = UniversalStrategyTemplate(CAND_D_CFG)
    s_f = UniversalStrategyTemplate(CAND_F_CFG)
    s_g = UniversalStrategyTemplate(CAND_G_CFG)

    fusion_quality_core = PortfolioStrategy([s_c, s_f, s_g, s_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
    fusion_activity = PortfolioStrategy([s_a, s_c, s_f], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=False)
    fusion_defensive = PortfolioStrategy([s_c, s_g, s_d], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)
    fusion_zero_rescue = PortfolioStrategy([s_d, s_g], conflict_rule="cancel", fusion_mode="union", zero_month_rescue=True)

    fusions_dict = {
        "quality_core": fusion_quality_core,
        "activity": fusion_activity,
        "defensive": fusion_defensive,
        "zero_rescue": fusion_zero_rescue
    }
    strat_v5_0 = FusionOfFusionsStrategy(fusions_dict, conflict_rule="cancel")

    # Run 1: Sequential
    engine1 = MultiPositionBacktestEngine(**settings)
    res1 = engine1.run(df, strat_v5_0, base_risk)
    trades1 = res1["trades"]

    # Run 2: Parallel
    strat_bytes = pickle.dumps(strat_v5_0)
    args = ("normal", {}, df, strat_bytes, settings, base_risk)
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(run_in_worker, [args]))
    pnl2, trades2 = results[0]

    print(f"Sequential PnL: ${res1['metrics']['net_pnl']:.2f}")
    print(f"Parallel PnL: ${pnl2:.2f}")

    # Compare trades
    for i in range(min(len(trades1), len(trades2))):
        t1 = trades1.iloc[i]
        t2 = trades2.iloc[i]
        if t1["entry_time"] != t2["entry_time"] or abs(t1["net_pnl"] - t2["net_pnl"]) > 1e-4:
            print(f"Divergence at trade {i}:")
            print(f"  Seq: entry_time={t1['entry_time']}, side={t1['side']}, pnl={t1['net_pnl']:.4f}, reason={t1.get('reason','')}")
            print(f"  Par: entry_time={t2['entry_time']}, side={t2['side']}, pnl={t2['net_pnl']:.4f}, reason={t2.get('reason','')}")
            break

if __name__ == "__main__":
    main()
