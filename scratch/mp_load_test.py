import os
import sys
import time
import multiprocessing
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators

df_global = None

def init_worker(csv_path):
    global df_global
    # Load and preprocess indicators once per process
    df_raw = pd.read_csv(csv_path)
    df_global = add_indicators(df_raw)

def test_worker(arg):
    global df_global
    # Verify we can access the global preloaded dataframe
    n_rows = len(df_global) if df_global is not None else 0
    return f"arg={arg} rows={n_rows}"

def main():
    csv_path = os.path.join(_ROOT, "data/processed/BTCUSDT_1h_processed.csv")
    t0 = time.time()
    with multiprocessing.Pool(processes=os.cpu_count(), initializer=init_worker, initargs=(csv_path,)) as pool:
        results = pool.map(test_worker, list(range(200)))
    print("Results sample:", results[:5])
    print(f"Time taken for 200 tasks: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
