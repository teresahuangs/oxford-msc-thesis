import json, re, pathlib, subprocess, tempfile, os, requests, networkx as nx
from typing import Dict, Tuple, List, Optional

def _normalise_spdx(raw: str) -> str:
    """Trim extras like ‘(^)’, ‘ ~ ’, semver, etc., then lowercase."""
    return re.sub(r'[^A-Za-z0-9\-.]+', '', raw).lower()

# ─────────────────────────  A. Node.js  ─────────────────────────
def parse_package_lock(lock_path: pathlib.Path) -> List[Tuple[str, str]]:
    """Return [(package, spdx_license)] pairs from a package‑lock.json."""
    data = json.loads(lock_path.read_text())
    deps = []
    for pkg, meta in data.get("packages", {}).items():
        lic = meta.get("license") or meta.get("licenses")
        if isinstance(lic, list): lic = lic[0]
        if lic:
            deps.append((pkg or "root", _normalise_spdx(lic)))
    return deps

# ─────────────────────────  B. Python  ─────────────────────────
def parse_requirements(req_path: pathlib.Path) -> List[Tuple[str, str]]:
    """
    Use pip‑licenses in a temp venv to pull SPDX IDs.
    """
    deps = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ["python3", "-m", "venv", td], check=True, stdout=subprocess.PIPE
        )
        pip = pathlib.Path(td) / "bin" / "pip"
        subprocess.run([pip, "install", "-r", str(req_path)], check=True)
        out = subprocess.check_output(
            [pip, "install", "pip-licenses"], text=True
        )
        out_json = subprocess.check_output(
            [pip, "licenses", "--from=mixed", "--format=json"], text=True
        )
        for row in json.loads(out_json):
            deps.append((row["Name"], _normalise_spdx(row["License"])))
    return deps

# ─────────────────────────  C. GitHub fallback  ─────────────────────────
def dependency_graph_api(repo: str, gh_token: str) -> List[Dict]:
    """Return list of dicts: {name, spdx, parent} for each dependency"""
    url = f"https://api.github.com/repos/{repo}/dependency-graph/sbom"
    hdr = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {gh_token}",
    }
    sbom = requests.get(url, headers=hdr).json()

    # Build SPDX name → license mapping
    license_map = {
        p["SPDXID"]: _normalise_spdx(
            p.get("licenseConcluded") or p.get("licenseDeclared") or ""
        )
        for p in sbom.get("packages", [])
    }

    # Build dependency edges using 'DEPENDS_ON' relationships
    deps = []
    for rel in sbom.get("relationships", []):
        if rel.get("relationshipType") == "DEPENDS_ON":
            src = rel.get("source")
            tgt = rel.get("target")
            tgt_license = license_map.get(tgt)
            if tgt_license:
                deps.append({
                    "name": tgt,
                    "spdx": tgt_license,
                    "parent": src
                })
    return deps

# ─────────────────────────  Dispatcher  ─────────────────────────
def load_dependencies(repo_path: pathlib.Path, gh_repo: str = "",
                      gh_token: Optional[str] = None
                      ) -> List[Tuple[str,str]]:
    """
    1. use lock / manifest if present,
    2. else fallback to GitHub API.
    """
    # core/dependency_parser.py  (inside load_dependencies)
    if (repo_path / "package.json").exists() and not (repo_path / "package-lock.json").exists():
        # call license-checker on the fly
        out = subprocess.check_output(
            ["npx", "license-checker", "--json"], cwd=repo_path, text=True
        )
        data = json.loads(out)
        return [(pkg, _normalise_spdx(meta["licenses"])) for pkg, meta in data.items()]

    if (repo_path / "requirements.txt").exists():
        return parse_requirements(repo_path / "requirements.txt")
    if gh_repo and gh_token:
        return dependency_graph_api(gh_repo, gh_token)
    return []
