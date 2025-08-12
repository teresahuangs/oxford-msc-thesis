#!/usr/bin/env python3
import argparse, csv, random
from pathlib import Path

def read_edges(edges_dir: Path):
    rows = []
    for f in sorted(edges_dir.glob("*.csv")):
        with f.open() as fh:
            r = csv.DictReader(fh)
            need = {"repo","sha","parent","child","lic_parent","lic_child"}
            if not need.issubset(r.fieldnames or set()):
                print(f"[warn] {f} missing columns {need - set(r.fieldnames or [])}; skipping")
                continue
            for row in r:
                rows.append({
                    "repo": row["repo"],
                    "sha": row.get("sha",""),
                    "parent": row["parent"],
                    "child": row["child"],
                    "lic_parent": row.get("lic_parent","unknown"),
                    "lic_child": row.get("lic_child","unknown"),
                })
    return rows

def dedupe(rows):
    seen, out = set(), []
    for r in rows:
        k = (r["repo"], r["sha"], r["parent"], r["child"])
        if k in seen: 
            continue
        seen.add(k); out.append(r)
    return out

def main():
    ap = argparse.ArgumentParser(description="Prefill data/edge_truth.csv from data/edges/*.csv")
    ap.add_argument("--edges-dir", default="data/edges")
    ap.add_argument("--out", default="data/edge_truth.csv")
    ap.add_argument("--jurisdiction", default="US")
    ap.add_argument("--n", type=int, default=500, help="Sample this many edges total")
    ap.add_argument("--per-repo", type=int, default=0, help="If >0, sample this many edges per repo")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    edges_dir = Path(args.edges_dir)
    if not edges_dir.exists():
        print(f"[error] {edges_dir} not found. Run scripts/build_graph.py first.")
        return

    rows = read_edges(edges_dir)
    if not rows:
        print(f"[error] No usable edge CSVs found in {edges_dir}.")
        return
    rows = dedupe(rows)

    random.seed(args.seed)
    if args.per_repo > 0:
        # bucket by repo
        by_repo = {}
        for r in rows:
            by_repo.setdefault(r["repo"], []).append(r)
        sampled = []
        for repo, lst in by_repo.items():
            k = min(args.per_repo, len(lst))
            sampled.extend(random.sample(lst, k))
    else:
        k = min(args.n, len(rows))
        sampled = random.sample(rows, k)

    # write output with empty label column for you to fill
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["repo","sha","parent","child","lic_parent","lic_child","jurisdiction","label"]
    with out_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in sampled:
            r2 = dict(r)
            r2["jurisdiction"] = args.jurisdiction
            r2["label"] = ""  # fill with: compatible / incompatible
            w.writerow(r2)
    print(f"[ok] Wrote {len(sampled)} rows to {out_path}. Fill the 'label' column before running eval.")
if __name__ == "__main__":
    main()
