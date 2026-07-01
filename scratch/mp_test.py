import os
import sys
import time
import multiprocessing

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, _ROOT)

from src.features.indicators import add_indicators

def test_worker(arg):
    pid = os.getpid()
    return f"arg={arg} pid={pid}"

def main():
    print(f"Cores: {os.cpu_count()}")
    t0 = time.time()
    with multiprocessing.Pool(processes=os.cpu_count()) as pool:
        results = pool.map(test_worker, list(range(50)))
    print("Results count:", len(results))
    print(f"Time taken: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
