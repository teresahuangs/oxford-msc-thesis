#!/usr/bin/env python3
import argparse
import json
import random
import pandas as pd
from pathlib import Path
from licensync.core.prolog_interface import evaluate_license_pair, get_risk_level

# --- Core Metric Calculation Functions ---

def calculate_metrics(y_true: list, y_pred: list) -> dict:
    """Calculates precision, recall, F1, coverage, and raw counts."""
    tp = fp = fn = tn = 0
    known_predictions = 0

    for true, pred in zip(y_true, y_pred):
        if pred is not None:  # A prediction was made
            known_predictions += 1
            if pred and true: tp += 1
            elif pred and not true: fp += 1
            elif not pred and true: fn += 1
            elif not pred and not true: tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    coverage = known_predictions / len(y_true) if len(y_true) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "coverage": coverage,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }

def bootstrap_f1_ci(y_true: list, y_pred: list, n_boot: int = 1000, seed: int = 42) -> tuple:
    """Performs bootstrap resampling to get a 95% confidence interval for F1 score."""
    rng = random.Random(seed)
    scores = []
    
    # Filter out None predictions for bootstrapping samples
    samples = [(t, p) for t, p in zip(y_true, y_pred) if p is not None]
    if not samples:
        return 0.0, 0.0, 0.0

    for _ in range(n_boot):
        boot_samples = [rng.choice(samples) for _ in range(len(samples))]
        boot_true = [s[0] for s in boot_samples]
        boot_pred = [s[1] for s in boot_samples]
        metrics = calculate_metrics(boot_true, boot_pred)
        scores.append(metrics["f1"])

    scores.sort()
    low = scores[int(0.025 * len(scores))]
    high = scores[int(0.975 * len(scores))]
    median = scores[int(0.5 * len(scores))]
    return median, low, high

def mcnemar_test(y_pred1: list, y_pred2: list, y_true: list) -> dict:
    """Performs McNemar's test to compare two models."""
    from statsmodels.stats.contingency_tables import mcnemar
    
    # b = Model 1 is wrong, Model 2 is right
    # c = Model 1 is right, Model 2 is wrong
    b = c = 0
    for p1, p2, true in zip(y_pred1, y_pred2, y_true):
        if p1 is None or p2 is None: continue # Only compare where both have predictions
        err1 = (p1 != true)
        err2 = (p2 != true)
        if err1 and not err2:
            b += 1
        elif not err1 and err2:
            c += 1
            
    # Create the 2x2 contingency table for McNemar's test
    # [[a, b], [c, d]] where a=both correct, d=both incorrect
    table = [[0, b], [c, 0]] # We only need b and c
    result = mcnemar(table, exact=True)

    return {"statistic": result.statistic, "p_value": result.pvalue, "b_misclassified_by_1_only": b, "c_misclassified_by_2_only": c}

# --- Main Evaluation Logic ---

def main():
    parser = argparse.ArgumentParser(description="Generate a comprehensive evaluation report for LicenSync.")
    parser.add_argument("--truth", required=True, help="Path to ground truth CSV file (e.g., edge_truth_filled.csv)")
    parser.add_argument("--baselines", nargs='+', help="Paths to baseline CSV files (e.g., baseline_ort.csv baseline_spdx.csv)")
    parser.add_argument("--out_dir", default="results", help="Directory to save evaluation outputs")
    args = parser.parse_args()
    
    # Create output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    truth_df = pd.read_csv(args.truth)
    baselines = {Path(p).stem: pd.read_csv(p) for p in args.baselines or []}
    
    y_true = (truth_df["label"].str.lower() == "compatible").tolist()

    # 2. Get Predictions and Risk Levels for All Models
    predictions = {}
    risk_levels = [] # <-- ADD THIS
    
    # LicenSync predictions
    licensync_preds = []
    # In advanced_eval.py, inside the main LicenSync prediction loop

    for _, row in truth_df.iterrows():
        juris = row.get("jurisdiction", "global")
        lic_p_str = str(row["lic_parent"])
        lic_c_str = str(row["lic_child"])
        
        # --- Logic to handle compound licenses ---
        if ' OR ' in lic_p_str: lic_p_str = lic_p_str.split(' OR ')[0].strip('()')
        if ' OR ' in lic_c_str: lic_c_str = lic_c_str.split(' OR ')[0].strip('()')

        p_licenses = [p.strip() for p in lic_p_str.split(' AND ')]
        c_licenses = [c.strip() for c in lic_c_str.split(' AND ')]
        
        final_res = "ok" # Assume compatible until an incompatibility is found
        for p_lic in p_licenses:
            for c_lic in c_licenses:
                # For complex LicenseRef strings, we simplify by checking if 'MIT' is present
                if 'LicenseRef' in p_lic: p_lic = 'MIT' # Heuristic simplification
                if 'LicenseRef' in c_lic: c_lic = 'MIT' # Heuristic simplification

                res = evaluate_license_pair(p_lic, c_lic, juris)
                if "incompatible" in res:
                    final_res = "incompatible"
                    break
            if final_res == "incompatible":
                break
        
        # --- End of compound license logic ---

    if "incompatible" in final_res:
        licensync_preds.append(False)
    elif final_res == "ok":
        licensync_preds.append(True)
    else:
        licensync_preds.append(None)

    predictions["LicenSync"] = licensync_preds


    # Baseline predictions
    for name, df in baselines.items():
        # This assumes baseline CSVs are merged with the truth file on parent/child licenses
        # A more robust implementation would merge dataframes. This is a simplified approach.
        predictions[name] = (df["prediction"].str.lower() == "compatible").tolist()
        
    # 3. Calculate Metrics and Build Results Table
    results_data = []
    for name, y_pred in predictions.items():
        metrics = calculate_metrics(y_true, y_pred)
        _, f1_low, f1_high = bootstrap_f1_ci(y_true, y_pred)
        
        row_data = {
            "Tool": name,
            "Precision": f"{metrics['precision']:.3f}",
            "Recall": f"{metrics['recall']:.3f}",
            "F1": f"{metrics['f1']:.3f}",
            "F1 95% CI": f"[{f1_low:.3f}, {f1_high:.3f}]",
            "Coverage": f"{metrics['coverage']:.1%}",
        }
        # Add risk level info only for LicenSync <-- ADD THIS LOGIC
        if name == "LicenSync":
            # For simplicity, we'll just count high-risk assessments
            high_risk_count = risk_levels.count('High')
            row_data["High-Risk Pairs"] = f"{high_risk_count}"
        
        results_data.append(row_data)

    results_df = pd.DataFrame(results_data).fillna('') # Use fillna to clean up empty cells


    # 4. Perform Comparative Analysis (LicenSync vs. Baselines)
    comparisons = {}
    licensync_f1 = float(results_df[results_df["Tool"] == "LicenSync"]["F1"].iloc[0])
    
    for name in baselines.keys():
        baseline_f1 = float(results_df[results_df["Tool"] == name]["F1"].iloc[0])
        mcnemar_results = mcnemar_test(predictions["LicenSync"], predictions[name], y_true)
        comparisons[name] = {
            "delta_f1": licensync_f1 - baseline_f1,
            "mcnemar_p_value": mcnemar_results["p_value"]
        }

    # 5. Print and Save Report
    report = f"""
# Evaluation Report: LicenSync Performance Analysis

This report details the performance of LicenSync against established baselines using the ground truth data from `{args.truth}`.

---
## Core Performance Metrics

The following table summarizes the precision, recall, F1 score, and coverage for each tool. F1 scores are accompanied by a 95% confidence interval derived from bootstrap resampling.

{results_df.to_markdown(index=False)}

---
## Comparative Analysis

Here, we compare LicenSync directly against each baseline to assess accuracy improvement and statistical significance.

"""
    for name, comp_data in comparisons.items():
        f1_gain = f"{comp_data['delta_f1']:+.3f}"
        p_value = f"{comp_data['mcnemar_p_value']:.4f}"
        significance = "**(Statistically Significant)**" if comp_data['mcnemar_p_value'] < 0.05 else ""

        report += f"""
### LicenSync vs. {name}

- **F1 Score Improvement (ΔF1):** {f1_gain}
- **McNemar's Test p-value:** {p_value} {significance}
"""
    
    print(report)
    (out_dir / "evaluation_report.md").write_text(report)
    print(f"\\n✅ Report saved to {out_dir / 'evaluation_report.md'}")

if __name__ == "__main__":
    main()