# LicenSync Experiment Harness (Quick Start)

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Build graphs (needs GitHub token)
```bash
export GITHUB_TOKEN=YOUR_TOKEN
make graphs         # writes CSVs under data/edges/ and data/nodes/
```

## Label ground truth
Edit `data/edge_truth.csv` and add rows:
```
repo,sha,parent,child,lic_parent,lic_child,jurisdiction,label
apache/airflow,9b1c...,apache/airflow,Flask,Apache-2.0,BSD-3-Clause,US,compatible
...
```

## Evaluate vs baseline
```bash
make eval           # writes results/eval_summary.json
```

## Benchmark performance
```bash
make perf           # writes results/perf.json
```

## Make simple figures
```bash
make figs           # writes figs/f1_bar.png and figs/perf_bar.png
```

Notes:
- `scripts/eval_edges.py` will automatically use `licensync.prolog_interface.evaluate_license_pair` if available.
- Baseline table lives at `data/baselines/spdx_matrix_min.csv` (extend as needed).
- SBOM retrieval retries when GitHub returns 202; falls back to `requirements.txt` and `package.json` at repo root.
```