#!/usr/bin/env bash
set -euo pipefail
# Usage: scripts/baselines/run_syft.sh <repo_dir> <out_dir>
repo_dir="${1:-}"
out_dir="${2:-baselines/syft}"
if [[ -z "$repo_dir" ]]; then echo "usage: $0 <repo_dir> [out_dir]"; exit 1; fi
mkdir -p "$out_dir"
name="$(basename "$repo_dir" | tr ':' '_' | tr '/' '_')"
out="$out_dir/${name}.spdx.json"

if command -v syft >/dev/null 2>&1; then
  syft "dir:${repo_dir}" -o "spdx-json=${out}"
else
  docker run --rm -v "${repo_dir}:/work:ro" -v "$(pwd)/${out_dir}:/out" anchore/syft:latest     "dir:/work" -o "spdx-json=/out/${name}.spdx.json"
fi
echo "[ok] syft SPDX written to ${out}"
