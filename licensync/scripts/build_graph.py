#!/usr/bin/env python3
import os, time, csv, json, argparse, sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
import networkx as nx

API_VER = "2022-11-28"

def _headers(token: Optional[str] = None, accept: Optional[str] = None) -> Dict[str, str]:
    h = {
        "Accept": accept or "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VER,
        "User-Agent": "licensync-eval"
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def fetch_sbom(owner_repo: str, token: Optional[str] = None, ref: Optional[str] = None) -> Optional[Dict]:
    url = f"https://api.github.com/repos/{owner_repo}/dependency-graph/sbom"
    if ref:
        url += f"?ref={ref}"
    # Retry a few times in case of 202 (SBOM being generated)
    for i in range(6):
        r = requests.get(url, headers=_headers(token))
        if r.status_code == 200:
            return r.json()
        if r.status_code == 202:
            time.sleep(1.5 * (i+1))
            continue
        # 404 or others -> give up
        return None
    return None

def flatten_sbom(owner_repo: str, sbom: Dict) -> List[Dict]:
    id_to_name: Dict[str, str] = {}
    id_to_license: Dict[str, str] = {}
    for p in sbom.get("sbom", {}).get("packages", []):
        sid = p.get("SPDXID")
        if not sid: 
            continue
        # prefer concluded, then declared
        lic = p.get("licenseConcluded") or p.get("licenseDeclared") or "unknown"
        name = p.get("name") or sid
        id_to_name[sid] = name
        id_to_license[sid] = lic

    edges: List[Dict] = []
    for rel in sbom.get("sbom", {}).get("relationships", []):
        if rel.get("relationshipType") != "DEPENDS_ON":
            continue
        s = rel.get("spdxElementId"); o = rel.get("relatedSpdxElement")
        parent = id_to_name.get(s); child = id_to_name.get(o)
        if not parent or not child:
            continue
        edges.append({"parent": parent, "name": child, "license": id_to_license.get(o, "unknown")})
    return edges

def fetch_text(owner_repo: str, path: str, token: Optional[str]) -> Optional[str]:
    url = f"https://api.github.com/repos/{owner_repo}/contents/{path}"
    r = requests.get(url, headers=_headers(token))
    if r.status_code == 200:
        j = r.json()
        if isinstance(j, dict) and j.get("encoding") == "base64":
            import base64
            return base64.b64decode(j.get("content","")).decode("utf-8", errors="replace")
        # raw text if not encoded
        if isinstance(j, dict) and "content" in j and isinstance(j["content"], str):
            return j["content"]
    return None

def parse_requirements_text(text: str) -> List[Tuple[str, str]]:
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"): 
            continue
        name = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
        if name:
            out.append((name, "unknown"))
    return out

def parse_package_json(text: str) -> List[Tuple[str, str]]:
    try:
        j = json.loads(text)
    except Exception:
        return []
    deps = []
    for key in ("dependencies","devDependencies","peerDependencies","optionalDependencies"):
        for name in (j.get(key) or {}):
            deps.append((name, "unknown"))
    return deps

def build_graph_for_repo(owner_repo: str, sha: Optional[str], token: Optional[str]) -> nx.DiGraph:
    G = nx.DiGraph()
    root = owner_repo
    G.add_node(root, license="unknown", is_root=True)

    # 1) SBOM
    sbom = fetch_sbom(owner_repo, token, ref=sha)
    edges: List[Dict] = []
    if sbom:
        edges = flatten_sbom(owner_repo, sbom)

    # 2) Fallback manifests at repo root
    if not edges:
        # Python
        txt = fetch_text(owner_repo, "requirements.txt", token)
        if txt:
            for n, lic in parse_requirements_text(txt):
                G.add_node(n, license=lic or "unknown", is_root=False)
                G.add_edge(root, n)
        # JS
        pkg = fetch_text(owner_repo, "package.json", token)
        if pkg:
            for n, lic in parse_package_json(pkg):
                G.add_node(n, license=lic or "unknown", is_root=False)
                G.add_edge(root, n)

    # 3) From SBOM relationships (if present)
    for e in edges:
        parent = e.get("parent"); child = e.get("name")
        lic = e.get("license","unknown") or "unknown"
        if parent and not G.has_node(parent):
            G.add_node(parent, license="unknown", is_root=False)
        if child and not G.has_node(child):
            G.add_node(child, license=lic, is_root=False)
        if parent and child:
            G.add_edge(parent, child)

    return G

def write_edges(owner_repo: str, sha: Optional[str], G: nx.DiGraph, outdir: Path):
    edges = []
    for u, v in G.edges():
        edges.append({
            "repo": owner_repo,
            "sha": sha or "",
            "parent": u,
            "child": v,
            "lic_parent": G.nodes[u].get("license","unknown"),
            "lic_child": G.nodes[v].get("license","unknown"),
        })
    # Even if no edges, ensure roots/nodes get stored (helps diagnostics)
    nodes = []
    for n, d in G.nodes(data=True):
        nodes.append({"repo": owner_repo, "sha": sha or "", "name": n, "license": d.get("license","unknown"), "is_root": bool(d.get("is_root"))})

    outdir.mkdir(parents=True, exist_ok=True)
    efile = outdir / f"{owner_repo.replace('/','_')}_{(sha or 'HEAD')}.csv"
    import pandas as pd
    pd.DataFrame(edges).to_csv(efile, index=False)
    nfile = outdir.parent / "nodes" / f"{owner_repo.replace('/','_')}_{(sha or 'HEAD')}.csv"
    pd.DataFrame(nodes).to_csv(nfile, index=False)
    return efile, nfile

def main():
    ap = argparse.ArgumentParser(description="Build dependency graphs (edges) for repos in data/repos.csv")
    ap.add_argument("--repos-file", default="data/repos.csv")
    ap.add_argument("--token", default=os.getenv("GITHUB_TOKEN"))
    ap.add_argument("--outdir", default="data/edges")
    args = ap.parse_args()

    rows = []
    with open(args.repos_file) as f:
        import csv
        r = csv.DictReader(f)
        for row in r:
            if row["repo"].startswith("#") or not row["repo"].strip():
                continue
            rows.append(row)

    all_edges = []
    for row in rows:
        owner_repo = row["repo"].strip()
        sha = (row.get("sha") or "").strip() or None
        print(f"[build] {owner_repo} @ {sha or 'default'}")
        try:
            G = build_graph_for_repo(owner_repo, sha, args.token)
            efile, nfile = write_edges(owner_repo, sha, G, Path(args.outdir))
            print(f"  -> edges: {efile}")
            print(f"  -> nodes: {nfile}")
            for u, v in G.edges():
                all_edges.append([owner_repo, sha or "", u, v])
        except Exception as e:
            print(f"[error] {owner_repo}: {e}")

    # aggregate (for quick sanity)
    if all_edges:
        with open(Path(args.outdir)/"ALL_EDGES.txt","w") as f:
            for r in all_edges:
                f.write("\t".join(r) + "\n")

if __name__ == "__main__":
    main()
