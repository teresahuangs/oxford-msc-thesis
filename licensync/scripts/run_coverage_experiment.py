#!/usr/bin/env python3
# In licensync/scripts/run_coverage_experiment.py

import os
import pandas as pd
import requests
from typing import Set, List, Tuple
import time
import traceback
import json

# Import functions from your project's core files
from licensync.core.dependency_parser import load_dependencies, flatten_sbom
from licensync.core.github_api import fetch_github_sbom
from licensync.core.license_utils import normalize_license


# --- Configuration ---
PROJECTS_TO_TEST = [
    "expressjs/express", "pallets/flask", "psf/requests",
    "facebook/react", "apache/kafka"
]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
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

# --- Main Experiment Logic (Updated) ---

def run_experiment():
    if not GITHUB_TOKEN:
        print("FATAL: GITHUB_TOKEN environment variable not set. Aborting.")
        return

    results = []

    for project in PROJECTS_TO_TEST:
        # Get data from all three sources
        ls_licensed, ls_all = get_licensync_deps(project, GITHUB_TOKEN)
        gh_licensed, gh_all = get_github_api_deps(project, GITHUB_TOKEN)
        sc_licensed, sc_all = get_scancode_deps(project)

        # Create the master list (union) of all dependencies found
        master_list_deps = ls_all.union(gh_all).union(sc_all)
        total_deps = len(master_list_deps)
        
        if total_deps == 0:
            print(f"  -> No dependencies found for {project}. Skipping.")
            continue

        # Calculate coverage for each tool
        ls_coverage = len(ls_licensed) / total_deps if total_deps > 0 else 0
        gh_coverage = len(gh_licensed) / total_deps if total_deps > 0 else 0
        sc_coverage = len(sc_licensed) / total_deps if total_deps > 0 else 0

        results.append({
            "Project": f"`{project}`",
            "Total Dependencies (Union)": total_deps,
            "LicenSync Coverage": f"{ls_coverage:.1%}",
            "GitHub API Coverage": f"{gh_coverage:.1%}",
            "Scancode Coverage": f"{sc_coverage:.1%}", # <-- New column
        })
        print("-" * 40)

    # Generate and print the final report table
    report_df = pd.DataFrame(results)
    
    print("\n\n--- Comparative Coverage Analysis Report ---")
    print(report_df.to_markdown(index=False))

if __name__ == "__main__":
    # You can reuse the get_licensync_deps and get_github_api_deps from your previous script
    # For brevity, they are not repeated here. Paste them into this script.
    print("Please ensure you have pasted the full get_licensync_deps and get_github_api_deps functions into this script.")
    run_experiment()