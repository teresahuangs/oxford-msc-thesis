#!/usr/bin/env python3
# In licensync/scripts/test_prolog.py

import os
from pathlib import Path
from licensync.core.prolog_interface import evaluate_license_pair

def run_diagnostic():
    """Performs a step-by-step check of the Prolog setup."""
    print("--- Starting Final Diagnostic Test ---")

    # 1. Calculate the path to rules.pl from the perspective of the script
    try:
        # This logic should mirror what's in prolog_interface.py
        rules_path = (
            Path(__file__).resolve().parent.parent / "prolog_rules" / "rules.pl"
        ).resolve()
        print(f"[DIAGNOSTIC] Calculated absolute path to rules.pl:\\n  -> {rules_path}")
    except Exception as e:
        print(f"[FATAL] Could not calculate path to rules.pl. Error: {e}")
        return

    # 2. Check if the file actually exists at that path
    if os.path.exists(rules_path):
        print(f"[SUCCESS] File exists at the calculated path.")
    else:
        print(f"[FATAL] File NOT found at the calculated path.")
        print("This is the root cause. Please check your directory structure. The script expects:")
        print("  licensync/")
        print("  ├── core/")
        print("  └── prolog_rules/")
        print("      └── rules.pl")
        return # Stop here if the file doesn't exist

    # 3. Check if we have permission to read the file
    if os.access(rules_path, os.R_OK):
        print(f"[SUCCESS] File is readable.")
    else:
        print(f"[FATAL] File is not readable. Please check the file permissions.")
        return

    # 4. If all checks pass, run a simple test query
    print("\\n--- All checks passed. Attempting a live test query. ---")
    run_test("MIT", "Apache-2.0")


def run_test(lic1, lic2, jurisdiction="global"):
    """Helper to run and print a single test case."""
    print(f"\\nTesting: {lic1} vs. {lic2}")
    result = evaluate_license_pair(lic1, lic2, jurisdiction)
    print(f"  -> Final Verdict: {result}")


if __name__ == "__main__":
    run_diagnostic()