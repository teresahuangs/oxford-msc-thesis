.PHONY: setup graphs eval perf figs

PYTHON ?= python3
TOKEN ?= $(GITHUB_TOKEN)

setup:
	$(PYTHON) -m pip install -r requirements.txt

graphs:
	$(PYTHON) scripts/build_graph.py --repos-file data/repos.csv --token "$(TOKEN)"

eval:
	$(PYTHON) scripts/eval_edges.py --truth data/edge_truth.csv --out results/eval_summary.json

perf:
	$(PYTHON) scripts/benchmark_runtime.py --edges-dir data/edges --out results/perf.json

figs:
	$(PYTHON) scripts/plotting.py --eval results/eval_summary.json --perf results/perf.json --outdir figs
