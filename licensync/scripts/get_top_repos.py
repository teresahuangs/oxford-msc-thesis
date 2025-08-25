# In licensync/scripts/get_top_repos.py

import os
import requests
import json # <-- Import the json library

def get_top_100_repos():
    """
    Fetches the top 100 most-starred GitHub repositories and saves them to a JSON file.
    """
    print("--- Fetching top 100 most-starred repositories from GitHub ---")
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("FATAL: GITHUB_TOKEN environment variable not set.")
        return

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    url = "https://api.github.com/search/repositories?q=stars:>1000&sort=stars&order=desc&per_page=100"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        repo_names = [item['full_name'] for item in data.get('items', [])]
        
        # --- MODIFIED PART ---
        output_file = "top_100_repos.json" # <-- Save as .json
        with open(output_file, 'w') as f:
            json.dump(repo_names, f, indent=2) # <-- Save the list as a JSON array
        
        print(f"✅ Successfully saved {len(repo_names)} repository names to '{output_file}'")

    except requests.RequestException as e:
        print(f"❌ ERROR: Failed to fetch data from GitHub API. {e}")

if __name__ == "__main__":
    get_top_100_repos()