# Resume Summary

## 项目名称

中文金融 LLM 评测系统：Golden Set + LLM-as-Judge + 多模型横向对比

## 一句话描述

构建了一套面向中文金融问答的 LLM 评测框架，用 440 条分层 golden set、结构化 LLM-as-judge、bad case taxonomy 和多模型对比，评估模型在准确性、忠实性、格式遵循、安全拒答和幻觉控制上的真实表现。

## 简历版本 1：偏算法工程

- 设计并实现中文金融问答 LLM 评测框架，构建 440 条 golden set，覆盖金融知识、计算、证据忠实问答、格式遵循、风险披露、拒答边界和实时信息幻觉陷阱。
- 设计 LLM-as-judge rubric，按 accuracy、faithfulness、format、refusal、hallucination 五个维度输出结构化 JSON 评分，并自动聚合 pass rate、critical failure、hallucination failure、refusal pass rate 和 bad case labels。
- 支持本地 HuggingFace 模型和 OpenAI-compatible API 模型统一评测；实现 batch local inference、API 并发生成、judge 并发、断点续跑、空响应自动失败和多模型结果对比。
- 横向评测 Qwen3-4B、Llama-3.1-8B、Mistral-7B、Llama-2-7B、Gemini-2.5-Flash、DeepSeek Flash 等 6 个模型；Gemini-2.5-Flash pass rate 79.55%，Qwen3-4B 为最佳本地模型，pass rate 69.77%。
- 通过 bad case 分析定位主要错误来源：证据不忠实、事实错误、风险披露缺失、不安全投资建议、实时行情/产品信息幻觉和 API 空响应。

## 简历版本 2：偏平台/评测工程

- 搭建中文金融 LLM evaluation pipeline，覆盖 golden set 构建、候选模型批量生成、LLM-as-judge 自动评分、summary/report 生成、bad case 导出和 regression check。
- 统一支持本地开源模型与闭源 API 模型评测，封装 `run.sh`、`run_api_eval.sh`、`judge_and_report.sh`、`compare_all_models.sh`，支持断点续跑、并发请求和异常样本自动处理。
- 针对金融场景设计安全评测样本和 critical failure 规则，识别个性化投资建议、保证收益、编造实时行情、伪造政策/产品信息等高风险输出。
- 生成可复核评测报告与 bad case analysis，用于解释模型差异而非只展示总分。

## 面试中可强调的结果

| Model | Pass Rate | Critical Failures | 结论 |
|---|---:|---:|---|
| Gemini-2.5-Flash API | 79.55% | 10 | 当前综合最好，安全和幻觉控制最稳。 |
| Qwen3-4B-Instruct | 69.77% | 35 | 最佳本地开源模型，可作为本地 baseline。 |
| Llama-3.1-8B-Instruct | 48.18% | 50 | 格式遵循较好，但准确性和忠实性不足。 |
| DeepSeek Flash API | 47.05% | 175 | 大量空响应拉低结果，体现评测系统对稳定性的捕捉。 |
| Mistral-7B-Instruct | 33.86% | 85 | 高风险拒答和金融忠实性不足。 |
| Llama-2-7B-Chat | 17.95% | 111 | 中文金融能力弱，幻觉和不忠实问题明显。 |

## 技术关键词

LLM Evaluation, Golden Set, LLM-as-Judge, Regression Check, Bad Case Analysis, Hallucination Detection, Refusal Evaluation, Financial QA, OpenAI-compatible API, HuggingFace Inference, Model Comparison
