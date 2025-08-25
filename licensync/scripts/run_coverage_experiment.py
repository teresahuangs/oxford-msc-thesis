import os
import pandas as pd
import requests
import json
from typing import Set, List, Tuple
import time
import traceback

# Import functions from your project's core files
from licensync.core.dependency_parser import load_dependencies, flatten_sbom
from licensync.core.github_api import fetch_github_sbom
from licensync.core.license_utils import normalize_license

# --- Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PROJECTS_TO_TEST = "top_100_repos.json"

def load_projects_from_file(filename: str) -> list:
    """Loads a list of repositories from a JSON file."""
    try:
        with open(filename, 'r') as f:
            projects = json.load(f)
        print(f"Loaded {len(projects)} projects to test from '{filename}'")
        return projects
    except FileNotFoundError:
        print(f"FATAL: Project list file not found at '{filename}'.")
        return []
    except json.JSONDecodeError:
        print(f"FATAL: Could not parse JSON from '{filename}'.")
        return []

# The script will now get its list of projects from this file
 # <-- Point to the .json file

# (The rest of your script remains exactly the same)
# (The rest of your script remains exactly the same)


SCANCODE_RESULTS_DIR = "licensync/data/scancode-results"


# --- NEW: Multi-Source Enrichment Functions ---

def enrich_from_clearlydefined(name: str, ecosystem: str) -> str:
    """Tries to get a license from the ClearlyDefined API."""
    if ecosystem == "pypi":
        cd_url = f"https://api.clearlydefined.io/definitions/pypi/pypi/-/{name}"
    elif ecosystem == "npm":
        cd_url = f"https://api.clearlydefined.io/definitions/npm/npmjs/-/{name}"
    else:
        return 'unknown'

    try:
        res = requests.get(cd_url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get('licensed', {}).get('declared', 'unknown')
    except requests.RequestException:
        return 'unknown'
    return 'unknown'

def enrich_from_native_registry(name: str, ecosystem: str) -> str:
    """Tries to get a license from the native package registry (PyPI or npm)."""
    if ecosystem == "pypi":
        registry_url = f"https://pypi.org/pypi/{name}/json"
        try:
            res = requests.get(registry_url, timeout=10)
            if res.status_code == 200:
                # PyPI license info is often in classifiers or the 'license' field
                info = res.json().get('info', {})
                license_str = info.get('license')
                if license_str and 'unknown' not in license_str.lower():
                    return license_str
                # Check classifiers for a license string
                for classifier in info.get('classifiers', []):
                    if "License :: OSI Approved ::" in classifier:
                        return classifier.split("::")[-1].strip()
        except requests.RequestException:
            return 'unknown'
    elif ecosystem == "npm":
        registry_url = f"https://registry.npmjs.org/{name}"
        try:
            res = requests.get(registry_url, timeout=10)
            if res.status_code == 200:
                return res.json().get('license', 'unknown')
        except requests.RequestException:
            return 'unknown'
    return 'unknown'

def enrich_licenses_waterfall(dependencies: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """
    The main enrichment function. Takes (name, ecosystem) tuples and tries
    multiple sources to find a license.
    """
    enriched_deps = []
    for name, ecosystem in dependencies:
        print(f"    -> Enriching '{name}' ({ecosystem})...")
        time.sleep(0.25)  # Rate limit

        # 1. Try ClearlyDefined first
        license = enrich_from_clearlydefined(name, ecosystem)

        # 2. If it fails, try the native registry
        if license == 'unknown' or not license:
            print(f"      -> ClearlyDefined failed, trying native registry...")
            license = enrich_from_native_registry(name, ecosystem)

        final_license = normalize_license(license)
        print(f"      -> Found license: {final_license}")
        enriched_deps.append((name, final_license))
            
    return enriched_deps

# --- Modified Experiment Logic ---

def get_licensync_deps(repo: str, token: str) -> Tuple[Set[str], Set[str]]:
    """Runs your tool and enriches the results using the new waterfall method."""
    print(f"[LicenSync] Analyzing {repo}...")
    initial_deps = load_dependencies(local_path=None, gh_repo=repo, gh_token=token)
    
    if initial_deps:
        print(f"  -> Enriching licenses for {len(initial_deps)} dependencies...")
        enriched_dependencies = enrich_licenses_waterfall(initial_deps)
    else:
        enriched_dependencies = []

    licensed_deps = {name for name, license in enriched_dependencies if license != 'unknown'}
    all_deps = {name for name, _ in initial_deps}
    return licensed_deps, all_deps

# (The rest of the script, get_github_api_deps and run_experiment, remains the same)
def get_github_api_deps(repo: str, token: str) -> Tuple[Set[str], Set[str]]:
    print(f"[GitHub API] Analyzing {repo}...")
    try:
        sbom = fetch_github_sbom(repo, token)
        edges = flatten_sbom(repo, sbom)
        licensed_deps = {dep['name'] for dep in edges if dep.get('license') != 'unknown'}
        all_deps = {dep['name'] for dep in edges}
        return licensed_deps, all_deps
    except Exception:
        return set(), set()

def get_scancode_deps(repo: str) -> Tuple[Set[str], Set[str]]:
    """Parses a Scancode JSON report to extract dependency information."""
    print(f"[Scancode] Analyzing {repo}...")
    repo_name = repo.split('/')[1]
    json_path = os.path.join(SCANCODE_RESULTS_DIR, f"scancode-{repo_name}.json")

    if not os.path.exists(json_path):
        print(f"  -> Scancode report not found at {json_path}")
        return set(), set()

    with open(json_path, 'r') as f:
        data = json.load(f)

    all_deps = set()
    licensed_deps = set()

    # Scancode puts discovered package manifests in the 'packages' list
    for package in data.get('packages', []):
        if package.get('name'):
            all_deps.add(package['name'])
            # A dependency is "covered" if it has a declared license
            if package.get('declared_license_expression'):
                licensed_deps.add(package['name'])
    
    return licensed_deps, all_deps




def run_experiment():
    """Executes the full comparative analysis for coverage."""
    if not GITHUB_TOKEN:
        print("FATAL: GITHUB_TOKEN environment variable not set. Aborting.")
        return

    # --- CORRECTED LOADING LOGIC ---
    # The project list is now loaded cleanly inside the main function.
    projects_to_test = load_projects_from_file(PROJECTS_TO_TEST)
    if not projects_to_test:
        return
    
    results = []
    # Now, loop through the list of projects correctly
    for project in projects_to_test:
        if not project: continue
        # Get data from both your tool and the baseline
        ls_licensed, ls_all = get_licensync_deps(project, GITHUB_TOKEN)
        gh_licensed, gh_all = get_github_api_deps(project, GITHUB_TOKEN)

        master_list_deps = ls_all.union(gh_all)
        total_deps = len(master_list_deps)
        
        if total_deps == 0:
            print(f"  -> No dependencies found for {project}. Skipping.")
            print("-" * 40)
            continue

        # Calculate coverage for each tool
        ls_coverage = len(ls_licensed) / total_deps if total_deps > 0 else 0
        gh_coverage = len(gh_licensed) / total_deps if total_deps > 0 else 0

        results.append({
            "Project": f"`{project}`",
            "Total Dependencies (Union)": total_deps,
            "LicenSync Coverage": f"{ls_coverage:.1%}",
            "GitHub API Coverage": f"{gh_coverage:.1%}",
        })
        print("-" * 40)

    # Generate and print the final report table
    report_df = pd.DataFrame(results)
    
    print("\n\n--- Comparative Coverage Analysis Report ---")
    print(report_df.to_markdown(index=False))

# --- This ensures the script runs when called ---
if __name__ == "__main__":
    # You will need to copy the full code for the helper functions
    # (enrich_*, get_licensync_deps, get_github_api_deps) into this script
    # for it to be self-contained and runnable. They are omitted here for brevity
    # but must be present in your file.
    run_experiment()