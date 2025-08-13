#!/usr/bin/env python3

"""
Fetch SPDX license info from ClearlyDefined for a list of package coordinates and
write a flat CSV you can merge into your pipeline.

Inputs (choose one):
  --from-spdx-csv baselines/node_licenses_syft.csv  # columns: repo,package,license,source
  --from-edges    licensync/data/edges/*.csv        # columns: repo,parent,child,lic_parent,lic_child,version?

We try to infer ClearlyDefined "coordinates" from names:
  PyPI  -> pypi/pypi/-/<name>/<version>
  npm   -> npm/npmjs/-/<name>/<version>
  GitHub repositories (root) -> git/github/<owner>/<repo>/<sha|version>

Tips:
- Provide versions where possible (from SBOMs or edges). If absent, we query without version and
  accept declared/concluded license at the component level (less precise).
- Results are cached under cache/clearlydefined/*.json to avoid re-fetching.

Usage examples:
  python3 scripts/enrich/clearlydefined_fetch.py --from-spdx-csv baselines/node_licenses_syft.csv --out baselines/clearlydefined_licenses.csv
  python3 scripts/enrich/clearlydefined_fetch.py --from-edges licensync/data/edges --out baselines/clearlydefined_licenses.csv
"""

import argparse, csv, os, re, sys, time, json
from pathlib import Path
from typing import Dict, Tuple, Optional, Iterable
try:
    # Python 3.11+
    import urllib.request as ul
    import urllib.error as ue
except Exception:
    import urllib as ul
    ue = ul

CACHE_DIR = Path("cache/clearlydefined")

CD_BASE = "https://api.clearlydefined.io/definitions"

def ensure_cache():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cd_url(coord: str) -> str:
    return f"{CD_BASE}/{coord}"

def http_get(url: str, timeout=20) -> Optional[dict]:
    try:
        with ul.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None

def cache_path(coord: str) -> Path:
    safe = coord.replace("/", "_")
    return CACHE_DIR / f"{safe}.json"

def load_cached(coord: str) -> Optional[dict]:
    p = cache_path(coord)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None

def save_cached(coord: str, data: dict):
    p = cache_path(coord)
    try:
        p.write_text(json.dumps(data))
    except Exception:
        pass

def guess_ecosystem(name: str) -> str:
    # Heuristics: scoped names -> npm, hyphenated lowercase -> npm, otherwise pypi fallback
    if "/" in name or name.startswith("@"):
        return "npm"
    # simple rule-of-thumb: many PyPI packages are all-lowercase with dashes/underscores
    return "pypi"

def to_coord(name: str, version: Optional[str]=None, repo: Optional[str]=None) -> Optional[str]:
    name = (name or "").strip()
    if not name:
        return None
    # GitHub repos: owner/repo
    if repo and "/" in repo and repo.count("/") == 1:
        owner, r = repo.split("/", 1)
        # If a SHA-like is available in version, use it; else leave empty (less precise)
        ver = (version or "").strip()
        if ver and len(ver) >= 7:
            return f"git/github/{owner}/{r}/{ver}"
        return f"git/github/{owner}/{r}"
    eco = guess_ecosystem(name)
    if eco == "npm":
        if version:
            return f"npm/npmjs/-/{name}/{version}"
        return f"npm/npmjs/-/{name}"
    else:
        # pypi
        if version:
            return f"pypi/pypi/-/{name}/{version}"
        return f"pypi/pypi/-/{name}"

def pick_license(doc: dict) -> str:
    if not isinstance(doc, dict):
        return ""
    # Prefer concluded or declared SPDX expression
    lic = (doc.get("licensed", {}) or {}).get("concluded") \
          or (doc.get("licensed", {}) or {}).get("declared") \
          or ""
    if lic:
        return lic
    # Fall back to discovered in core facet
    try:
        facets = doc.get("licensed", {}).get("facets", {})
        core = facets.get("core", {})
        discovered = core.get("discovered", [])
        if discovered:
            # collect the ids; join with OR
            ids = [d.get("license", "") for d in discovered if d.get("license")]
            ids = [i for i in ids if i]
            if ids:
                return " OR ".join(sorted(set(ids)))
    except Exception:
        pass
    return ""

def iter_spdx_csv(path: Path):
    # Expect columns: repo, package, license, (optional version, source)
    import csv
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            pkg = (row.get("package") or "").strip()
            ver = (row.get("version") or "").strip()
            repo = (row.get("repo") or "").strip()
            yield repo, pkg, ver

def iter_edges_dir(path: Path):
    for f in path.glob("*.csv"):
        with open(f) as h:
            r = csv.DictReader(h)
            for row in r:
                repo = (row.get("repo") or "").strip()
                # Try both parent and child as packages (child is more likely a package)
                child = (row.get("child") or "").strip()
                ver = (row.get("version") or "").strip()
                if child:
                    yield repo, child, ver

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-spdx-csv", help="CSV from SPDX aligner (package->license)")
    ap.add_argument("--from-edges", help="Directory with edge CSVs")
    ap.add_argument("--out", default="baselines/clearlydefined_licenses.csv")
    ap.add_argument("--sleep", type=float, default=0.3, help="Sleep seconds between requests (politeness)")
    args = ap.parse_args()

    ensure_cache()

    it = []
    if args.from_spdx_csv:
        it = iter_spdx_csv(Path(args.from_spdx_csv))
    elif args.from_edges:
        it = iter_edges_dir(Path(args.from_edges))
    else:
        print("[fatal] provide --from-spdx-csv or --from-edges", file=sys.stderr)
        sys.exit(2)

    seen = set()
    rows = []
    for repo, pkg, ver in it:
        coord = to_coord(pkg, ver, repo=repo)
        if not coord or coord in seen:
            continue
        seen.add(coord)
        doc = load_cached(coord)
        if doc is None:
            url = cd_url(coord)
            doc = http_get(url)
            if doc:
                save_cached(coord, doc)
            time.sleep(args.sleep)
        lic = pick_license(doc) if doc else ""
        rows.append(dict(coord=coord, repo=repo, package=pkg, version=ver, license=lic))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["coord","repo","package","version","license"])
        w.writeheader(); w.writerows(rows)
    print(f"[ok] wrote {len(rows)} rows to {args.out}")

if __name__ == "__main__":
    main()
