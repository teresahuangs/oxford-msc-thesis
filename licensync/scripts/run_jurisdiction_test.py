#!/usr/bin/env python3
# In licensync/scripts/run_jurisdiction_test.py

import pandas as pd
from licensync.core.prolog_interface import evaluate_license_pair

def run_jurisdiction_experiment():
    """
    Measures how compatibility verdicts change across different legal jurisdictions,
    ensuring each unique pair is tested only once.
    """
    print("--- Running Final, Corrected Jurisdiction Flip Rate Experiment ---")

   
    golden_truth_data = [
    # --- Standard Permissive & Copyleft Combinations ---
    {'lic_parent': 'MIT', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'ISC', 'lic_child': 'BSD-3-Clause', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'Apache-2.0', 'lic_child': 'MPL-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'MIT', 'lic_child': 'LGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'MIT', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'MPL-2.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'LGPL-3.0-only', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'EPL-2.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    
    # --- Problematic & Famous Incompatibilities ---
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'global'},
    {'lic_parent': 'MIT', 'lic_child': 'Commons-Clause', 'label': 'incompatible', 'jurisdiction': 'us'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'CC-BY-NC-SA-4.0', 'label': 'incompatible', 'jurisdiction': 'global'},
    {'lic_parent': 'Apache-2.0', 'lic_child': 'Confluent-Community-1.0', 'label': 'incompatible', 'jurisdiction': 'global'},
    {'lic_parent': 'Apache-2.0', 'lic_child': 'Elastic-License-2.0', 'label': 'incompatible', 'jurisdiction': 'us'},
    {'lic_parent': 'MIT', 'lic_child': 'BSL-1.1', 'label': 'incompatible', 'jurisdiction': 'global'},

    # --- Jurisdiction-Specific Cases ---
    {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'global'},
    {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'eu'},
    {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'compatible', 'jurisdiction': 'us'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'MIT', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'MIT', 'label': 'incompatible', 'jurisdiction': 'de'},
    
    # --- Public Domain & Ambiguous Cases ---
    {'lic_parent': 'CC0-1.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'Unlicense', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'MIT', 'lic_child': 'JSON', 'label': 'incompatible', 'jurisdiction': 'global'},
    
    # --- Advanced & Nuanced Cases ---
    {'lic_parent': 'GPL-2.0-with-classpath-exception', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'EUPL-1.2', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'eu'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'ODbL-1.0', 'label': 'incompatible', 'jurisdiction': 'global'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'CC-BY-SA-4.0', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'GPL-2.0-only', 'lic_child': 'Apache-2.0', 'label': 'incompatible', 'jurisdiction': 'global'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'MIT', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'Apache-2.0', 'lic_child': 'SSPL-1.0', 'label': 'incompatible', 'jurisdiction': 'eu'},

    {'lic_parent': 'LGPL-2.1-only', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'MPL-2.0', 'lic_child': 'MIT', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'BSD-2-Clause', 'lic_child': 'GPL-2.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'Apache-2.0', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'GPL-3.0-only', 'lic_child': 'EPL-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'MIT', 'lic_child': 'Redis-Source-Available-2.0', 'label': 'incompatible', 'jurisdiction': 'global'},
    {'lic_parent': 'BSD-3-Clause', 'lic_child': 'BSD-3-Clause', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'GPL-2.0-only', 'lic_child': 'LGPL-2.1-only', 'label': 'compatible', 'jurisdiction': 'global'},
    {'lic_parent': 'AGPL-3.0-only', 'lic_child': 'SSPL-1.0', 'label': 'incompatible', 'jurisdiction': 'global'},
    {'lic_parent': 'WTFPL', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'}
] 
    truth_df = pd.DataFrame(golden_truth_data)
    
    # --- FIX: Create a set of unique license pairs to test ---
    unique_pairs = {
        tuple(sorted((row['lic_parent'], row['lic_child'])))
        for _, row in truth_df.iterrows()
    }
    
    flips = []
    
    print(f"Analyzing {len(unique_pairs)} unique license pairs across multiple jurisdictions...")

    for pair in unique_pairs:
        lic1, lic2 = pair
        
        # Get the 'global' verdict as the baseline for this pair
        global_verdict = evaluate_license_pair(lic1, lic2, 'global')
        
        # Check other jurisdictions to see if the verdict flips
        for juris in ['us', 'eu', 'de']:
            juris_verdict = evaluate_license_pair(lic1, lic2, juris)
            
            if juris_verdict != global_verdict and 'unknown' not in juris_verdict:
                flips.append({
                    "Test Case": f"{lic1} vs. {lic2}",
                    "Global Verdict": global_verdict,
                    "Jurisdiction": juris.upper(),
                    "New Verdict": juris_verdict
                })
                print(f"  -> FLIP DETECTED ({juris.upper()}): {lic1} vs {lic2} changed from '{global_verdict}' to '{juris_verdict}'")

    total_unique_pairs = len(unique_pairs)
    flip_count = len(flips)
    flip_rate = (flip_count / total_unique_pairs) if total_unique_pairs > 0 else 0

    print(f"\\n--- Jurisdiction Flip Rate Report ---")
    print(f"Found {flip_count} unique pairs that flipped their verdict out of {total_unique_pairs} unique pairs tested.")
    print(f"Overall Flip Rate: {flip_rate:.1%}\\n")

    if flips:
        flips_df = pd.DataFrame(flips)
        print("Details of Flipped Pairs:")
        print(flips_df.to_markdown(index=False))

if __name__ == "__main__":
    # You must paste your full golden_truth_data list into the script for it to be accurate.
    run_jurisdiction_experiment()