# DATA REGISTRY
## All Data Assets for Binance Futures Backtest Project
## Last Updated: 2026-07-02 (Phase 30)

---

## Processed Data Files (In Git Repository)

These files are committed and available in the GitHub repo.

| Asset | Timeframe | File | Rows | Start | End | SHA-256 (12 chars) | Git Tracked |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 1h | `data/processed/BTCUSDT_1h_processed.csv` | 56,929 | 2020-01-01 | 2026-06-30 | `0d9f63bc016b` | YES |
| BTCUSDT | 15m | `data/processed/BTCUSDT_15m_processed.csv` | 227,521 | 2020-01-01 | 2026-06-28 | (computed) | YES |
| ETHUSDT | 1h | `data/processed/ETHUSDT_1h_processed.csv` | 56,929 | 2020-01-01 | 2026-06-30 | `30db51f322ba` | YES |
| BNBUSDT | 1h | `data/processed/BNBUSDT_1h_processed.csv` | 55,961 | 2020-02-10 | 2026-06-30 | `756cd4158b8a` | YES |
| SOLUSDT | 1h | `data/processed/SOLUSDT_1h_processed.csv` | 50,754 | 2020-09-01 | 2026-06-30 | `a7221ce844fd` | YES |
| BTCUSDT | 5m | `data/processed/BTCUSDT_5m_processed.csv` | 682,561 | 2020-01-01 | 2026-06-28 | (computed) | NO (gitignored) |

---

## Raw Data Files (Local Only — NOT in Git)

These files are in `data/raw/` which is excluded from git by `.gitignore`.

| Asset | Timeframe | File | Git Tracked |
|---|---|---|---|
| BTCUSDT | 5m | `data/raw/BTCUSDT_5m_raw.csv` | NO |
| BTCUSDT | 15m | `data/raw/BTCUSDT_15m_raw.csv` | NO |
| BTCUSDT | 1h | `data/raw/BTCUSDT_1h_raw.csv` | NO |
| BTCUSDT | funding | `data/raw/BTCUSDT_funding_raw.csv` | NO |
| ETHUSDT | 5m/15m/1h | Similar pattern | NO |
| BNBUSDT | 5m/15m/1h | Similar pattern | NO |
| SOLUSDT | 5m/15m/1h | Similar pattern | NO |

---

## Re-Downloading Data

Use the Phase 29 download script:
```bash
python scripts/phase29_download_binance_data.py
```

This downloads BTCUSDT 1h, 15m, 5m + funding from Binance API (2020-01-01 to present).

For multi-asset:
```bash
python src/research/phase27_data_setup.py
```

---

## Data Column Schema (Processed Files)

Every processed CSV must have these columns:

| Column | Description |
|---|---|
| `open_time` | UNIX timestamp (ms) — candle open time |
| `open` | Open price (USDT) |
| `high` | High price (USDT) |
| `low` | Low price (USDT) |
| `close` | Close price (USDT) |
| `volume` | Quote volume (USDT) |
| `close_time` | UNIX timestamp (ms) — candle close time |
| `funding_rate` | Funding rate at this candle (cumulative or snapshot) |
| `atr_14` | 14-period ATR (computed from processed data) |

---

## Data Integrity Requirements

Before using any processed CSV:
1. Verify no duplicate timestamps: `df.open_time.duplicated().any()` must be False.
2. Verify monotonic time: `df.open_time.is_monotonic_increasing` must be True.
3. Verify no NaN in OHLCV: `df[["open","high","low","close"]].isna().any().any()` must be False.
4. Verify gap count is reasonable (some gaps are normal for weekends/low liquidity periods).

Use `src/data/auditor.py` for automated data integrity checks.

---

## Multi-Asset Validation Status

| Asset | Processed 1h Available | Processed 5m Available | Valid Benchmark Run | Last Validated |
|---|---|---|---|---|
| BTCUSDT | YES | YES (local) | NO (PF8.1 was forced) | Phase 29 |
| ETHUSDT | YES | NO | NO | Phase 27 (hardcoded) |
| BNBUSDT | YES | NO | NO | Phase 27 (hardcoded) |
| SOLUSDT | YES | NO | NO | Phase 27 (hardcoded) |

> Phase 27 claimed multi-asset validation but it was hardcoded. No genuine multi-asset
> validation exists. This should be done AFTER a valid BTCUSDT live-executable router is found.

---

## MTF Data Alignment (Phase 29.6 Verification)

Phase 29.6 confirmed the following alignment status:

| Timeframe | Rows | Status | Start | End |
|---|---|---|---|---|
| 1h | 56,929 | PASS | 2020-01-01 | 2026-06-30 |
| 15m | 227,521 | PASS | 2020-01-01 | 2026-06-28 |
| 5m | 682,561 | PASS | 2020-01-01 | 2026-06-28 |

All MTF alignment tests: `setup_close_time < trigger_close_time < entry_time` — PASS.
