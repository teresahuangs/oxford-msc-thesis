import subprocess
import os
from pathlib import Path
from pyswip import Prolog

# Path to rules.pl  ⇣ make sure this is a Path, not str
PROLOG_FILE = (
    Path(__file__).resolve().parent / ".." / "prolog_rules" / "rules.pl"
).resolve()

prolog = Prolog()
prolog.consult(str(PROLOG_FILE))   # turn Path → str only at consult time


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


def obligations_for_license(lic: str, juris: str):
    """
    Return a Python list of obligation atoms for (license, jurisdiction).
    """
    query = f"evaluate_license_obligations({lic}, {juris}, O)."
    results = list(prolog.query(query))
    if not results:
        return ["unknown"]
    # O is a Prolog list; convert to Python list of strings
    return [str(item) for item in results[0]["O"]]
