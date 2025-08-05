import requests
from typing import Optional          


def fetch_spdx_license(repo: str, token: Optional[str] = None) -> Optional[str]:
    """Fetch SPDX license for a GitHub repo like 'owner/repo'."""
    url = f"https://api.github.com/repos/{repo}/license"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"


    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    data = response.json()
    return data.get("license", {}).get("spdx_id", "").lower()
