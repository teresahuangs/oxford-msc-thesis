#!/usr/bin/env python3
import argparse, pandas as pd
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Compare license strings between SPDX sources")
    ap.add_argument("--syft", default="baselines/node_licenses_syft.csv")
    ap.add_argument("--scancode", default="baselines/node_licenses_scancode.csv")
    ap.add_argument("--out", default="baselines/license_compare.csv")
    args = ap.parse_args()

    rows = []
    if Path(args.syft).exists():
        sy = pd.read_csv(args.syft)
    else:
        sy = pd.DataFrame(columns=["repo","package","license","source"])
    if Path(args.scancode).exists():
        sc = pd.read_csv(args.scancode)
    else:
        sc = pd.DataFrame(columns=["repo","package","license","source"])

    merged = sy.merge(sc, on=["repo","package"], how="outer", suffixes=("_syft","_scancode"))
    merged.to_csv(args.out, index=False)
    print(f"[ok] wrote {args.out} with {len(merged)} rows")

if __name__ == "__main__":
    main()
