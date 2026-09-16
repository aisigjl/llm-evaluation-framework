#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_JSON="${OUTPUT_JSON:-reports/all_model_comparison_v2.json}"
OUTPUT_MD="${OUTPUT_MD:-reports/all_model_comparison_v2.md}"

args=()
for path in reports/*_v2_summary.json; do
  [[ -f "${path}" ]] || continue
  if [[ "${path}" == *_api_v2_summary.json ]]; then
    continue
  fi
  name="$(basename "${path}" _v2_summary.json)"
  args+=(--summary "${name}=${path}")
done

for path in reports/*_api_v2_summary.json; do
  [[ -f "${path}" ]] || continue
  name="$(basename "${path}" _api_v2_summary.json)_api"
  args+=(--summary "${name}=${path}")
done

if [[ ${#args[@]} -eq 0 ]]; then
  echo "No summary files found under reports/." >&2
  exit 2
fi

"${PYTHON_BIN}" scripts/compare_models.py \
  "${args[@]}" \
  --output-json "${OUTPUT_JSON}" \
  --output-md "${OUTPUT_MD}"
