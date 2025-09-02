# In licensync/core/prolog_interface.py

from __future__ import annotations
import subprocess
import re
from pathlib import Path
from typing import List, Dict
from pyswip import Prolog

from .license_utils import normalize_license

PROLOG_FILE: Path = (
    Path(__file__).resolve().parent.parent / "prolog_rules" / "rules.pl"
).resolve()

prolog = Prolog()
try:
    prolog.consult(str(PROLOG_FILE))
except Exception as e:
    print(f"FATAL: Could not consult Prolog rules file at {PROLOG_FILE}. Error: {e}")

def _atom(s: str) -> str:
    """Returns a string formatted as a valid Prolog atom."""
    if re.match(r"^[a-z][a-zA-Z0-9_]*$", s):
        return s
    else:
        return f"'{s}'"

def evaluate_license_pair(lic1: str, lic2: str, juris: str) -> Dict[str, str]:
    """Calls SWI-Prolog to evaluate a pair of licenses."""
    norm_lic1 = normalize_license(lic1)
    norm_lic2 = normalize_license(lic2)
    norm_juris = normalize_license(juris)
    l1 = _atom(norm_lic1)
    l2 = _atom(norm_lic2)
    j  = _atom(norm_juris)
    
    query = f"evaluate_pair({l1},{l2},{j},Result,Risk), format('~w,~w', [Result, Risk]), halt."
    command = ["swipl", "-q", "-s", str(PROLOG_FILE), "-g", query]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            return {"result": f"Error: {proc.stderr.strip()}", "risk": "undefined"}
        output = proc.stdout.strip().split(',')
        return {"result": output[0], "risk": output[1]} if len(output) == 2 else {"result": "unknown_license", "risk": "undefined"}
    except Exception as e:
        return {"result": f"Error: {e}", "risk": "undefined"}

def obligations_for_license(lic: str, jur: str) -> List[str]:
    """Queries Prolog for the obligations of a given license."""
    norm_lic = normalize_license(lic)
    norm_jur = normalize_license(jur)  # Also normalize the jurisdiction

    q = f"obligation({_atom(norm_lic)}, {_atom(norm_jur)}, Obligation)."

    try:
        rows = list(prolog.query(q))
        return sorted([str(row["Obligation"]) for row in rows]) if rows else []
    except Exception:
        return []

def verdict_and_obligs(lic1: str, lic2: str, jur: str):
    """Utility to get the verdict and obligations for two licenses."""
    response = evaluate_license_pair(lic1, lic2, jur)
    verdict = response.get("result", "unknown_license")
    ob1 = obligations_for_license(lic1, jur)
    ob2 = obligations_for_license(lic2, jur)
    return verdict, ob1, ob2