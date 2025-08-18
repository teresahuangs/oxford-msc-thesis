#!/usr/bin/env python3
# In licensync/scripts/final_verification_and_jurisdiction_test.py

import pandas as pd
import subprocess
import re
from pathlib import Path

# --- Self-Contained Helper Functions (to avoid any cross-file issues) ---

PROLOG_FILE: Path = (
    Path(__file__).resolve().parent.parent / "prolog_rules" / "rules.pl"
).resolve()

SPDX_TO_PROLOG = {
    "mit": "mit", "apache-2.0": "apache2", "bsd-3-clause": "bsd3",
    "bsd-2-clause": "bsd2", "mpl-2.0": "mpl2", "lgpl-3.0-only": "lgpl3",
    "lgpl-2.1-only": "lgpl2", "gpl-3.0-only": "gpl3", "gpl-2.0-only": "gpl2",
    "agpl-3.0-only": "agpl3", "epl-2.0": "epl2", "cc0-1.0": "cc0", "0bsd": "bsd0",
    "sspl-1.0": "sspl", "commons-clause": "commons_clause", "cc-by-nc-sa-4.0": "cc_by_nc_sa_4",
    "confluent-community-1.0": "confluent_community_1", "elastic-license-2.0": "elastic2",
    "unlicense": "unlicense", "isc": "isc", "gpl-2.0-with-classpath-exception": "gpl2_classpath",
    "bsl-1.1": "bsl1_1", "odbl-1.0": "odbl1", "cc-by-sa-4.0": "cc_by_sa_4",
    "json": "json", "eupl-1.2": "eupl1_2", "unknown": "unknown",
}

def normalize_license(license_str: str) -> str:
    s = str(license_str).strip().lower()
    return SPDX_TO_PROLOG.get(s, s)

def _atom(s: str) -> str:
    if re.match(r"^[a-z][a-zA-Z0-9_]*$", s):
        return s
    else:
        return f"'{s}'"

def evaluate_license_pair(lic1: str, lic2: str, juris: str) -> str:
    norm_lic1 = normalize_license(lic1)
    norm_lic2 = normalize_license(lic2)
    l1 = _atom(norm_lic1)
    l2 = _atom(norm_lic2)
    j  = _atom(juris)
    query = f"evaluate_pair({l1},{l2},{j},Result),write(Result),halt."
    command = ["swipl", "-q", "-s", str(PROLOG_FILE), "-g", query]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if proc.returncode != 0: return f"Error: {proc.stderr.strip()}"
        return proc.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

# --- Main Experiment Logic ---
def run_jurisdiction_experiment():
    print("--- Running Final, Self-Contained Jurisdiction Flip Rate Experiment ---")

    golden_truth_data = [
        {'lic_parent': 'MIT', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Standard permissive combination'},
        {'lic_parent': 'ISC', 'lic_child': 'BSD-3-Clause', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Two similar permissive licenses'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'MPL-2.0', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Permissive with weak copyleft; allowed'},
        {'lic_parent': 'MIT', 'lic_child': 'LGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Permissive library can be used by an LGPL project'},
        {'lic_parent': 'MIT', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Permissive license is compatible with strong copyleft'},
        {'lic_parent': 'MPL-2.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'MPLv2 was designed for GPL compatibility'},
        {'lic_parent': 'LGPL-3.0-only', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'GPLv3 explicitly allows linking with LGPLv3'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Identical strong copyleft licenses'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'global', 'reason': 'Problematic Pair (Global): Incompatible due to patent clauses'},
        {'lic_parent': 'GPL-2.0-only', 'lic_child': 'Apache-2.0', 'label': 'incompatible', 'jurisdiction': 'global', 'reason': 'Problematic Pair (Global): Reverse of the above; still incompatible'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Problematic Pair (Global): GPL-3.0 explicitly solved Apache-2.0 compatibility'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Problematic Pair (Global): Reverse of the above; still compatible'},
        {'lic_parent': 'MIT', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Permissive license can be incorporated into AGPL'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Allowed by Section 13 of both licenses'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'SSPL-1.0', 'label': 'incompatible', 'jurisdiction': 'eu', 'reason': 'Problematic Pair (Network): SSPL is not OSI-approved and conflicts with traditional OSS'},
        {'lic_parent': 'MIT', 'lic_child': 'Commons-Clause', 'label': 'incompatible', 'jurisdiction': 'us', 'reason': 'Problematic Pair (Non-Commercial): Commons Clause adds conflicting commercial restrictions'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'CC-BY-NC-SA-4.0', 'label': 'incompatible', 'jurisdiction': 'global', 'reason': 'Problematic Pair (Non-Commercial): NC clause is incompatible with GPL'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'Confluent-Community-1.0', 'label': 'incompatible', 'jurisdiction': 'global', 'reason': 'Problematic Pair (Source-Available): Confluent license has conflicting use restrictions'},
        {'lic_parent': 'EPL-2.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Weak copyleft EPL-2.0 has a secondary license provision for GPL compatibility'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'MIT', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Patent Grant Test: Apache-2.0\'s patent grant is compatible with MIT'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'global', 'reason': 'Patent Grant Test: GPLv3 includes patent grant language that is not in GPLv2, creating an incompatibility'},
        {'lic_parent': 'CC0-1.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Public Domain Test: CC0 is a dedication to public domain and compatible with GPL'},
        {'lic_parent': 'Unlicense', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Public Domain Test: Unlicense is compatible with strong copyleft'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'Elastic-License-2.0', 'label': 'incompatible', 'jurisdiction': 'us', 'reason': 'Source-Available Test: Elastic License 2.0 is not open source and conflicts with Apache-2.0'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'compatible', 'jurisdiction': 'us', 'reason': 'Jurisdiction Test: Models US-specific interpretation of implied patent grants making it compatible'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'eu', 'reason': 'Jurisdiction Test: Models EU-specific interpretation where the patent conflict remains'},
        {'lic_parent': 'GPL-2.0-with-classpath-exception', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Nuanced Copyleft: The Classpath Exception allows linking with libraries under different terms'},
        {'lic_parent': 'MIT', 'lic_child': 'BSL-1.1', 'label': 'incompatible', 'jurisdiction': 'global', 'reason': 'Modern Source-Available: BSL is non-commercial until its Change Date'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'ODbL-1.0', 'label': 'incompatible', 'jurisdiction': 'global', 'reason': 'Data License Test: ODbL\'s terms for database sharing conflict with GPL for tightly coupled works'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'CC-BY-SA-4.0', 'label': 'compatible', 'jurisdiction': 'global', 'reason': 'Content License Test: The code and content can coexist, as CC-BY-SA 4.0 is one-way compatible with GPLv3'},
        {'lic_parent': 'MIT', 'lic_child': 'JSON', 'label': 'incompatible', 'jurisdiction': 'global', 'reason': 'Ambiguous License: The Good, not Evil use restriction makes the JSON license non-free'},
        {'lic_parent': 'EUPL-1.2', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'eu', 'reason': 'International License: The EUPL is designed for interoperability with GPL'}
    ]
    truth_df = pd.DataFrame(golden_truth_data)
    flips = []

    for index, row in truth_df.iterrows():
        lic1, lic2 = row['lic_parent'], row['lic_child']
        
        # Get the verdict for the 'global' jurisdiction
        global_verdict = evaluate_license_pair(lic1, lic2, 'global')
        
        # Get verdicts for all other jurisdictions and check for flips
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

    total_pairs = len(truth_df)
    flip_count = len(flips)
    flip_rate = (flip_count / total_pairs) if total_pairs > 0 else 0

    print(f"\\n--- Jurisdiction Flip Rate Report ---")
    print(f"Found {flip_count} instances of flipped verdicts across {total_pairs} pairs.")
    print(f"Overall Flip Rate: {flip_rate:.1%}\\n")

    if flips:
        flips_df = pd.DataFrame(flips)
        print("Details of Flipped Pairs:")
        print(flips_df.to_markdown(index=False))

if __name__ == "__main__":
    # You must paste your full `golden_truth_data` list into the script.
    # The list is omitted here for brevity.
    run_jurisdiction_experiment()