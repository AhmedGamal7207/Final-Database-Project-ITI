import time
import subprocess
import sys
import os
import shutil
import random
import requests
from src.client.client import DatabaseClient

DB_PORT = 8005
DATA_DIR = "benchmark_data"

def run_benchmark():
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
    os.makedirs(DATA_DIR)

    print("Starting DB Server for Benchmark...")
    env = os.environ.copy()
    env["DB_DATA_DIR"] = DATA_DIR
    proc = subprocess.Popen(
        [sys.executable, "main.py", "--port", str(DB_PORT)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)

    client = DatabaseClient(port=DB_PORT)
    
    counts = [100, 1000, 5000]
    
    try:
        print(f"{'Count':<10} | {'Mode':<10} | {'Time (s)':<10} | {'Ops/sec':<10}")
        print("-" * 50)
        
        # Sequential Set
        for n in counts:
            start_time = time.time()
            for i in range(n):
                client.set(f"key_{n}_{i}", f"val_{i}")
            duration = time.time() - start_time
            print(f"{n:<10} | {'SEQ SET':<10} | {duration:<10.4f} | {n/duration:<10.2f}")

        # Bulk Set
        for n in counts:
            items = [(f"blk_{n}_{i}", f"val_{i}") for i in range(n)]
            start_time = time.time()
            client.bulk_set(items)
            duration = time.time() - start_time
            print(f"{n:<10} | {'BULK SET':<10} | {duration:<10.4f} | {n/duration:<10.2f}")

    finally:
        proc.terminate()
        proc.wait()
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)

if __name__ == "__main__":
    run_benchmark()
