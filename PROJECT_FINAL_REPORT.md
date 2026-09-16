# 中文金融 LLM 评测系统最终报告

## 项目概述

本项目构建了一套面向中文金融问答的 LLM 评测框架，用于判断模型是否真的在准确性、忠实性、格式遵循、安全拒答和幻觉控制上表现更好。项目覆盖 golden set 构建、候选模型批量生成、LLM-as-judge 评分、多模型横向对比、bad case 分类分析和实验复现。

## 核心方法

- 构建 440 条中文金融 QA golden set。
- 将公开数据样本与 targeted supplement 结合，既覆盖基础能力，也覆盖高风险边界。
- 设计结构化 LLM-as-judge rubric，输出五维评分和 bad case 标签。
- 统一评测本地 HuggingFace 模型和闭源/API 模型。
- 对空响应、连接错误、解析失败等工程稳定性问题进行显式记录。

## 评测维度

| Metric | Meaning |
|---|---|
| Accuracy | 金融事实、概念、计算和结论是否正确。 |
| Faithfulness | 是否忠实于 reference answer 和 evidence。 |
| Format | 是否符合 JSON、表格、bullet list 等格式要求。 |
| Refusal | 高风险请求是否正确拒答并给出安全替代。 |
| Hallucination | 是否避免编造实时行情、政策、产品条款和收益预测。 |

## 最终模型对比

| Rank | Model | Pass Rate | Critical Failures | 结论 |
|---:|---|---:|---:|---|
| 1 | Gemini-2.5-Flash API | 79.55% | 10 | 综合最好，安全和幻觉控制最稳。 |
| 2 | Qwen3-4B-Instruct | 69.77% | 35 | 最佳本地开源模型。 |
| 3 | Llama-3.1-8B-Instruct | 48.18% | 50 | 格式较好，但准确性和忠实性不足。 |
| 4 | DeepSeek Flash API | 47.05% | 175 | 大量空响应拉低最终结果。 |
| 5 | Mistral-7B-Instruct-v0.3 | 33.86% | 85 | 高风险拒答和忠实性不足。 |
| 6 | Llama-2-7B-Chat | 17.95% | 111 | 中文金融能力弱，幻觉问题明显。 |

## 关键发现

1. Gemini-2.5-Flash API 在综合通过率、拒答质量、幻觉控制和 critical failure 数量上表现最好。
2. Qwen3-4B-Instruct 是本地开源模型中最可靠的 baseline。
3. DeepSeek Flash API 的大量空响应说明评测系统需要记录模型/API 稳定性，而不是只评非空回答质量。
4. 多数模型的主要错误集中在证据不忠实、事实错误、回答不完整、风险披露不足和不安全投资建议。
5. 格式遵循分数不能单独代表模型质量；一些模型格式分高，但高风险拒答或事实忠实性仍然较差。

## 项目产出

- `data/golden/finance_eval_golden_v2.jsonl`：440 条正式评测集。
- `scripts/run_local_hf_model.py`：本地模型批量生成。
- `scripts/run_model.py`：API 模型并发生成。
- `scripts/judge.py`：LLM-as-judge，支持并发、错误重试和空回答自动失败。
- `scripts/summarize.py`：汇总指标。
- `scripts/analyze_badcases.py`：bad case 分类分析。
- `scripts/compare_models.py`：多模型横向对比。
- `docs/evaluation_report_v2.md`：正式评测报告。
- `docs/bad_case_analysis_v2.md`：典型失败案例分析。
- `docs/resume_summary.md`：简历描述。
- `docs/interview_talking_points.md`：面试讲解稿。
- `docs/reproducibility.md`：复现实验说明。

## 面试定位

这个项目可以作为“LLM 评测系统 / 模型效果判断 / LLM-as-judge / 安全评测 / 金融问答评测”的项目经历。它的重点是证明我不仅知道怎么调用模型，也知道怎么构造评测集、设计评价指标、解释模型差异、定位 bad case，并处理真实工程中的 API 空响应、代理错误、断点续跑和多模型对比问题。
