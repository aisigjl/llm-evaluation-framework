#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_DIR}"

GPU_ID="${GPU_ID:-1}"
CONFIG="${CONFIG:-configs/finance_eval_public_v2.json}"
MODE="${MODE:-smoke}"          # smoke or full
LIMIT="${LIMIT:-10}"           # used only when MODE=smoke
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-1024}"
MAX_INPUT_TOKENS="${MAX_INPUT_TOKENS:-4096}"
BATCH_SIZE="${BATCH_SIZE:-4}"
TORCH_DTYPE="${TORCH_DTYPE:-bfloat16}"
PYTHON_BIN="${PYTHON_BIN:-python}"
OVERWRITE="${OVERWRITE:-0}"    # 1 deletes old response files; 0 resumes
MODELS="${MODELS:-all}"       # all or space-separated model names

COMMON_ARGS=(
  --config "${CONFIG}"
  --max-new-tokens "${MAX_NEW_TOKENS}"
  --max-input-tokens "${MAX_INPUT_TOKENS}"
  --batch-size "${BATCH_SIZE}"
  --torch-dtype "${TORCH_DTYPE}"
  --trust-remote-code
)

if [[ "${MODE}" == "smoke" ]]; then
  COMMON_ARGS+=(--limit "${LIMIT}")
elif [[ "${MODE}" != "full" ]]; then
  echo "MODE must be smoke or full, got: ${MODE}" >&2
  exit 2
fi

if [[ "${OVERWRITE}" == "1" ]]; then
  COMMON_ARGS+=(--overwrite)
fi

run_model() {
  local model_path="$1"
  local model_name="$2"
  local suffix="v2"
  if [[ "${MODE}" == "smoke" ]]; then
    suffix="v2_smoke"
  fi

  if [[ "${MODELS}" != "all" && " ${MODELS} " != *" ${model_name} "* ]]; then
    echo "[skip] model=${model_name} not in MODELS=${MODELS}"
    return
  fi

  echo "[run] model=${model_name} mode=${MODE} gpu=${GPU_ID} batch_size=${BATCH_SIZE}"
  CUDA_VISIBLE_DEVICES="${GPU_ID}" "${PYTHON_BIN}" scripts/run_local_hf_model.py \
    "${COMMON_ARGS[@]}" \
    --model-path "${model_path}" \
    --model-name "${model_name}" \
    --responses-path "data/responses/${model_name}_${suffix}_responses.jsonl"
}

run_model "/home/WangChanghui/wch/model/Qwen3-4B-Instruct-2507" "qwen3_4b_instruct"
run_model "/home/WangChanghui/wch/model/Llama-3.1-8B-Instruct" "llama31_8b_instruct"
run_model "/home/WangChanghui/wch/model/Mistral-7B-Instruct-v0.3" "mistral_7b_instruct"
run_model "/home/WangChanghui/wch/model/Llama-2-7B-chat-hf" "llama2_7b_chathf"
