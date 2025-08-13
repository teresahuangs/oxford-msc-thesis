#!/usr/bin/env python3
# In licensync/scripts/final_verification.py

import pandas as pd
from licensync.core.prolog_interface import evaluate_license_pair
from licensync.scripts.advanced_eval import calculate_metrics, bootstrap_f1_ci # Re-use our metric functions

def run_final_verification():
    """
    Runs a final, self-contained evaluation using an embedded "golden" ground truth dataset.
    This bypasses any issues with external CSV files.
    """
    print("--- Running Final Verification with Embedded Golden Dataset ---")

    # The complete, clean, "golden" ground truth dataset
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
    y_true = (truth_df["label"].str.lower() == "compatible").tolist()
    
    # Get LicenSync predictions
    licensync_preds = []
    for _, row in truth_df.iterrows():
        res = evaluate_license_pair(row["lic_parent"], row["lic_child"], row["jurisdiction"])
        if "incompatible" in res:
            licensync_preds.append(False)
        elif res == "ok":
            licensync_preds.append(True)
        else:
            licensync_preds.append(None) # Handle 'unknown' or errors

    # Calculate final metrics
    metrics = calculate_metrics(y_true, licensync_preds)
    _, f1_low, f1_high = bootstrap_f1_ci(y_true, licensync_preds)

    # Build and print the final report table
    results_data = [{
        "Tool": "LicenSync",
        "Precision": f"{metrics['precision']:.3f}",
        "Recall": f"{metrics['recall']:.3f}",
        "F1": f"{metrics['f1']:.3f}",
        "F1 95% CI": f"[{f1_low:.3f}, {f1_high:.3f}]",
        "Coverage": f"{metrics['coverage']:.1%}",
    }]
    results_df = pd.DataFrame(results_data)
    
    print("\\n--- Final Evaluation Report ---")
    print("Based on the embedded 'golden' dataset.\\n")
    print(results_df.to_markdown(index=False))

if __name__ == "__main__":
    run_final_verification()