from __future__ import annotations
import subprocess, os
from pathlib import Path
from typing import List
from pyswip import Prolog

# ───────────────────────────────────────────────────────────────
#  Load rules.pl once per Python interpreter
# ───────────────────────────────────────────────────────────────
PROLOG_FILE: Path = (
    Path(__file__).resolve().parent / ".." / "prolog_rules" / "rules.pl"
).resolve()

prolog = Prolog()
prolog.consult(str(PROLOG_FILE))          # consult needs a string path

# ───────────────────────────────────────────────────────────────
#  Helpers
# ───────────────────────────────────────────────────────────────
def _atom(s: str) -> str:
    """Return a lowercase Prolog atom, quoted if it contains a dash."""
    a = s.lower()
    return f"'{a}'" if "-" in a else a

# ───────────────────────────────────────────────────────────────
#  Public API
# ───────────────────────────────────────────────────────────────
def evaluate_license_pair(lic1: str, lic2: str, juris: str) -> str:
    """
    Call SWI-Prolog in a subprocess so we don’t pollute the shared engine
    with writes/halts.  Returns: "ok" | "incompatible" | "unknown_license"
    or "Error: …".
    """
    l1 = _atom(lic1)
    l2 = _atom(lic2)
    j  = _atom(juris)

    query = f"evaluate_pair({l1},{l2},{j},Result),write(Result),halt."

    proc = subprocess.run(
        ["swipl", "-q", "-s", str(PROLOG_FILE), "-g", query],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return f"Error: {proc.stderr.strip()}"
    return proc.stdout.strip()

# ------------------------------------------------------------------
#  Obligation helpers (stay inside embedded Prolog engine)
# ------------------------------------------------------------------
def obligations_for_license(lic: str, jur: str) -> List[str]:
    q = f"evaluate_license_obligations({_atom(lic)},{_atom(jur)},O)."
    rows = list(prolog.query(q))
    return [str(o) for o in rows[0]["O"]] if rows else []

def verdict_and_obligs(lic1: str, lic2: str, jur: str):
    """Utility used by CLI 'explain' command."""
    verdict = evaluate_license_pair(lic1, lic2, jur)
    ob1 = obligations_for_license(lic1, jur)
    ob2 = obligations_for_license(lic2, jur)
    return verdict, ob1, ob2
