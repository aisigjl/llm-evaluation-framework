#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_DIR}"

CONFIG="${CONFIG:-configs/finance_eval_public_v2.json}"
PYTHON_BIN="${PYTHON_BIN:-python}"
MODEL_WORKERS="${MODEL_WORKERS:-4}"
JUDGE_WORKERS="${JUDGE_WORKERS:-4}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o}"
LIMIT="${LIMIT:-0}"             # 0 means all rows
OVERWRITE="${OVERWRITE:-0}"     # 1 deletes old response/judgement files; 0 resumes
MAX_TOKENS="${MAX_TOKENS:-1024}"
JUDGE_MAX_TOKENS="${JUDGE_MAX_TOKENS:-1024}"

# Load MODEL_NAME from .env if it is not already exported.
if [[ -z "${MODEL_NAME:-}" && -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ -z "${MODEL_NAME:-}" ]]; then
  echo "MODEL_NAME is missing. Set it in .env or export MODEL_NAME=..." >&2
  exit 2
fi

MODEL_TAG="${MODEL_TAG:-$(printf '%s' "${MODEL_NAME}" | tr '/: .' '____')}"
RESPONSES="data/responses/${MODEL_TAG}_api_v2_responses.jsonl"
JUDGEMENTS="data/judgements/${MODEL_TAG}_api_v2_judgements.jsonl"
SUMMARY="reports/${MODEL_TAG}_api_v2_summary.json"
REPORT="reports/${MODEL_TAG}_api_v2_report.md"
BADCASES="reports/${MODEL_TAG}_api_v2_badcases.jsonl"
BADCASES_MD="reports/${MODEL_TAG}_api_v2_badcases.md"

limit_args=()
if [[ "${LIMIT}" != "0" ]]; then
  limit_args+=(--limit "${LIMIT}")
fi

overwrite_args=()
if [[ "${OVERWRITE}" == "1" ]]; then
  overwrite_args+=(--overwrite)
fi

echo "[generate-api] model=${MODEL_NAME} tag=${MODEL_TAG} workers=${MODEL_WORKERS} limit=${LIMIT}"
"${PYTHON_BIN}" scripts/run_model.py \
  --config "${CONFIG}" \
  --responses-path "${RESPONSES}" \
  --model-name "${MODEL_NAME}" \
  --max-tokens "${MAX_TOKENS}" \
  --workers "${MODEL_WORKERS}" \
  "${limit_args[@]}" \
  "${overwrite_args[@]}"

echo "[judge] candidate=${MODEL_TAG} judge=${JUDGE_MODEL} workers=${JUDGE_WORKERS}"
"${PYTHON_BIN}" scripts/judge.py \
  --config "${CONFIG}" \
  --responses-path "${RESPONSES}" \
  --judgements-path "${JUDGEMENTS}" \
  --judge-model "${JUDGE_MODEL}" \
  --max-tokens "${JUDGE_MAX_TOKENS}" \
  --workers "${JUDGE_WORKERS}" \
  "${limit_args[@]}" \
  "${overwrite_args[@]}"

echo "[summary] candidate=${MODEL_TAG}"
"${PYTHON_BIN}" scripts/summarize.py \
  --config "${CONFIG}" \
  --judgements-path "${JUDGEMENTS}" \
  --summary-path "${SUMMARY}" \
  --report-path "${REPORT}"

echo "[badcases] candidate=${MODEL_TAG}"
"${PYTHON_BIN}" scripts/analyze_badcases.py \
  --config "${CONFIG}" \
  --judgements-path "${JUDGEMENTS}" \
  --badcase-path "${BADCASES}" \
  --markdown-path "${BADCASES_MD}" \
  --overwrite

cat <<EOF
[done]
responses:  ${RESPONSES}
judgements: ${JUDGEMENTS}
summary:    ${SUMMARY}
report:     ${REPORT}
badcases:   ${BADCASES_MD}
EOF
