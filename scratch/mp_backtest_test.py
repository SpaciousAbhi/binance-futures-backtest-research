import os
import sys
import time
import multiprocessing
import json
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators
from src.backtest.engine import MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate

df_global = None
engine_global = None
base_risk = None

def init_worker(csv_path):
    global df_global, engine_global, base_risk
    df_raw = pd.read_csv(csv_path)
    df_global = add_indicators(df_raw)
    
    settings  = {"initial_capital": 10000.0, "maker_fee": 0.0002, "taker_fee": 0.0005,
                 "slippage": 0.0005, "max_positions": 1, "cooldown_candles": 5}
    engine_global = MultiPositionBacktestEngine(**settings)
    base_risk = {"risk_limit_pct": 1.0, "monthly_risk_limit": 0.025,
                 "risk_throttle_mode": "no_throttle", "emergency_pause_threshold": 0.025}

def test_worker(params_json):
    global df_global, engine_global, base_risk
    try:
        params = json.loads(params_json)
        strat = UniversalStrategyTemplate(params)
        res = engine_global.run(df_global, strat, base_risk)
        trades = res.get("trades")
        n = len(trades) if trades is not None and not trades.empty else 0
        return n
    except Exception as e:
        return str(e)

def main():
    csv_path = os.path.join(_ROOT, "data/processed/BTCUSDT_1h_processed.csv")
    
    # 50 duplicate configurations for timing
    params = {
        "template_type": "bollinger_expansion_breakout",
        "regime_filter_mode": "strict",
        "tp_atr_mult": 2.5,
        "sl_atr_mult": 1.8,
        "bb_width_thresh": 0.06,
        "adx_thresh": 20,
        "expected_r_threshold": 1.40,
        "trend_filter": None,
        "rsi_overbought": 100,
        "rsi_oversold": 0,
        "wick_ratio_thresh": 0.45,
    }
    params_json = json.dumps(params)
    tasks = [params_json] * 50

    t0 = time.time()
    with multiprocessing.Pool(processes=os.cpu_count(), initializer=init_worker, initargs=(csv_path,)) as pool:
        results = pool.map(test_worker, tasks)
    print("Results count:", len(results))
    print("Sample results:", results[:5])
    print(f"Time taken for 50 backtests: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
