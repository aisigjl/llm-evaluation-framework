# LLM 评测系统：中文金融问答模型评测

这个项目用于展示如何判断模型是否真的变好了。重点不是单个分数，而是一套可复用的评测方法：golden set、指标体系、LLM-as-judge、多模型对比、训练前后 regression check 和 bad case 分类分析。

第一版领域选择中文金融问答，因为它天然覆盖事实准确性、忠实性、格式遵循、拒答能力和幻觉控制。


## 当前实验结果 v2

当前正式评测集为 `data/golden/finance_eval_golden_v2.jsonl`，共 440 条中文金融 QA 样本，包含公开数据转换样本和 150 条 targeted supplement。targeted supplement 专门覆盖拒答/合规边界、高风险投资建议、幻觉陷阱、格式遵循和复杂计算。

已完成 4 个本地开源模型和 2 个闭源/API 模型评测：

| Model | Pass Rate | Accuracy | Faithfulness | Format | Refusal | Hallucination | Critical Failures |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini-2.5-Flash API | 79.55% | 4.4273 | 4.3682 | 4.8114 | 4.8568 | 4.7545 | 10 |
| Qwen3-4B-Instruct | 69.77% | 4.1386 | 4.0455 | 4.7023 | 4.7659 | 4.4750 | 35 |
| Llama-3.1-8B-Instruct | 48.18% | 3.5068 | 3.4182 | 4.7295 | 4.6068 | 4.3909 | 50 |
| DeepSeek Flash API | 84.55% | 3.0591 | 3.0136 | 3.3341 | 3.4023 | 3.3727 | 10 |
| Mistral-7B-Instruct-v0.3 | 33.86% | 3.0795 | 2.9614 | 4.6636 | 4.3500 | 3.9955 | 85 |
| Llama-2-7B-Chat | 17.95% | 2.5636 | 2.3614 | 3.6818 | 3.9159 | 3.4364 | 111 |

完整结果和分析见：

- `docs/evaluation_report_v2.md`
- `docs/bad_case_analysis_v2.md`
- `reports/final_result_tables_v2.md`
- `reports/local_model_comparison_v2.md`
- `reports/all_model_comparison_v2.md`


## 项目包装材料

- `PROJECT_FINAL_REPORT.md`：最终项目报告，适合作为作品集入口。
- `docs/resume_summary.md`：简历项目描述，可直接改写到简历。
- `docs/interview_talking_points.md`：面试讲解稿，包含一分钟讲法、设计选择和局限性。
- `docs/reproducibility.md`：复现实验步骤。
- `docs/evaluation_report_v2.md`：正式评测报告。
- `docs/bad_case_analysis_v2.md`：典型 bad case 分析。

## 项目结构

```text
llm-evaluation-framework/
  configs/
    finance_eval_v0.json
    finance_eval_public_v1.json
    finance_eval_public_v2.json
  data/
    golden/
      finance_qa_golden_v0.jsonl
      finance_eval_golden_v2.jsonl
      finance_targeted_supplement_v1.jsonl
    responses/
    judgements/
  docs/
    project_spec.md
    golden_set_design.md
    public_datasets.md
    metrics.md
    judge_prompt.md
    bad_case_taxonomy.md
    evaluation_report_v2.md
    bad_case_analysis_v2.md
    resume_summary.md
    interview_talking_points.md
    reproducibility.md
    run_evaluation.md
  reports/
  scripts/
    run_model.py
    run_local_hf_model.py
    judge.py
    summarize.py
    compare_models.py
    regression_check.py
    analyze_badcases.py
    validate_golden.py
    inspect_raw_data.py
    build_public_golden.py
    combine_golden_sets.py
```

## 第一版能力

- golden set：`data/golden/finance_qa_golden_v0.jsonl`，30 条中文金融 QA 样本。
- public dataset 调研：`docs/public_datasets.md`。
- 指标：accuracy、faithfulness、format following、refusal quality、hallucination score。
- LLM-as-judge：强模型输出结构化 JSON 评分和 bad case 标签。
- 多模型对比：每个模型输出独立 responses/judgements/summary。
- regression check：比较 baseline summary 和 candidate summary。
- bad case 分类：按标签、风险等级、任务类别聚合失败样本。

## 安装

```bash
cd /home/WangChanghui/wch/llm/llm-evaluation-framework
pip install -r requirements.txt
cp .env.example .env
```

`.env` 示例：

```text
MODEL_API_KEY=xxx
MODEL_BASE_URL=
MODEL_NAME=gpt-4o-mini

JUDGE_API_KEY=xxx
JUDGE_BASE_URL=
JUDGE_MODEL=gpt-4o
```

`MODEL_*` 用于被评测模型，`JUDGE_*` 用于裁判模型。两者建议分开，避免自评。

## 公开数据处理

你当前放在 `data/raw_data/` 下的四个来源可以按以下方式处理：

```bash
python scripts/inspect_raw_data.py \
  --raw-dir data/raw_data \
  --output reports/raw_data_inventory.json

python scripts/build_public_golden.py \
  --raw-dir data/raw_data \
  --output data/golden/finance_public_golden_v1.jsonl \
  --summary-output data/golden/finance_public_golden_v1_summary.json \
  --fineval-count 80 \
  --disc-count 60 \
  --cfbenchmark-count 60 \
  --pixiu-count 60

python scripts/combine_golden_sets.py \
  --input data/golden/finance_qa_golden_v0.jsonl \
  --input data/golden/finance_public_golden_v1.jsonl \
  --output data/golden/finance_eval_golden_v1.jsonl \
  --summary-output data/golden/finance_eval_golden_v1_summary.json

python scripts/validate_golden.py \
  --config configs/finance_eval_public_v1.json
```

当前已生成正式 v1 golden set：`data/golden/finance_eval_golden_v1.jsonl`，共 290 条，其中 30 条人工 smoke 样本、260 条公开数据转换样本。配置文件是 `configs/finance_eval_public_v1.json`。

详细处理策略见 `docs/raw_data_processing_plan.md`。

## 运行流程

### 1. 校验 golden set

```bash
python scripts/validate_golden.py --config configs/finance_eval_v0.json
```

### 2. 生成候选模型回答

```bash
python scripts/run_model.py \
  --config configs/finance_eval_v0.json \
  --responses-path data/responses/model_a_responses.jsonl \
  --model-name "$MODEL_NAME" \
  --overwrite
```

### 3. LLM-as-judge 评分

```bash
python scripts/judge.py \
  --config configs/finance_eval_v0.json \
  --responses-path data/responses/model_a_responses.jsonl \
  --judgements-path data/judgements/model_a_judgements.jsonl \
  --judge-model "$JUDGE_MODEL" \
  --overwrite
```

### 4. 汇总报告

```bash
python scripts/summarize.py \
  --config configs/finance_eval_v0.json \
  --judgements-path data/judgements/model_a_judgements.jsonl \
  --summary-path reports/model_a_summary.json \
  --report-path reports/model_a_report.md
```

### 5. Bad case 分类

```bash
python scripts/analyze_badcases.py \
  --config configs/finance_eval_v0.json \
  --judgements-path data/judgements/model_a_judgements.jsonl \
  --badcase-path reports/model_a_badcases.jsonl \
  --markdown-path reports/model_a_badcases.md \
  --overwrite
```

### 6. Regression check

训练前后或版本前后比较：

```bash
python scripts/regression_check.py \
  --config configs/finance_eval_v0.json \
  --baseline-summary reports/baseline_summary.json \
  --candidate-summary reports/model_a_summary.json
```

### 7. 多模型横向对比

```bash
python scripts/compare_models.py \
  --summary base=reports/base_summary.json \
  --summary sft=reports/sft_summary.json \
  --summary dpo=reports/dpo_summary.json \
  --output-json reports/model_comparison.json \
  --output-md reports/model_comparison.md
```

## 多模型横向对比建议

对每个模型使用同一份 golden set、同一个 judge model、同一套 summarize 脚本，输出独立文件：

```text
reports/base_summary.json
reports/sft_summary.json
reports/dpo_summary.json
```

最终报告重点比较：

- pass_rate
- average_scores
- critical_failure_count
- hallucination_failure_count
- refusal_pass_count / refusal_eval_count
- bad_case_label_counts

## 项目边界

本项目用于评估模型能力，不提供真实投资建议。评测样本中的金融内容用于测试模型是否谨慎、准确、忠实和合规，不构成任何买卖建议。
