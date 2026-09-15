# LLM 评测系统：中文金融问答模型评测

这个项目用于展示如何判断模型是否真的变好了。重点不是单个分数，而是一套可复用的评测方法：golden set、指标体系、LLM-as-judge、多模型对比、训练前后 regression check 和 bad case 分类分析。

第一版领域选择中文金融问答，因为它天然覆盖事实准确性、忠实性、格式遵循、拒答能力和幻觉控制。

## 项目结构

```text
llm-evaluation-framework/
  configs/
    finance_eval_v0.json
  data/
    golden/
      finance_qa_golden_v0.jsonl
    responses/
    judgements/
  docs/
    project_spec.md
    golden_set_design.md
    metrics.md
    judge_prompt.md
    bad_case_taxonomy.md
  reports/
  scripts/
    run_model.py
    judge.py
    summarize.py
    compare_models.py
    regression_check.py
    analyze_badcases.py
    validate_golden.py
```

## 第一版能力

- golden set：`data/golden/finance_qa_golden_v0.jsonl`，30 条中文金融 QA 样本。
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
