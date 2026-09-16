# Reproducibility

## 1. Environment

```bash
cd /home/WangChanghui/wch/llm/llm-evaluation-framework
pip install -r requirements.txt
```

`.env` should contain candidate model and judge model credentials:

```text
MODEL_API_KEY=...
MODEL_BASE_URL=...
MODEL_NAME=...

JUDGE_API_KEY=...
JUDGE_BASE_URL=...
JUDGE_MODEL=gpt-4o
```

The shell scripts default to `DISABLE_PROXY=1`, which clears `http_proxy` and `https_proxy` before API calls. Set `DISABLE_PROXY=0` only if a working proxy is required.

## 2. Validate Golden Set

```bash
python scripts/validate_golden.py --config configs/finance_eval_public_v2.json
```

Expected result:

```text
validated=440 ... refusal=79
```

## 3. Run Local Models

Smoke test:

```bash
MODE=smoke LIMIT=10 MODELS="qwen3_4b_instruct" ./run.sh
```

Full local run:

```bash
MODE=full BATCH_SIZE=4 MAX_NEW_TOKENS=512 ./run.sh
```

Each model writes to `data/responses/{model_name}_v2_responses.jsonl`.

## 4. Judge Local Models

```bash
JUDGE_WORKERS=4 ./judge_and_report.sh
```

Outputs:

```text
data/judgements/*_v2_judgements.jsonl
reports/*_v2_summary.json
reports/*_v2_report.md
reports/*_v2_badcases.md
reports/local_model_comparison_v2.md
```

## 5. Run API Models

Example for one API model:

```bash
MODEL_NAME="gemini-2.5-flash" MODEL_TAG="gemini-2_5-flash" LIMIT=0 MODEL_WORKERS=4 JUDGE_WORKERS=4 ./run_api_eval.sh
```

If a model returns empty responses and you want to count them as failures, do not retry generation. Rejudge with the current response file; `scripts/judge.py` automatically marks empty responses as failed.

Retry only invalid judge rows:

```bash
python scripts/judge.py   --config configs/finance_eval_public_v2.json   --responses-path data/responses/deepseekflash_api_v2_responses.jsonl   --judgements-path data/judgements/deepseekflash_api_v2_judgements.jsonl   --judge-model gpt-4o   --workers 2   --retry-errors
```

## 6. Compare All Models

```bash
./compare_all_models.sh
```

Output:

```text
reports/all_model_comparison_v2.md
reports/all_model_comparison_v2.json
```

## 7. Final Reports

Main documents:

```text
README.md
docs/evaluation_report_v2.md
docs/bad_case_analysis_v2.md
reports/final_result_tables_v2.md
reports/all_model_comparison_v2.md
```

## 8. Notes On Determinism

- Candidate generation uses `temperature=0.0` by default.
- LLM-as-judge uses `temperature=0.0` by default.
- API providers may still change outputs over time because closed models and routing services can update silently.
- For strict reproducibility, keep response and judgement JSONL artifacts.
