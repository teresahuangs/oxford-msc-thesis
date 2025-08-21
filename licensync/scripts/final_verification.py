#!/usr/bin/env python3
# In licensync/scripts/final_verification.py

import pandas as pd
from licensync.core.prolog_interface import evaluate_license_pair
from licensync.scripts.advanced_eval import calculate_metrics, bootstrap_f1_ci

def run_final_verification_with_comparison():
    """
    Runs a final, self-contained evaluation using the embedded "golden" dataset
    and compares LicenSync's accuracy against a pre-computed baseline file.
    """
    print("--- Running Final Verification with Baseline Comparison ---")

    golden_truth_data = [
        # (Your full list of 32 golden test cases goes here)
        {'lic_parent': 'MIT', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'ISC', 'lic_child': 'BSD-3-Clause', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'MPL-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'MIT', 'lic_child': 'LGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'MIT', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'MPL-2.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'LGPL-3.0-only', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'global'},
        {'lic_parent': 'GPL-2.0-only', 'lic_child': 'Apache-2.0', 'label': 'incompatible', 'jurisdiction': 'global'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'MIT', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'SSPL-1.0', 'label': 'incompatible', 'jurisdiction': 'eu'},
        {'lic_parent': 'MIT', 'lic_child': 'Commons-Clause', 'label': 'incompatible', 'jurisdiction': 'us'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'CC-BY-NC-SA-4.0', 'label': 'incompatible', 'jurisdiction': 'global'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'Confluent-Community-1.0', 'label': 'incompatible', 'jurisdiction': 'global'},
        {'lic_parent': 'EPL-2.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'MIT', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'global'},
        {'lic_parent': 'CC0-1.0', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'Unlicense', 'lic_child': 'AGPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'Elastic-License-2.0', 'label': 'incompatible', 'jurisdiction': 'us'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'compatible', 'jurisdiction': 'us'},
        {'lic_parent': 'Apache-2.0', 'lic_child': 'GPL-2.0-only', 'label': 'incompatible', 'jurisdiction': 'eu'},
        {'lic_parent': 'GPL-2.0-with-classpath-exception', 'lic_child': 'Apache-2.0', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'MIT', 'lic_child': 'BSL-1.1', 'label': 'incompatible', 'jurisdiction': 'global'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'ODbL-1.0', 'label': 'incompatible', 'jurisdiction': 'global'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'CC-BY-SA-4.0', 'label': 'compatible', 'jurisdiction': 'global'},
        {'lic_parent': 'MIT', 'lic_child': 'JSON', 'label': 'incompatible', 'jurisdiction': 'global'},
        {'lic_parent': 'EUPL-1.2', 'lic_child': 'GPL-3.0-only', 'label': 'compatible', 'jurisdiction': 'eu'},
        {'lic_parent': 'GPL-3.0-only', 'lic_child': 'MIT', 'label': 'incompatible', 'jurisdiction': 'de'},
    ]
    truth_df = pd.DataFrame(golden_truth_data)
    y_true = (truth_df["label"].str.lower() == "compatible").tolist()

    # --- Load Baseline Data ---
    baseline_path = "licensync/data/baseline_scancode.csv"
    baseline_loaded = False
    try:
        baseline_df = pd.read_csv(baseline_path)
        print(f"Successfully loaded {len(baseline_df)} verdicts from {baseline_path}")
        baseline_loaded = True
    except FileNotFoundError:
        print(f"Warning: Baseline file not found at {baseline_path}. Skipping comparison.")
        baseline_df = pd.DataFrame() # Create an empty df as a placeholder

    # --- Get Predictions for LicenSync ---
    licensync_preds = []
    licensync_risks = []
    for _, row in truth_df.iterrows():
        response = evaluate_license_pair(row["lic_parent"], row["lic_child"], row["jurisdiction"])
        verdict = response.get("result", "unknown_license")
        risk = response.get("risk", "undefined")
        licensync_risks.append(risk.capitalize())
        
        if "incompatible" in verdict: licensync_preds.append(False)
        elif verdict == "ok": licensync_preds.append(True)
        else: licensync_preds.append(None)

    # --- Calculate LicenSync Metrics ---
    licensync_metrics = calculate_metrics(y_true, licensync_preds)
    _, ls_f1_low, ls_f1_high = bootstrap_f1_ci(y_true, licensync_preds)
    
    # --- Build the results data ---
    results_data = [{
        "Tool": "LicenSync",
        "Precision": f"{licensync_metrics['precision']:.3f}",
        "Recall": f"{licensync_metrics['recall']:.3f}",
        "F1": f"{licensync_metrics['f1']:.3f}",
        "F1 95% CI": f"[{ls_f1_low:.3f}, {ls_f1_high:.3f}]",
        "Coverage": f"{licensync_metrics['coverage']:.1%}",
    }]

    # --- Get Predictions and Metrics for Baseline ONLY IF LOADED ---
    if baseline_loaded:
        baseline_preds = []
        for _, row in truth_df.iterrows():
            match = baseline_df[
                (baseline_df['lic_parent'] == row['lic_parent']) &
                (baseline_df['lic_child'] == row['lic_child'])
            ]
            if not match.empty:
                prediction_str = match.iloc[0]['prediction']
                baseline_preds.append(prediction_str == 'compatible')
            else:
                baseline_preds.append(None)
        
        baseline_metrics = calculate_metrics(y_true, baseline_preds)
        _, b_f1_low, b_f1_high = bootstrap_f1_ci(y_true, baseline_preds)
        
        results_data.append({
            "Tool": "Scancode", # Or whatever your baseline is
            "Precision": f"{baseline_metrics['precision']:.3f}",
            "Recall": f"{baseline_metrics['recall']:.3f}",
            "F1": f"{baseline_metrics['f1']:.3f}",
            "F1 95% CI": f"[{b_f1_low:.3f}, {b_f1_high:.3f}]",
            "Coverage": f"{baseline_metrics['coverage']:.1%}",
        })

    # --- Print Final Report ---
    results_df = pd.DataFrame(results_data)
    print("\\n--- Final Accuracy Report (vs. Golden Dataset) ---")
    print(results_df.to_markdown(index=False))

if __name__ == "__main__":
    run_final_verification_with_comparison()