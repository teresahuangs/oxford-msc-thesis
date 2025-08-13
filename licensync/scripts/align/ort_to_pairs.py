#!/usr/bin/env python3
import argparse, yaml, csv
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Approximate (parent, child, ok) pairs from ORT evaluation")
    ap.add_argument("--ort-dir", required=True, help="Root folder with per-repo ORT outputs")
    ap.add_argument("--out", default="licensync/data/baselines/ort_pairs.csv")
    args = ap.parse_args()

    rows = []
    root = Path(args.ort_dir)
    for repo_dir in sorted(root.iterdir()):
        if not repo_dir.is_dir(): continue
        eval_yml = repo_dir / "evaluation-result.yml"
        scan_yml = repo_dir / "scan-result.yml"
        if not eval_yml.exists() or not scan_yml.exists():
            continue
        # Load scan result to get effective licenses per package
        scan = yaml.safe_load(scan_yml.read_text())
        packages = {}
        for p in scan.get("packages", []):
            id_ = p.get("id","")
            lic = ""
            try:
                # ORT summarizes effective license under "vcs_processed"/"declared_licenses_processed" etc.
                lic = (p.get("concluded_license") 
                       or (p.get("declared_licenses_processed",{}).get("spdx_expression")) 
                       or "")
            except Exception:
                pass
            packages[id_] = lic

        # Use the first project as parent; map all packages as children
        projects = scan.get("projects", [])
        parent_lic = ""
        if projects:
            pr = projects[0]
            parent_lic = (pr.get("concluded_license") 
                          or (pr.get("declared_licenses_processed",{}).get("spdx_expression")) 
                          or "")
        # Approximate: if evaluation has any ERROR on a package, mark ok=False for that child.
        evaldoc = yaml.safe_load(eval_yml.read_text())
        violated = set()
        for r in evaldoc.get("rules", []):
            if r.get("severity","").upper() == "ERROR":
                for loc in r.get("rule_violations", []):
                    id_ = loc.get("pkg","") or loc.get("id","")
                    if id_: violated.add(id_)

        repo_name = repo_dir.name
        for id_, child_lic in packages.items():
            if not child_lic: continue
            ok = id_ not in violated
            rows.append({
                "repo": repo_name,
                "parent": repo_name,
                "child": id_,
                "lic_parent": parent_lic or "NOASSERTION",
                "lic_child": child_lic or "NOASSERTION",
                "ok": 1 if ok else 0
            })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["repo","parent","child","lic_parent","lic_child","ok"])
        w.writeheader(); w.writerows(rows)
    print(f"[ok] wrote {len(rows)} rows to {args.out}")

if __name__ == "__main__":
    main()
