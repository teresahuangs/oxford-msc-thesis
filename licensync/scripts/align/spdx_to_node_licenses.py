#!/usr/bin/env python3
import json, argparse, csv, os
from pathlib import Path

def extract_packages(spdx_json):
    pkgs = []
    for p in spdx_json.get("packages", []):
        name = p.get("name") or p.get("PackageName") or ""
        # prefer concluded then declared
        lic = p.get("licenseConcluded") or p.get("concludedLicense") or p.get("licenseDeclared") or p.get("declaredLicense") or ""
        pkgs.append((name, lic))
    return pkgs

def main():
    ap = argparse.ArgumentParser(description="Extract (package, license) from SPDX JSON files")
    ap.add_argument("--in-dir", required=True, help="Directory with *.spdx.json files")
    ap.add_argument("--out", default="baselines/node_licenses_spdx.csv")
    args = ap.parse_args()

    rows = []
    for f in sorted(Path(args.in_dir).glob("*.spdx.json")):
        data = json.loads(Path(f).read_text())
        repo = f.stem
        for name, lic in extract_packages(data):
            if not name: continue
            rows.append({"source": Path(args.in_dir).name, "repo": repo, "package": name, "license": lic})

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as out:
        w = csv.DictWriter(out, fieldnames=["source","repo","package","license"])
        w.writeheader(); w.writerows(rows)
    print(f"[ok] wrote {len(rows)} rows to {args.out}")

if __name__ == "__main__":
    main()
