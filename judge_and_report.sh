#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_DIR}"

DISABLE_PROXY="${DISABLE_PROXY:-1}"
if [[ "${DISABLE_PROXY}" == "1" ]]; then
  unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
fi

CONFIG="${CONFIG:-configs/finance_eval_public_v2.json}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o}"
JUDGE_WORKERS="${JUDGE_WORKERS:-4}"
JUDGE_LIMIT="${JUDGE_LIMIT:-0}"     # 0 means all rows
PYTHON_BIN="${PYTHON_BIN:-python}"
OVERWRITE="${OVERWRITE:-0}"    # 1 deletes old judgement/badcase files; 0 resumes judgement
MODELS="${MODELS:-qwen3_4b_instruct llama31_8b_instruct mistral_7b_instruct llama2_7b_chathf}"

SUMMARY_ARGS=()

run_one() {
  local model_name="$1"
  local responses="data/responses/${model_name}_v2_responses.jsonl"
  local judgements="data/judgements/${model_name}_v2_judgements.jsonl"
  local summary="reports/${model_name}_v2_summary.json"
  local report="reports/${model_name}_v2_report.md"
  local badcases="reports/${model_name}_v2_badcases.jsonl"
  local badcases_md="reports/${model_name}_v2_badcases.md"

  if [[ ! -f "${responses}" ]]; then
    echo "[skip] missing responses: ${responses}" >&2
    return
  fi

  local overwrite_args=()
  if [[ "${OVERWRITE}" == "1" ]]; then
    overwrite_args+=(--overwrite)
  fi

  local limit_args=()
  if [[ "${JUDGE_LIMIT}" != "0" ]]; then
    limit_args+=(--limit "${JUDGE_LIMIT}")
  fi

  echo "[judge] model=${model_name} judge=${JUDGE_MODEL} workers=${JUDGE_WORKERS}"
  "${PYTHON_BIN}" scripts/judge.py \
    --config "${CONFIG}" \
    --responses-path "${responses}" \
    --judgements-path "${judgements}" \
    --judge-model "${JUDGE_MODEL}" \
    --workers "${JUDGE_WORKERS}" \
    "${limit_args[@]}" \
    "${overwrite_args[@]}"

  echo "[summary] model=${model_name}"
  "${PYTHON_BIN}" scripts/summarize.py \
    --config "${CONFIG}" \
    --judgements-path "${judgements}" \
    --summary-path "${summary}" \
    --report-path "${report}"

  echo "[badcases] model=${model_name}"
  "${PYTHON_BIN}" scripts/analyze_badcases.py \
    --config "${CONFIG}" \
    --judgements-path "${judgements}" \
    --badcase-path "${badcases}" \
    --markdown-path "${badcases_md}" \
    --overwrite

  SUMMARY_ARGS+=(--summary "${model_name}=${summary}")
}

for model in ${MODELS}; do
  run_one "${model}"
done

if [[ ${#SUMMARY_ARGS[@]} -gt 0 ]]; then
  echo "[compare] ${MODELS}"
  "${PYTHON_BIN}" scripts/compare_models.py \
    "${SUMMARY_ARGS[@]}" \
    --output-json reports/local_model_comparison_v2.json \
    --output-md reports/local_model_comparison_v2.md
fi
