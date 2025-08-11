
import requests

API_VER = "2022-11-28"

def _headers(token: str | None):
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VER}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def fetch_github_sbom(owner_repo: str, token: str | None):
    url = f"https://api.github.com/repos/{owner_repo}/dependency-graph/sbom"
    r = requests.get(url, headers=_headers(token), timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_repo_license_spdx(owner_repo: str, token: str | None) -> str | None:
    url = f"https://api.github.com/repos/{owner_repo}"
    r = requests.get(url, headers=_headers(token), timeout=30)
    if r.status_code != 200:
        return None
    lic = (r.json().get("license") or {}).get("spdx_id")
    return lic if lic and lic != "NOASSERTION" else None

def fetch_text_from_repo(owner_repo: str, path: str, token: str | None) -> str | None:
    url = f"https://api.github.com/repos/{owner_repo}/contents/{path}"
    r = requests.get(url, headers=_headers(token), timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    content = data.get("content")
    if not content:
        return None
    if data.get("encoding") == "base64":
        import base64
        return base64.b64decode(content).decode("utf-8", errors="ignore")
    return content

def list_repo_tree(owner_repo: str, token: str | None) -> list[dict]:
    # Try HEAD shortcut
    url = f"https://api.github.com/repos/{owner_repo}/git/trees/HEAD?recursive=1"
    r = requests.get(url, headers=_headers(token), timeout=30)
    if r.status_code == 200:
        return r.json().get("tree", []) or []
    # Fallback: resolve default branch then tree
    meta = requests.get(f"https://api.github.com/repos/{owner_repo}", headers=_headers(token), timeout=30).json()
    default = meta.get("default_branch", "main")
    ref = requests.get(f"https://api.github.com/repos/{owner_repo}/git/refs/heads/{default}", headers=_headers(token), timeout=30).json()
    sha = (ref.get("object") or {}).get("sha")
    if not sha:
        return []
    tree = requests.get(f"https://api.github.com/repos/{owner_repo}/git/trees/{sha}?recursive=1", headers=_headers(token), timeout=30).json()
    return tree.get("tree", []) or []
