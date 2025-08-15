# In licensync/core/dependency_parser.py

import json
import pathlib
import re
from typing import Dict, List, Tuple, Optional
import traceback # Add traceback for better error logging

# Import the necessary functions from your own project's core files
from .license_utils import normalize_license
from .github_api import fetch_github_sbom, fetch_text_from_repo, list_repo_tree

# --- Manifest Parsing Functions ---
# (These functions parse the text of different dependency files)

def parse_requirements_text(text: str) -> List[Tuple[str, str]]:
    deps: List[Tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        name = re.split(r'[<>=!~ ]+', line)[0]
        if name: deps.append((name, "unknown"))
    return deps

def parse_pyproject(text: str) -> List[Tuple[str, str]]:
    deps: List[Tuple[str, str]] = []
    # Look for [project.dependencies]
    try:
        m = re.search(r'\\[project\\.dependencies\\]\s*=\s*\\[(.*?)\\]', text, flags=re.MULTILINE|re.DOTALL)
        if m:
            for item in re.findall(r'["\']([^"\']+)["\']', m.group(1)):
                name = re.split(r'[<>=!~ ]+', item.strip())[0]
                if name: deps.append((name, "unknown"))
    except Exception:
        pass # Ignore TOML parsing errors in this simple version
    return deps

def parse_package_json(text: str) -> List[Tuple[str, str]]:
    deps: List[Tuple[str, str]] = []
    try:
        data = json.loads(text)
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            if key in data and isinstance(data[key], dict):
                for name in data[key]:
                    deps.append((name, "unknown"))
    except json.JSONDecodeError:
        pass # Ignore malformed JSON
    return deps

# --- Main Dependency Loading Logic ---

def load_dependencies(local_path: Optional[pathlib.Path], # Allow None for gh_repo only
                      gh_repo: str = "",
                      gh_token: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Load dependencies for a project, prioritizing GitHub's SBOM API,
    but falling back to robust manual manifest parsing.
    """
    if not gh_repo:
        # (Your original local file parsing logic can go here if needed)
        return []

    # --- Method 1: Try the GitHub SBOM API First ---
    try:
        print(f"Attempting to fetch SBOM for {gh_repo}...")
        sbom = fetch_github_sbom(gh_repo, gh_token)
        edges = flatten_sbom(gh_repo, sbom)
        if edges:
            print(f"  -> Successfully loaded {len(edges)} dependencies from SBOM.")
            deps = {(item['name'], item['license']) for item in edges}
            return sorted(list(deps))
        print("  -> SBOM was valid but empty, proceeding to manual parsing.")
    except Exception:
        print(f"  -> SBOM for {gh_repo} failed critically. See error below.")
        traceback.print_exc(limit=1)
        print("  -> Falling back to manual parsing.")

    # --- Method 2: Fallback to Manual Manifest Parsing ---
    # Method 2: Fallback to Manual Manifest Parsing
    print(f"Falling back to manually parsing manifests for {gh_repo}...")
    deps: List[Tuple[str, str]] = [] # Now stores (name, ecosystem)
    try:
        repo_tree = list_repo_tree(gh_repo, gh_token)
        manifest_paths = [
            item['path'] for item in repo_tree
            if item['path'].endswith(('requirements.txt', 'pyproject.toml', 'package.json'))
        ]
        
        for path in manifest_paths:
            print(f"  -> Found manifest: {path}. Fetching and parsing...")
            content = fetch_text_from_repo(gh_repo, path, gh_token)
            if not content: continue
            
            # --- MODIFIED LOGIC ---
            # Identify the ecosystem from the filename
            if path.endswith(('requirements.txt', 'pyproject.toml')):
                ecosystem = "pypi"
                parsed_deps = parse_pyproject(content) if 'pyproject' in path else parse_requirements_text(content)
            elif path.endswith('package.json'):
                ecosystem = "npm"
                parsed_deps = parse_package_json(content)
            else:
                continue

            # Add the name and its identified ecosystem to the list
            for name, _ in parsed_deps:
                deps.append((name, ecosystem))

    except Exception:
        print("  -> Error during manual manifest parsing.")
        traceback.print_exc(limit=1)

    uniq_deps = list(set(deps))
    print(f"  -> Found {len(uniq_deps)} unique dependencies via manual parsing.")
    return uniq_deps


# You need flatten_sbom in this file as well, assuming it wasn't here before
def flatten_sbom(owner_repo: str, sbom: Dict) -> List[Dict]:
    # (Ensure the flatten_sbom function from your original file is present here)
    id_to_name: Dict[str, str] = {}
    id_to_license: Dict[str, str] = {}
    for p in sbom.get("packages", []):
        sid = p.get("SPDXID")
        if not sid: continue
        name = p.get("name") or sid
        lic = p.get("licenseConcluded") or p.get("licenseDeclared") or "unknown"
        id_to_name[sid] = name
        id_to_license[sid] = normalize_license(lic)
    edges: List[Dict] = []
    for rel in sbom.get("relationships", []) or []:
        if rel.get("relationshipType") != "DEPENDS_ON": continue
        src_id = rel.get("spdxElementId")
        tgt_id = rel.get("relatedSpdxElementId")
        tgt_name = id_to_name.get(tgt_id)
        if not tgt_name: continue
        edges.append({
            "name": tgt_name,
            "license": id_to_license.get(tgt_id, "unknown"),
            "parent": id_to_name.get(src_id, owner_repo),
        })
    return edges