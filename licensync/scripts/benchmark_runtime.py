#!/usr/bin/env python3
import argparse, time, csv
from pathlib import Path
from typing import List, Tuple
import pandas as pd

def _import_licensync():
    try:
        from licensync.prolog_interface import evaluate_license_pair  # type: ignore
        return evaluate_license_pair
    except Exception:
        def stub(a,b,c): return True
        return stub

def main():
    ap = argparse.ArgumentParser(description="Benchmark LicenSync evaluator over edges CSVs")
    ap.add_argument("--edges-dir", default="data/edges")
    ap.add_argument("--jurisdiction", default="US")
    ap.add_argument("--out", default="results/perf.json")
    args = ap.parse_args()

    eval_fn = _import_licensync()
    files = sorted(Path(args.edges_dir).glob("*.csv"))
    total_edges = 0
    t0 = time.time()
    for f in files:
        df = pd.read_csv(f)
        for _, row in df.iterrows():
            p = str(row.get("lic_parent","unknown"))
            c = str(row.get("lic_child","unknown"))
            _ = eval_fn(p, c, args.jurisdiction)
            total_edges += 1
    dt = time.time() - t0
    res = {"files": len(files), "edges": total_edges, "seconds": dt, "edges_per_sec": (total_edges/dt if dt>0 else None)}
    print(res)
    Path(args.out).write_text(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
