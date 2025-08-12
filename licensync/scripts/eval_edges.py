#!/usr/bin/env python3
import argparse, csv, json, random
from pathlib import Path
from typing import Dict, Tuple, List, Optional
import pandas as pd
from licensync.core.prolog_interface import evaluate_license_pair


def baseline_from_csv(path: Path):
    tbl = {}
    if path.exists():
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            k = (str(row["lic_parent"]).strip(), str(row["lic_child"]).strip())
            tbl[k] = bool(int(row["ok"]))
    return tbl

def spdx_matrix_ok(lic_parent: str, lic_child: str, tbl: Dict[Tuple[str,str], bool]) -> bool:
    return tbl.get((lic_parent, lic_child), True)  # default permissive

def f1_from_counts(tp, fp, fn):
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec) else 0.0
    return prec, rec, f1

def bootstrap_f1(samples, n_boot=1000, seed=42):
    rng = random.Random(seed)
    scores = []
    for _ in range(n_boot):
        tp=fp=fn=0
        for (y_true, y_pred) in (samples[rng.randrange(len(samples))] for _ in range(len(samples))):
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
    ap = argparse.ArgumentParser(description="Evaluate edge-level compatibility vs. ground truth")
    ap.add_argument("--truth", default="data/edge_truth.csv")
    ap.add_argument("--jurisdiction", default="US")
    ap.add_argument("--baseline-matrix", default="data/baselines/spdx_matrix_min.csv")
    ap.add_argument("--out", default="results/eval_summary.json")
    args = ap.parse_args()

    eval_fn = _import_licensync()
    if eval_fn is None:
        print("[warn] Could not import licensync.prolog_interface.evaluate_license_pair; using a stub that returns True.")
        def eval_fn(lic_p, lic_c, juris): return True  # type: ignore

    base_tbl = baseline_from_csv(Path(args.baseline_matrix))

    truth = []
    with open(args.truth) as f:
        for row in csv.DictReader((r for r in f if not r.startswith("#"))):
            y = str(row["label"]).strip().lower() == "compatible"
            # prefer explicit lic strings if present
            lic_p = (row.get("lic_parent") or "").strip() or "unknown"
            lic_c = (row.get("lic_child") or "").strip() or "unknown"
            juris = (row.get("jurisdiction") or args.jurisdiction).strip()
            truth.append((y, lic_p, lic_c, juris))

    # paired evaluation
    l_tp=l_fp=l_fn=0
    b_tp=b_fp=b_fn=0
    b01=b10=0
    samples_L=[]; samples_B=[]

    for y, lic_p, lic_c, juris in truth:
        yL = bool(eval_fn(lic_p, lic_c, juris))
        yB = bool(spdx_matrix_ok(lic_p, lic_c, base_tbl))

        if yL and y: l_tp+=1
        elif yL and not y: l_fp+=1
        elif (not yL) and y: l_fn+=1
        samples_L.append((y, yL))

        if yB and y: b_tp+=1
        elif yB and not y: b_fp+=1
        elif (not yB) and y: b_fn+=1
        samples_B.append((y, yB))

        if yL != yB:
            if yL == y: b01 += 1
            else: b10 += 1

    l_prec, l_rec, l_f1 = f1_from_counts(l_tp, l_fp, l_fn)
    b_prec, b_rec, b_f1 = f1_from_counts(b_tp, b_fp, b_fn)
    l_med, l_lo, l_hi = bootstrap_f1(samples_L)
    b_med, b_lo, b_hi = bootstrap_f1(samples_B)
    pval = mcnemar(b01, b10)

    summary = {
        "licensync": {"precision": l_prec, "recall": l_rec, "f1": l_f1, "ci95": [l_lo, l_hi]},
        "baseline":  {"precision": b_prec, "recall": b_rec, "f1": b_f1, "ci95": [b_lo, b_hi]},
        "delta_f1": l_f1 - b_f1,
        "mcnemar": {"b01": b01, "b10": b10, "p": pval},
        "n": len(truth)
    }
    print(json.dumps(summary, indent=2))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
