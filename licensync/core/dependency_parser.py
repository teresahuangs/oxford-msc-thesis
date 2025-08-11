
import json, pathlib, re
from typing import Dict, List, Tuple, Optional
from .license_utils import normalize_license
from .github_api import fetch_github_sbom, fetch_text_from_repo, list_repo_tree


def _strip(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9._/\-]+', '', s or '')

def flatten_sbom(owner_repo: str, sbom: Dict) -> List[Dict]:
    id_to_name: Dict[str, str] = {}
    id_to_license: Dict[str, str] = {}
    for p in sbom.get("packages", []):
        sid = p.get("SPDXID")
        if not sid:
            continue
        name = p.get("name") or sid
        lic = p.get("licenseConcluded") or p.get("licenseDeclared") or "unknown"
        id_to_name[sid] = _strip(name)
        id_to_license[sid] = normalize_license(lic)
    edges: List[Dict] = []
    for rel in sbom.get("relationships", []) or []:
        if rel.get("relationshipType") != "DEPENDS_ON":
            continue
        src = id_to_name.get(rel.get("source"))
        tgt = id_to_name.get(rel.get("target"))
        if not tgt:
            continue
        edges.append({
            "name": tgt,
            "license": id_to_license.get(rel.get("target"), "unknown"),
            "parent": src or owner_repo,
        })
    return edges

def parse_requirements_text(text: str) -> List[Tuple[str, str]]:
    deps: List[Tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        if line.startswith(('-r','--requirement','-c','--constraint')): continue
        name = re.split(r'[<>=!~ ]+', line)[0]
        if name: deps.append((name, "unknown"))
    return deps

def parse_pyproject(text: str) -> List[Tuple[str, str]]:
    deps: List[Tuple[str, str]] = []
    m = re.search(r'^\[project\][\s\S]*?^dependencies\s*=\s*\[(.*?)\]', text, flags=re.MULTILINE|re.DOTALL)
    if m:
        inner = m.group(1)
        for item in re.findall(r'["\']([^"\']+)["\']', inner):
            name = re.split(r'[<>=!~ ]+', item.strip())[0]
            if name: deps.append((name, "unknown"))
    # Poetry tool
    block = re.search(r'^\[tool\.poetry\.dependencies\](.*?)(^\[|\Z)', text, flags=re.MULTILINE|re.DOTALL)
    if block:
        body = block.group(1)
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            key = line.split("=",1)[0].strip().strip('"\'')
            if key.lower()=="python": continue
            deps.append((key, "unknown"))
    return deps

def parse_setup_cfg(text: str) -> List[Tuple[str, str]]:
    deps: List[Tuple[str, str]] = []
    m = re.search(r'^\[options\][\s\S]*?^install_requires\s*=\s*(.*?)^(\[|\Z)', text, flags=re.MULTILINE|re.DOTALL)
    if m:
        inner = m.group(1)
        for line in inner.splitlines():
            line = line.strip().lstrip('-').strip()
            if not line or line.startswith("#"): continue
            name = re.split(r'[<>=!~ ]+', line)[0]
            if name: deps.append((name, "unknown"))
    return deps

def parse_setup_py(text: str) -> List[Tuple[str, str]]:
    deps: List[Tuple[str, str]] = []
    m = re.search(r'install_requires\s*=\s*\[(.*?)\]', text, flags=re.DOTALL)
    if m:
        inner = m.group(1)
        for item in re.findall(r'["\']([^"\']+)["\']', inner):
            name = re.split(r'[<>=!~ ]+', item.strip())[0]
            if name: deps.append((name, "unknown"))
    return deps

PY_PATTERNS = (
    re.compile(r'(^|/)requirements[^/]*\.txt$', re.IGNORECASE),
    re.compile(r'(^|/)requirements/[^/]+\.txt$', re.IGNORECASE),
    re.compile(r'(^|/)pyproject\.toml$', re.IGNORECASE),
    re.compile(r'(^|/)setup\.cfg$', re.IGNORECASE),
    re.compile(r'(^|/)setup\.py$', re.IGNORECASE),
)

def _collect_python_manifests(owner_repo: str, token: Optional[str]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    try:
        tree = list_repo_tree(owner_repo, token)
    except Exception:
        tree = []
    for entry in tree:
        path = (entry.get("path") or "")
        if not any(p.search(path) for p in PY_PATTERNS):
            continue
        txt = fetch_text_from_repo(owner_repo, path, token)
        if txt:
            out.append((path, txt))
    return out

# licensync/core/dependency_parser.py

def load_dependencies(local_path: pathlib.Path,
                      gh_repo: str = "",
                      gh_token: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Load dependencies for a project.

    Prioritizes fetching from GitHub's dependency graph SBOM API if a repo
    is specified. Falls back to manually parsing manifest files if the SBOM
    API fails.
    """
    # 1. GitHub SBOM (Primary Method for GitHub Repos)
    if gh_repo:
        try:
            print(f"Attempting to fetch SBOM for {gh_repo}...")
            sbom = fetch_github_sbom(gh_repo, gh_token)
            edges = flatten_sbom(gh_repo, sbom)
            if edges:
                print(f"Successfully loaded {len(edges)} dependencies from SBOM.")
                # Convert from edge list to a simple (name, license) tuple list
                deps = {(item['name'], item['license']) for item in edges}
                return sorted(list(deps))
        except Exception as e:
            print(f"SBOM for {gh_repo} failed: {e}. Falling back to manual parsing.")

        # 2. GitHub Manual Parsing (Fallback)
        print(f"Falling back to manually parsing manifests for {gh_repo}...")
        deps: List[Tuple[str, str]] = []
        manifests = _collect_python_manifests(gh_repo, gh_token)
        manifests += _collect_js_manifests(gh_repo, gh_token)

        if not manifests:
            print("Could not find any dependency manifests.")
            return []

        for path, txt in manifests:
            if "requirements" in path and path.endswith(".txt"):
                deps.extend(parse_requirements_text(txt))
            elif path.endswith("pyproject.toml"):
                deps.extend(parse_pyproject(txt))
            elif path.endswith("setup.cfg"):
                deps.extend(parse_setup_cfg(txt))
            elif path.endswith("setup.py"):
                deps.extend(parse_setup_py(txt))
            elif path.endswith("package.json"):
                deps.extend(parse_package_json(txt))
        
        # Deduplicate and return
        uniq = {name: lic or "unknown" for name, lic in deps}
        return sorted(uniq.items())

    # 3. Local File Parsing
    for fn in ["requirements.txt", "pyproject.toml", "setup.cfg", "setup.py"]:
        p = local_path / fn
        if not p.exists(): continue
        txt = p.read_text()
        if fn.endswith(".txt"): return parse_requirements_text(txt)
        if fn == "pyproject.toml": return parse_pyproject(txt)
        if fn == "setup.cfg": return parse_setup_cfg(txt)
        if fn == "setup.py": return parse_setup_py(txt)

    return []

def parse_package_json(text: str) -> List[Tuple[str, str]]:
    try:
        j = json.loads(text)
    except Exception:
        return []
    deps: List[Tuple[str, str]] = []
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        for name in (j.get(key) or {}):
            deps.append((name, "unknown"))
    return deps

JS_PATTERNS = (
    re.compile(r'(^|/)package\.json$', re.IGNORECASE),
)

def _collect_js_manifests(owner_repo: str, token: Optional[str]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    try:
        tree = list_repo_tree(owner_repo, token)
    except Exception:
        tree = []
    for entry in tree:
        path = (entry.get("path") or "")
        if not any(p.search(path) for p in JS_PATTERNS):
            continue
        txt = fetch_text_from_repo(owner_repo, path, token)
        if txt:
            out.append((path, txt))
    return out

