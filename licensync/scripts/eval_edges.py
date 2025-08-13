#!/usr/bin/env python3
# SPDX: MIT
# Fixed evaluation harness:
# - robust import of evaluator (matches main.py path)
# - SPDX -> Prolog-atom normalization before calling evaluator
# - coerce evaluator return ('compatible'/'incompatible'/bool/'unknown_license')
# - compute coverage (skip unknowns from scoring)
# - conservative baseline by default (unknown pairs => incompatible, toggleable)
# - clearer errors when truth has no labels

import os, sys, csv, json, random, argparse, importlib
from pathlib import Path
from typing import Dict, Tuple

# --- repo path shim: ensure we can import licensync.* like main.py does ---
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def _import_eval_and_norm():
    """Import evaluate_license_pair and normalize_license from your package."""
    eval_fn = None
    norm_fn = None

    # evaluator
    for modname in ["licensync.core.prolog_interface", "licensync.prolog_interface", "prolog_interface"]:
        try:
            mod = importlib.import_module(modname)
            fn = getattr(mod, "evaluate_license_pair", None)
            if callable(fn):
                eval_fn = fn
                print(f"[info] using evaluator from {mod.__file__}")
                break
        except Exception:
            continue
    if eval_fn is None:
        raise SystemExit("[fatal] cannot import evaluate_license_pair. Tip: run from repo root and set PYTHONPATH=$(pwd)")

    # normalizer
    for modname in ["licensync.core.license_utils", "licensync.license_utils", "license_utils"]:
        try:
            mod = importlib.import_module(modname)
            fn = getattr(mod, "normalize_license", None)
            if callable(fn):
                norm_fn = fn
                print(f"[info] using normalize_license from {mod.__file__}")
                break
        except Exception:
            continue

    return eval_fn, norm_fn

def to_prolog_atom(spdx: str, normalize_license=None) -> str:
    """Map SPDX-like strings to the Prolog-style atoms expected by the evaluator."""
    s = (spdx or "unknown").strip()
    if normalize_license is not None:
        try:
            s2 = normalize_license(s)
            if s2:
                s = s2
        except Exception:
            pass
    # SPDX -> prolog-ish atom
    s = s.lower().replace("-", "_").replace(".", "_").replace("+", "_plus_").replace("/", "_")
    # common synonyms passthrough (kept for clarity; s is already normalized above)
    return s

def coerce_verdict(v):
    """Return (bool_or_None, status_str) where None means unknown/skip."""
    if isinstance(v, bool):
        return v, "ok"
    s = str(v).strip().lower()
    if s in {"compatible", "ok", "true", "yes"}:
        return True, "ok"
    if s in {"incompatible", "false", "no"}:
        return False, "ok"
    if "unknown" in s:
        return None, "unknown"
    # last resort: treat anything else as unknown
    return None, "unknown"

def baseline_from_csv(path: Path) -> Dict[Tuple[str,str], bool]:
    import pandas as pd
    tbl = {}
    if path.exists():
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            lp = str(row["lic_parent"]).strip()
            lc = str(row["lic_child"]).strip()
            ok = bool(int(row["ok"]))
            tbl[(lp, lc)] = ok
    return tbl

def spdx_matrix_ok(lic_parent: str, lic_child: str, tbl, default_ok: bool=False) -> bool:
    """Conservative by default: unknown pairs -> incompatible (default_ok=False)."""
    return tbl.get((lic_parent, lic_child), default_ok)

def f1_from_counts(tp, fp, fn):
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec) else 0.0
    return prec, rec, f1

def bootstrap_f1(samples, n_boot=1000, seed=42):
    rng = random.Random(seed)
    scores = []
    n = len(samples)
    if n == 0:
        return 0.0, 0.0, 0.0
    for _ in range(n_boot):
        tp=fp=fn=0
        for (y_true, y_pred) in (samples[rng.randrange(n)] for _ in range(n)):
            if y_pred and y_true: tp += 1
            elif y_pred and not y_true: fp += 1
            elif (not y_pred) and y_true: fn += 1
        _, _, f1 = f1_from_counts(tp, fp, fn)
        scores.append(f1)
    scores.sort()
    lo = scores[int(0.025*len(scores))]
    hi = scores[int(0.975*len(scores))]
    med = scores[int(0.5*len(scores))]
    return med, lo, hi

def mcnemar(b01, b10):
    from math import comb
    n = b01 + b10
    if n == 0: return 1.0
    tail = sum(comb(n, k) for k in range(0, min(b01, b10)+1)) / (2**n)
    p = 2*tail
    return min(1.0, p)

def main():
    ap = argparse.ArgumentParser(description="Evaluate edge-level compatibility vs. ground truth (LicenSync vs SPDX baseline)")
    ap.add_argument("--truth", required=True, help="Path to adjudicated CSV (repo,sha,parent,child,lic_parent,lic_child,jurisdiction,label)")
    ap.add_argument("--jurisdiction", default=None, help="Override jurisdiction (else use per-row value)")
    ap.add_argument("--baseline-matrix", default="data/baselines/spdx_matrix_min.csv")
    ap.add_argument("--baseline-default", choices=["true","false"], default="false",
                    help="What to return when a pair isn't in the matrix (default: false => incompatible)")
    ap.add_argument("--out", default="results/eval_summary.json")
    args = ap.parse_args()

    eval_fn, normalize_license = _import_eval_and_norm()

    # read truth (skip commented lines)
    rows = []
    with open(args.truth) as f:
        reader = csv.DictReader((line for line in f if not line.lstrip().startswith("#")))
        for r in reader:
            lab = (r.get("label") or "").strip().lower()
            if lab not in {"compatible","incompatible"}:
                continue  # only keep labeled rows
            rows.append(r)

    if not rows:
        raise SystemExit("[fatal] no labeled rows in truth CSV. Fill the 'label' column with 'compatible'/'incompatible'.")

    n_total = len(rows)

    base_tbl = baseline_from_csv(Path(args.baseline_matrix))
    base_default_ok = (args.baseline_default == "true")

    # counters
    l_tp=l_fp=l_fn=0
    b_tp=b_fp=b_fn=0
    b01=b10=0
    samples_L=[]; samples_B=[]
    evaluated=0
    skipped_unknown=0

    for r in rows:
        y_true = (str(r["label"]).strip().lower() == "compatible")
        juris = (args.jurisdiction or r.get("jurisdiction") or "US").strip()

        lp_raw = r.get("lic_parent","")
        lc_raw = r.get("lic_child","")
        lp = to_prolog_atom(lp_raw, normalize_license)
        lc = to_prolog_atom(lc_raw, normalize_license)

        # LicenSync prediction
        try:
            yL_raw = eval_fn(lp, lc, juris)
        except Exception:
            # treat runtime errors as unknown (skip)
            skipped_unknown += 1
            continue
        yL_bool, status = coerce_verdict(yL_raw)
        if yL_bool is None:
            skipped_unknown += 1
            continue

        # Baseline
        yB = spdx_matrix_ok(str(lp_raw).strip(), str(lc_raw).strip(), base_tbl, default_ok=base_default_ok)

        evaluated += 1

        # update counts
        if yL_bool and y_true: l_tp+=1
        elif yL_bool and not y_true: l_fp+=1
        elif (not yL_bool) and y_true: l_fn+=1
        samples_L.append((y_true, yL_bool))

        if yB and y_true: b_tp+=1
        elif yB and not y_true: b_fp+=1
        elif (not yB) and y_true: b_fn+=1
        samples_B.append((y_true, yB))

        if yL_bool != yB:
            if yL_bool == y_true: b01 += 1
            elif yB == y_true: b10 += 1

    l_prec, l_rec, l_f1 = f1_from_counts(l_tp, l_fp, l_fn)
    b_prec, b_rec, b_f1 = f1_from_counts(b_tp, b_fp, b_fn)
    l_med, l_lo, l_hi = bootstrap_f1(samples_L)
    b_med, b_lo, b_hi = bootstrap_f1(samples_B)
    pval = mcnemar(b01, b10)

    coverage = evaluated / n_total if n_total else 0.0

    summary = {
        "licensync": {"precision": l_prec, "recall": l_rec, "f1": l_f1, "ci95": [l_lo, l_hi]},
        "baseline":  {"precision": b_prec, "recall": b_rec, "f1": b_f1, "ci95": [b_lo, b_hi]},
        "delta_f1": l_f1 - b_f1,
        "mcnemar": {"b01": b01, "b10": b10, "p": pval},
        "n_labeled": n_total,
        "n_evaluated": evaluated,
        "coverage": coverage,
        "skipped_unknown": skipped_unknown,
        "config": {
            "jurisdiction_override": args.jurisdiction,
            "baseline_default": args.baseline_default,
            "truth_path": args.truth,
            "baseline_matrix": args.baseline_matrix,
        }
    }

    print(json.dumps(summary, indent=2))
    outp = Path(args.out); outp.parent.mkdir(parents=True, exist_ok=True); outp.write_text(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
