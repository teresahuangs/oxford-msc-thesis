#!/usr/bin/env bash
set -euo pipefail
# Usage: scripts/baselines/run_scancode.sh <repo_dir> <out_dir>
repo_dir="${1:-}"
out_dir="${2:-baselines/scancode}"
if [[ -z "$repo_dir" ]]; then echo "usage: $0 <repo_dir> [out_dir]"; exit 1; fi
mkdir -p "$out_dir"
name="$(basename "$repo_dir" | tr ':' '_' | tr '/' '_')"
out="$out_dir/${name}.spdx.json"
docker run --rm -v "${repo_dir}:/scan:ro" -v "$(pwd)/${out_dir}:/out" aboutcode/scancode-toolkit:latest   scancode -l --spdx-json "/out/${name}.spdx.json" "/scan"
echo "[ok] scancode SPDX written to ${out}"
