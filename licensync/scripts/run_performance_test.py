#!/usr/bin/env python3
# In licensync/scripts/run_performance_test.py

import time
import os
import subprocess
import pandas as pd

# --- Configuration ---
REPO_URL = "https://github.com/pallets/flask.git"
REPO_NAME = "flask"

def benchmark_licensync():
    """Measures the runtime of the LicenSync coverage experiment script."""
    print("--- Benchmarking LicenSync ---")
    start_time = time.time()
    
    # We run the full coverage experiment as a representative workload
    command = [
        "python3", "-m", "licensync.scripts.run_coverage_experiment"
    ]
    # Use subprocess.run to execute the command
    subprocess.run(command, capture_output=True, text=True)
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"  -> LicenSync finished in {duration:.2f} seconds.")
    return duration

def benchmark_scancode():
    """Measures the runtime of a full Scancode scan."""
    print("\\n--- Benchmarking Scancode ---")
    
    # 1. Clone the repo if it doesn't exist
    if not os.path.exists(REPO_NAME):
        print(f"  -> Cloning {REPO_NAME}...")
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL])
    
    # 2. Run the scan and time it
    start_time = time.time()
    command = [
        "scancode", "-pl", "--json-pp", f"scancode-{REPO_NAME}.json", REPO_NAME
    ]
    subprocess.run(command, capture_output=True, text=True)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"  -> Scancode finished in {duration:.2f} seconds.")
    
    # 3. Clean up
    os.remove(f"scancode-{REPO_NAME}.json")
    subprocess.run(["rm", "-rf", REPO_NAME])
    
    return duration

if __name__ == "__main__":
    licensync_time = benchmark_licensync()
    scancode_time = benchmark_scancode()
    
    # Generate and print the final report table
    report_df = pd.DataFrame([
        {"Tool": "LicenSync", "Runtime (seconds)": f"{licensync_time:.2f}"},
        {"Tool": "Scancode", "Runtime (seconds)": f"{scancode_time:.2f}"},
    ])
    
    print("\\n--- Performance Benchmark Report ---")
    print(f"Results based on analyzing the '{REPO_NAME}' repository.\\n")
    print(report_df.to_markdown(index=False))