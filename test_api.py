import os
import requests

# --- Configuration ---
TOKEN = os.getenv("GITHUB_TOKEN")
REPO_TO_TEST = "pallets/flask"
API_URL = f"https://api.github.com/repos/{REPO_TO_TEST}/dependency-graph/sbom"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}

# --- Test Logic ---
print("--- Running GitHub API Connection Test ---")

if not TOKEN:
    print("❌ FAILURE: GITHUB_TOKEN not found in environment!")
    print("Please run 'export GITHUB_TOKEN=\"ghp_YourTokenHere\"' in your terminal.")
else:
    print(f"✅ Found token starting with: {TOKEN[:7]}...")
    print(f"Querying API for: {REPO_TO_TEST}")
    
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        
        print(f"\\n-> HTTP Status Code: {response.status_code}")
        print("-> Response Body (first 200 chars):")
        print(response.text[:200])

        if response.status_code == 200:
            print("\\n✅ SUCCESS: Your token is working correctly!")
        elif response.status_code == 401:
            print("\\n❌ FAILURE: Status code 401 (Unauthorized). Your token is incorrect, invalid, or expired.")
        elif response.status_code in [403, 404]:
            print("\\n❌ FAILURE: Status code {response.status_code}. Your token is likely valid but is MISSING THE REQUIRED 'repo' SCOPE.")
            
    except requests.exceptions.RequestException as e:
        print(f"\\n❌ FAILURE: A network error occurred.")
        print(f"Could not connect to api.github.com. Check your firewall or proxy settings.")
        print(f"Error details: {e}")