# In licensync/core/prolog_interface.py

from __future__ import annotations
import subprocess
from pathlib import Path
from typing import List
from pyswip import Prolog

# Import the corrected normalizer
from .license_utils import normalize_license

# ───────────────────────────────────────────────────────────────
#  Load rules.pl once per Python interpreter
# ───────────────────────────────────────────────────────────────
PROLOG_FILE: Path = (
    Path(__file__).resolve().parent.parent / "prolog_rules" / "rules.pl"
).resolve()

prolog = Prolog()
prolog.consult(str(PROLOG_FILE))

# ───────────────────────────────────────────────────────────────
#  Helpers
# ───────────────────────────────────────────────────────────────
def _atom(s: str) -> str:
    """Return a lowercase Prolog atom, quoted if it contains a dash or needs quoting."""
    # This function should only be called AFTER normalization
    a = s.lower()
    # Only quote if it's not a simple alphanumeric atom
    return f"'{a}'" if not a.isalnum() else a

# ───────────────────────────────────────────────────────────────
#  Public API
# ───────────────────────────────────────────────────────────────
def evaluate_license_pair(lic1: str, lic2: str, juris: str) -> dict:
    """
    Calls SWI-Prolog to evaluate a pair of licenses.
    Returns a dictionary with 'result' and 'risk'.
    """
    norm_lic1 = normalize_license(lic1)
    norm_lic2 = normalize_license(lic2)
    norm_juris = normalize_license(juris)

    l1 = _atom(norm_lic1)
    l2 = _atom(norm_lic2)
    j  = _atom(norm_juris)
    
    # NEW QUERY: Calls evaluate_pair/5 and formats the output as "result,risk"
    query = f"evaluate_pair({l1},{l2},{j},Result,Risk), format('~w,~w', [Result, Risk]), halt."

    command = ["swipl", "-q", "-s", str(PROLOG_FILE), "-g", query]
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if proc.returncode != 0:
            return {"result": f"Error: {proc.stderr.strip()}", "risk": "undefined"}
        
        # Parse the "result,risk" output string
        output = proc.stdout.strip().split(',')
        if len(output) == 2:
            return {"result": output[0], "risk": output[1]}
        else:
            return {"result": "unknown_license", "risk": "undefined"}

    except Exception as e:
        return {"result": f"Error: {e}", "risk": "undefined"}


def obligations_for_license(lic: str, jur: str) -> List[str]:
    """Queries Prolog for the obligations of a given license."""
    norm_lic = normalize_license(lic)
    norm_jur = normalize_license(jur)
    q = f"evaluate_license_obligations({_atom(norm_lic)},{_atom(norm_jur)},O)."
    try:
        rows = list(prolog.query(q))
        return [str(o) for o in rows[0]["O"]] if rows else []
    except Exception:
        return []

def get_risk_level(lic1: str, lic2: str, juris: str) -> str:
    """
    Call SWI-Prolog to get the jurisdiction-specific risk level.
    Returns: "low" | "high" | "unknown"
    """
    l1 = _atom(lic1)
    l2 = _atom(lic2)
    j  = _atom(juris)

    query = f"risk_level({l1},{l2},{j},Result)."
    try:
        # Use the existing prolog instance for speed
        rows = list(prolog.query(query))
        return str(rows[0]["Result"]) if rows else "unknown"
    except Exception:
        return "unknown"
    
def verdict_and_obligs(lic1: str, lic2: str, jur: str):
    """Utility to get the verdict and obligations for two licenses."""
    # This function calls the other functions already in your file.
    response = evaluate_license_pair(lic1, lic2, jur)
    verdict = response.get("result", "unknown_license")
    ob1 = obligations_for_license(lic1, jur)
    ob2 = obligations_for_license(lic2, jur)
    return verdict, ob1, ob2