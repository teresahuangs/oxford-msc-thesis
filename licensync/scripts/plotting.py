#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser(description="Plot simple result charts from eval summary/perf")
    ap.add_argument("--eval", default="results/eval_summary.json")
    ap.add_argument("--perf", default="results/perf.json")
    ap.add_argument("--outdir", default="figs")
    args = ap.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)

    # F1 bar
    evalj = json.loads(Path(args.eval).read_text())
    fig = plt.figure()
    xs = ["Baseline", "LicenSync"]
    ys = [evalj["baseline"]["f1"], evalj["licensync"]["f1"]]
    plt.bar(xs, ys)
    plt.title("Edge-level F1")
    plt.ylabel("F1")
    plt.savefig(Path(args.outdir)/"f1_bar.png", dpi=200)

    # Perf bar
    perfj = json.loads(Path(args.perf).read_text())
    fig = plt.figure()
    xs = ["Edges", "Seconds"]
    ys = [perfj.get("edges", 0), perfj.get("seconds", 0.0)]
    plt.bar(xs, ys)
    plt.title("Performance (total edges & seconds)")
    plt.savefig(Path(args.outdir)/"perf_bar.png", dpi=200)

if __name__ == "__main__":
    main()
