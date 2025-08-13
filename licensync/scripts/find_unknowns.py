# In licensync/scripts/find_unknowns.py

import pandas as pd
from collections import Counter
from licensync.core.prolog_interface import evaluate_license_pair
from licensync.core.license_utils import normalize_license # Import the normalizer

def main():
    """
    Analyzes a ground truth file to find which licenses are not recognized
    by the Prolog engine.
    """
    truth_file = 'licensync/data/edge_truth_2.csv' # Make sure this path is correct
    print(f"--- Analyzing {truth_file} for unknown licenses ---\\n")

    df = pd.read_csv(truth_file)
    unknown_licenses = []

    # Get a set of all known atoms from your rules file for comparison
    # This is a simplified list; you could parse rules.pl for a complete one
    known_atoms = {'mit', 'apache2', 'bsd2', 'bsd3', 'isc', 'gpl2', 'gpl3', 'agpl3', 'lgpl2', 'lgpl3', 'mpl2', 'epl2', 'sspl', 'unlicense', 'cc0'}

    all_licenses = pd.concat([df['lic_parent'], df['lic_child']]).dropna().unique()

    for lic_str in all_licenses:
        normalized = normalize_license(lic_str)
        if normalized not in known_atoms:
            unknown_licenses.append(lic_str)

    if not unknown_licenses:
        print("✅ All license strings appear to map to known Prolog atoms!")
        return

    print("Found the following license strings that do not map to a known Prolog atom:")
    # Print the top 20 most frequent unrecognized license strings
    for lic, count in Counter(unknown_licenses).most_common(20):
        print(f"  - '{lic}' (appears ~{count} times)")

    print("\\nNext steps: Update 'license_utils.py' or 'rules.pl' to handle these licenses.")


if __name__ == "__main__":
    main()