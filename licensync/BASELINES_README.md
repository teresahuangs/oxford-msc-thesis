# LicenSync Baselines Bundle

This bundle contains wrappers for **Syft**, **ScanCode**, and **ORT**, plus aligners and a Makefile.

## Quick Start
```bash
# from your project root after unzipping
python3 -m pip install -r requirements_baselines.txt

# clone repos listed in data/repos.csv (format: owner/repo[,sha])
make -f Makefile.baselines baselines_clone

# run baselines
make -f Makefile.baselines syft
make -f Makefile.baselines scancode
make -f Makefile.baselines ort

# align outputs
make -f Makefile.baselines align_spdx
make -f Makefile.baselines align_ort

# evaluate
export PYTHONPATH="$(pwd)"
python3 -m licensync.scripts.eval_edges   --truth licensync/data/edge_truth_curated.csv   --baseline-matrix licensync/data/baselines/spdx_matrix_min.csv   --baseline-default false   --out licensync/results/eval_spdx.json

python3 -m licensync.scripts.eval_edges   --truth licensync/data/edge_truth_curated.csv   --baseline-matrix licensync/data/baselines/ort_pairs.csv   --baseline-default false   --out licensync/results/eval_ort.json
```
Notes:
- Syft uses local binary if available, else Docker. ScanCode and ORT run via Docker.
- Adjust `policy/rules.kts` to reflect your policy.
- Aligners write CSVs under `baselines/` and `licensync/data/baselines/`.
