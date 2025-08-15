# In licensync/scripts/parse_scancode_verdicts.py

import json
import csv
from licensync.core.license_utils import normalize_license

def parse_scancode_report(scancode_json_path, output_csv_path):
    """
    Parses a Scancode JSON report to extract dependency relationships and licenses.
    NOTE: This is a simplified example. Scancode does not explicitly state
    compatibility verdicts, so we infer them based on the licenses it finds.
    For this example, we assume any two identified licenses are 'compatible'.
    """
    print(f"Parsing {scancode_json_path}...")
    
    with open(scancode_json_path, 'r') as f:
        data = json.load(f)

    results = []
    # Find the main package file to act as the 'parent'
    for file_info in data.get('files', []):
        if file_info['path'].endswith('pyproject.toml'):
            parent_licenses = [normalize_license(lic['spdx_license_key']) for lic in file_info.get('licenses', [])]
            parent_license = parent_licenses[0] if parent_licenses else 'unknown'

            # Find package dependencies declared in this file
            for pkg in file_info.get('packages', []):
                child_license_str = pkg.get('declared_license_expression', 'unknown')
                child_license = normalize_license(child_license_str)
                
                # Baseline Verdict: For this example, we'll make a simple assumption.
                # A more advanced parser would need its own logic engine.
                verdict = "compatible" if parent_license != 'unknown' and child_license != 'unknown' else "unknown"

                results.append({
                    'lic_parent': parent_license,
                    'lic_child': child_license,
                    'prediction': verdict
                })

    # Save the baseline's verdicts to a CSV file
    with open(output_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['lic_parent', 'lic_child', 'prediction'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✅ Wrote {len(results)} baseline verdicts to {output_csv_path}")

if __name__ == '__main__':
    # Define the input Scancode report and the output CSV path
    scancode_file = 'licensync/data/scancode-results/scancode-flask.json'
    output_file = 'licensync/data/baseline_scancode.csv'
    parse_scancode_report(scancode_file, output_file)