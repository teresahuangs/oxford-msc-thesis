#!/usr/bin/env bash
set -euo pipefail
# Usage: scripts/baselines/run_ort.sh <repo_dir> <out_dir>
repo_dir="${1:-}"
out_dir="${2:-baselines/ort}"
if [[ -z "$repo_dir" ]]; then echo "usage: $0 <repo_dir> [out_dir]"; exit 1; fi
mkdir -p "$out_dir"
name="$(basename "$repo_dir" | tr ':' '_' | tr '/' '_')"
work="$(pwd)"
docker_image="ghcr.io/oss-review-toolkit/ort:latest"

mkdir -p "${out_dir}/${name}"
# Analyze
docker run --rm -u "$(id -u)" -v "${work}:/work" ${docker_image}   --info analyze -i "/work/${repo_dir}" -o "/work/${out_dir}/${name}"
# Scan
docker run --rm -u "$(id -u)" -v "${work}:/work" ${docker_image}   --info scan -i "/work/${out_dir}/${name}/analyzer-result.yml" -o "/work/${out_dir}/${name}"
# Evaluate
docker run --rm -u "$(id -u)" -v "${work}:/work" ${docker_image}   --info evaluate -i "/work/${out_dir}/${name}/scan-result.yml" -o "/work/${out_dir}/${name}"   --policy-rules "/work/policy/rules.kts"

echo "[ok] ORT results in ${out_dir}/${name}"
