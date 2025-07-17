import subprocess
import os

PROLOG_FILE = os.path.join(os.path.dirname(__file__), '../prolog_rules/rules.pl')

def evaluate_license_pair(license1, license2, jurisdiction):
    """
    Calls the Prolog engine to evaluate a license pair for compatibility.
    """
    query = f"evaluate_pair({license1}, {license2}, {jurisdiction}, Result), write(Result), halt."

    result = subprocess.run(
        ['swipl', '-q', '-s', PROLOG_FILE, '-g', query],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip()
