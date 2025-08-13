#!/usr/bin/env python3

"""
Apply ClearlyDefined enrichment to fill missing licences in a truth CSV or edge CSVs.

Examples:
  python3 scripts/enrich/apply_enrichment.py \
      --truth licensync/data/edge_truth_filled.csv \
      --cd baselines/clearlydefined_licenses.csv \
      --out licensync/data/edge_truth_enriched.csv

Rules:
- If lic_parent or lic_child is empty/unknown, and we have a mapping for that package,
  fill it with the ClearlyDefined license (SPDX expression).
- We do not overwrite non-empty licences.
"""

import argparse, csv, pandas as pd
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True, help="Path to edge truth CSV")
    ap.add_argument("--cd", required=True, help="CSV produced by clearlydefined_fetch.py")
    ap.add_argument("--out", required=True, help="Output enriched CSV")
    args = ap.parse_args()

    truth = pd.read_csv(args.truth)
    cd = pd.read_csv(args.cd)

    # Build a simple package->license map (most recent wins)
    cd_map = {}
    for _, r in cd.iterrows():
        pkg = str(r.get("package") or "").strip()
        lic = str(r.get("license") or "").strip()
        if pkg and lic:
            cd_map[pkg] = lic

    def fill(val, pkg):
        s = str(val or "").strip().lower()
        if s in ("", "unknown", "none", "noassertion"):
            lic = cd_map.get(pkg, "")
            return lic if lic else val
        return val

    if "parent" in truth.columns and "child" in truth.columns:
        truth["lic_parent"] = [
            fill(v, p) for v, p in zip(truth.get("lic_parent",""), truth.get("parent",""))
        ]
        truth["lic_child"] = [
            fill(v, c) for v, c in zip(truth.get("lic_child",""), truth.get("child",""))
        ]
    else:
        truth["lic_parent"] = truth["lic_parent"].apply(lambda v: fill(v, ""))
        truth["lic_child"] = truth["lic_child"].apply(lambda v: fill(v, ""))

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    truth.to_csv(outp, index=False)
    print(f"[ok] wrote enriched CSV to {outp}")

if __name__ == "__main__":
    main()
