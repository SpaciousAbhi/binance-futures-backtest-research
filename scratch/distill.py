import os
import json
import yaml
import pandas as pd
import numpy as np

from src.data.processor import DataProcessor
from src.features.indicators import add_indicators
from src.backtest.engine import BacktestEngine, MultiPositionBacktestEngine
from src.strategies.candidates import UniversalStrategyTemplate
from src.strategies.portfolio import PortfolioStrategy

def main():
    print("=== Phase 1: Load and Enrich Data ===")
    project_cfg = yaml.safe_load(open("configs/project.yaml"))
    costs_cfg = yaml.safe_load(open("configs/costs.yaml"))

    symbol = project_cfg.get("symbol", "BTCUSDT")
    timeframe = "1h"
    raw_dir = project_cfg.get("raw_data_dir", "data/raw")
    processed_dir = project_cfg.get("processed_data_dir", "data/processed")

    # Load and enrich data using project libraries
    processor = DataProcessor(raw_dir, processed_dir)
    df_processed = processor.process_and_align(symbol, timeframe)
    df_enriched = add_indicators(df_processed)
    print(f"Data loaded: {len(df_enriched)} rows.")

    open_time_to_idx = {t: idx for idx, t in enumerate(df_enriched["open_time"].values)}
    highs_arr = df_enriched["high"].values
    lows_arr = df_enriched["low"].values

    print("\n=== Phase 2: Load Strategy Configurations ===")
    # Read top 3 configurations from search_checkpoint.json
    with open("reports/search_checkpoint.json", "r") as f:
        checkpoint = json.load(f)
    leaderboard = checkpoint["leaderboard"]
    top_3_configs = [x["config"] for x in leaderboard[:3]]
    
    print("Candidate B (Leaderboard Top 3) Configs:")
    for idx, cfg in enumerate(top_3_configs):
        print(f"  Config {idx+1}: {cfg['template_type']} | rsi: {cfg.get('rsi_overbought')}/{cfg.get('rsi_oversold')} | strict: {cfg.get('regime_filter_mode')}")

    # Standard candidate configurations
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

    # Engines setup
    initial_cap = costs_cfg.get("initial_capital", 10000.0)
    maker = costs_cfg.get("maker_fee", 0.0002)
    taker = costs_cfg.get("taker_fee", 0.0005)
    slip = costs_cfg.get("slippage", 0.0005)

    engine_single = BacktestEngine(initial_cap, maker, taker, slip)
    engine_multi = MultiPositionBacktestEngine(initial_cap, maker, taker, slip, max_positions=3, cooldown_candles=5)

    print("\n=== Phase 3: Run Candidate Backtests ===")
    
    # Candidate A: Portfolio of p5_best_single_cfg, p4_strat_1_cfg, p6_strat_3_cfg
    portfolio_a = PortfolioStrategy([
        UniversalStrategyTemplate(p5_best_single_cfg),
        UniversalStrategyTemplate(p4_strat_1_cfg),
        UniversalStrategyTemplate(p6_strat_3_cfg)
    ], conflict_rule="cancel")
    print("Running Candidate A...")
    res_a = engine_multi.run(df_enriched, portfolio_a, {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0})

    # Candidate B: Portfolio of top 3 configs from search_checkpoint.json
    portfolio_b = PortfolioStrategy([
        UniversalStrategyTemplate(cfg) for cfg in top_3_configs
    ], conflict_rule="cancel")
    print("Running Candidate B...")
    res_b = engine_multi.run(df_enriched, portfolio_b, {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0})

    # Candidate C: Single strategy of p5_best_single_cfg
    strat_c = UniversalStrategyTemplate(p5_best_single_cfg)
    print("Running Candidate C...")
    res_c = engine_single.run(df_enriched, strat_c)

    # Candidate D: Single strategy of rebuilt_filler_cfg
    strat_d = UniversalStrategyTemplate(rebuilt_filler_cfg)
    print("Running Candidate D...")
    res_d = engine_single.run(df_enriched, strat_d)

    # Candidate E: Portfolio Candidate A run under MultiPositionBacktestEngine with delay_candles=1
    print("Running Candidate E...")
    res_e = engine_multi.run(df_enriched, portfolio_a, {"monthly_risk_limit": 0.025, "risk_limit_pct": 1.0, "delay_candles": 1})

    print("\n=== Phase 4: Post-Process and Extract Metrics ===")
    def post_process_trades(trades_df):
        if trades_df.empty:
            return trades_df
        trades_df = trades_df.copy()
        
        mfes = []
        maes = []
        for idx, row in trades_df.iterrows():
            entry_idx = open_time_to_idx[row["entry_time"]]
            exit_idx = open_time_to_idx[row["exit_time"]]
            entry_price = row["entry_price"]
            side = row["side"]
            
            # Slice highs and lows
            trade_highs = highs_arr[entry_idx : exit_idx + 1]
            trade_lows = lows_arr[entry_idx : exit_idx + 1]
            
            if side == "Long":
                mfe = (trade_highs.max() - entry_price) / entry_price
                mae = (entry_price - trade_lows.min()) / entry_price
            else:
                mfe = (entry_price - trade_lows.min()) / entry_price
                mae = (trade_highs.max() - entry_price) / entry_price
                
            mfes.append(float(mfe))
            maes.append(float(mae))
            
        trades_df["MFE"] = mfes
        trades_df["MAE"] = maes
        return trades_df

    trades_a = post_process_trades(res_a["trades"])
    trades_b = post_process_trades(res_b["trades"])
    trades_c = post_process_trades(res_c["trades"])
    trades_d = post_process_trades(res_d["trades"])
    trades_e = post_process_trades(res_e["trades"])

    trades_dict = {
        "Candidate A": trades_a,
        "Candidate B": trades_b,
        "Candidate C": trades_c,
        "Candidate D": trades_d,
        "Candidate E": trades_e
    }

    def compute_metrics(t_df):
        if t_df.empty:
            return {
                "trade_count": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_winner": 0.0,
                "avg_loser": 0.0,
                "avg_hold_time": 0.0,
                "max_mfe": 0.0,
                "max_mae": 0.0
            }
        wins = t_df[t_df["net_pnl"] > 0]
        losses = t_df[t_df["net_pnl"] <= 0]
        
        trade_count = len(t_df)
        win_rate = len(wins) / trade_count
        
        gross_wins = wins["net_pnl"].sum()
        gross_losses = abs(losses["net_pnl"].sum())
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else (gross_wins if gross_wins > 0 else 1.0)
        
        avg_winner = wins["net_pnl"].mean() if not wins.empty else 0.0
        avg_loser = losses["net_pnl"].mean() if not losses.empty else 0.0
        avg_hold = t_df["hold_candles"].mean()
        max_mfe = t_df["MFE"].max()
        max_mae = t_df["MAE"].max()
        
        return {
            "trade_count": int(trade_count),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "avg_winner": float(avg_winner),
            "avg_loser": float(avg_loser),
            "avg_hold_time": float(avg_hold),
            "max_mfe": float(max_mfe),
            "max_mae": float(max_mae)
        }

    metrics_dict = {}
    for name, t_df in trades_dict.items():
        metrics_dict[name] = compute_metrics(t_df)
        print(f"Metrics for {name}:")
        print(json.dumps(metrics_dict[name], indent=2))

    print("\n=== Phase 5: Compute Matrices ===")
    candidates = ["Candidate A", "Candidate B", "Candidate C", "Candidate D", "Candidate E"]

    # 1. Trade-overlap matrix
    trade_overlap_matrix = {}
    for c1 in candidates:
        trade_overlap_matrix[c1] = {}
        t1 = trades_dict[c1]
        entries_1 = set(t1["entry_time"].values) if not t1.empty else set()
        for c2 in candidates:
            t2 = trades_dict[c2]
            entries_2 = set(t2["entry_time"].values) if not t2.empty else set()
            
            intersection = entries_1.intersection(entries_2)
            union = entries_1.union(entries_2)
            
            jaccard_pct = (len(intersection) / len(union) * 100.0) if len(union) > 0 else 0.0
            overlap_pct = (len(intersection) / len(entries_1) * 100.0) if len(entries_1) > 0 else 0.0
            
            trade_overlap_matrix[c1][c2] = {
                "shared_trades": int(len(intersection)),
                "union_trades": int(len(union)),
                "overlap_pct": float(overlap_pct),
                "jaccard_pct": float(jaccard_pct)
            }

    # 2. Monthly complement matrix
    monthly_pnl_dict = {
        "Candidate A": res_a["metrics"]["monthly_pnl"],
        "Candidate B": res_b["metrics"]["monthly_pnl"],
        "Candidate C": res_c["metrics"]["monthly_pnl"],
        "Candidate D": res_d["metrics"]["monthly_pnl"],
        "Candidate E": res_e["metrics"]["monthly_pnl"]
    }
    
    monthly_complement_matrix = {}
    for c1 in candidates:
        monthly_complement_matrix[c1] = {}
        c1_pnl = monthly_pnl_dict[c1]
        # Identify bad months (net PnL <= 0)
        bad_months = [m for m, pnl in c1_pnl.items() if pnl <= 0.0]
        
        for c2 in candidates:
            c2_pnl = monthly_pnl_dict[c2]
            c2_bad_pnl = sum(c2_pnl.get(m, 0.0) for m in bad_months)
            
            monthly_complement_matrix[c1][c2] = {
                "bad_months_count": int(len(bad_months)),
                "bad_months": bad_months,
                "net_pnl": float(c2_bad_pnl)
            }

    # 3. Regime complement matrix
    regime_cols = [
        "regime_bull_trend",
        "regime_bear_trend",
        "regime_sideways_range",
        "regime_vol_compression",
        "regime_vol_expansion",
        "regime_funding_extreme",
        "regime_toxic_chop"
    ]
    
    regime_complement_matrix = {}
    for c in candidates:
        t_df = trades_dict[c]
        regime_complement_matrix[c] = {}
        for r_col in regime_cols:
            if t_df.empty:
                regime_complement_matrix[c][r_col] = {
                    "net_pnl": 0.0,
                    "trade_count": 0
                }
                continue
                
            entry_indices = [open_time_to_idx[t] for t in t_df["entry_time"]]
            is_regime_active = df_enriched[r_col].values[entry_indices]
            matching_trades = t_df[is_regime_active]
            
            regime_complement_matrix[c][r_col] = {
                "net_pnl": float(matching_trades["net_pnl"].sum()),
                "trade_count": int(len(matching_trades))
            }

    print("\n=== Phase 6: Save Output JSON ===")
    output_data = {
        "metrics": metrics_dict,
        "trade_overlap_matrix": trade_overlap_matrix,
        "monthly_complement_matrix": monthly_complement_matrix,
        "regime_complement_matrix": regime_complement_matrix
    }

    output_path = r"reports/distillation_matrices.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=4)
    print(f"Results written to {output_path}")

    print("\n=== Phase 7: Print Markdown Tables ===")
    print("\n### 1. Candidate Performance Summary Table")
    print("| Candidate | Trade Count | Win Rate | Profit Factor | Avg Winner ($) | Avg Loser ($) | Avg Hold (candles) | Max MFE | Max MAE |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in candidates:
        m = metrics_dict[c]
        print(f"| {c} | {m['trade_count']} | {m['win_rate']:.2%} | {m['profit_factor']:.2f} | {m['avg_winner']:.2f} | {m['avg_loser']:.2f} | {m['avg_hold_time']:.1f} | {m['max_mfe']:.2%} | {m['max_mae']:.2%} |")

    print("\n### 2. Trade Overlap Matrix (% of Row's trades entering at same timestamp as Column)")
    print("| Candidate (Row) | Candidate A | Candidate B | Candidate C | Candidate D | Candidate E |")
    print("|---|---|---|---|---|---|")
    for c1 in candidates:
        row_str = f"| {c1} "
        for c2 in candidates:
            row_str += f"| {trade_overlap_matrix[c1][c2]['overlap_pct']:.2f}% "
        row_str += "|"
        print(row_str)

    print("\n### 3. Monthly Complement Matrix (Column PnL during Row's losing/zero months)")
    print("| Candidate (Row) | Losing/Zero Months | Candidate A | Candidate B | Candidate C | Candidate D | Candidate E |")
    print("|---|---|---|---|---|---|---|")
    for c1 in candidates:
        row_str = f"| {c1} | {monthly_complement_matrix[c1][c1]['bad_months_count']} "
        for c2 in candidates:
            row_str += f"| ${monthly_complement_matrix[c1][c2]['net_pnl']:.2f} "
        row_str += "|"
        print(row_str)

    print("\n### 4. Regime Complement Matrix (Net PnL / Trade Count per Regime)")
    regime_headers = " | ".join(regime_cols)
    print(f"| Candidate | {regime_headers} |")
    print("|---|" + "---|"*len(regime_cols))
    for c in candidates:
        row_str = f"| {c} "
        for r in regime_cols:
            r_data = regime_complement_matrix[c][r]
            row_str += f"| ${r_data['net_pnl']:.2f} ({r_data['trade_count']}) "
        row_str += "|"
        print(row_str)

if __name__ == "__main__":
    main()
