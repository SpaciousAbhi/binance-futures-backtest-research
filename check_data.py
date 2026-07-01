import pandas as pd
for fn in ['data/raw/BTCUSDT_5m_raw.csv', 'data/raw/BTCUSDT_15m_raw.csv', 'data/raw/BTCUSDT_1h_raw.csv', 'data/raw/BTCUSDT_funding_raw.csv']:
    df = pd.read_csv(fn)
    time_col = 'open_time' if 'open_time' in df.columns else 'fundingTime'
    max_val = df[time_col].max()
    print(f'{fn}: {max_val} ({pd.to_datetime(max_val, unit="ms", utc=True)})')
