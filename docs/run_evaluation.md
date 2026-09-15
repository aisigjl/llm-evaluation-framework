# Evaluation Runbook

This runbook uses `configs/finance_eval_public_v2.json`, which points to the 440-sample golden set.

## 1. Local Model Smoke Test

Run a small local generation first. Use a separate response file for each model.

```bash
cd /home/WangChanghui/wch/llm/llm-evaluation-framework

CUDA_VISIBLE_DEVICES=0 python scripts/run_local_hf_model.py \
  --config configs/finance_eval_public_v2.json \
  --model-path /home/WangChanghui/wch/model/Qwen3-4B-Instruct-2507 \
  --model-name qwen3_4b_instruct \
  --responses-path data/responses/qwen3_4b_instruct_v2_smoke_responses.jsonl \
  --limit 10 \
  --max-new-tokens 512 \
  --torch-dtype bfloat16 \
  --trust-remote-code \
  --overwrite
```

## 2. Full Local Model Generation

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/run_local_hf_model.py \
  --config configs/finance_eval_public_v2.json \
  --model-path /home/WangChanghui/wch/model/Qwen3-4B-Instruct-2507 \
  --model-name qwen3_4b_instruct \
  --responses-path data/responses/qwen3_4b_instruct_v2_responses.jsonl \
  --max-new-tokens 1024 \
  --torch-dtype bfloat16 \
  --trust-remote-code \
  --overwrite
```

Remove `--overwrite` to resume from an existing responses file.

## 3. Judge Responses With API

Set judge credentials in `.env` or the shell first.

```bash
python scripts/judge.py \
  --config configs/finance_eval_public_v2.json \
  --responses-path data/responses/qwen3_4b_instruct_v2_responses.jsonl \
  --judgements-path data/judgements/qwen3_4b_instruct_v2_judgements.jsonl \
  --judge-model gpt-4o \
  --overwrite
```

Remove `--overwrite` to resume judging.

## 4. Summarize

```bash
python scripts/summarize.py \
  --config configs/finance_eval_public_v2.json \
  --judgements-path data/judgements/qwen3_4b_instruct_v2_judgements.jsonl \
  --summary-path reports/qwen3_4b_instruct_v2_summary.json \
  --report-path reports/qwen3_4b_instruct_v2_report.md
```

## 5. API Candidate Model Generation

For API models, use `scripts/run_model.py` and set `MODEL_API_KEY`, `MODEL_BASE_URL`, `MODEL_NAME`.

```bash
MODEL_NAME=gpt-4o python scripts/run_model.py \
  --config configs/finance_eval_public_v2.json \
  --responses-path data/responses/gpt4o_v2_responses.jsonl \
  --model-name gpt-4o \
  --overwrite
```

Then reuse the same judge and summarize commands with matching paths.
