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
def evaluate_license_pair(lic1: str, lic2: str, juris: str) -> str:
    """
    Calls SWI-Prolog to evaluate a pair of licenses.
    """
    # CORRECTLY normalize the license strings first.
    norm_lic1 = normalize_license(lic1)
    norm_lic2 = normalize_license(lic2)
    norm_juris = normalize_license(juris)

    # Convert the clean, normalized strings into Prolog atoms.
    l1 = _atom(norm_lic1)
    l2 = _atom(norm_lic2)
    j  = _atom(norm_juris)
    
    # This print statement is left for final verification
    print(f"[DEBUG] Correctly Normalized Atoms: l1={l1}, l2={l2}")

    query = f"evaluate_pair({l1},{l2},{j},Result),write(Result),halt."

    # Use a fresh Prolog process for safety in evaluation
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
            return f"Error: Prolog Stderr: {proc.stderr.strip()}"
        return proc.stdout.strip()
    except FileNotFoundError:
        return "Error: swipl_not_found"
    except Exception as e:
        return f"Error: {e}"

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