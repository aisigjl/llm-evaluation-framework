# 可用公开数据集与基准

本项目第一版是中文金融问答模型评测。公开数据集建议不要原封不动全量塞进最终 golden set，而是作为候选样本池：抽样、清洗、统一 schema、补充 reference/evidence/rubric，再形成项目自己的 golden set。

## 推荐优先级

### 1. CFBenchmark

- 地址：https://github.com/TongjiFinLab/CFBenchmark
- 类型：中文金融大模型评测基准。
- 覆盖：金融 NLP、金融场景计算、金融分析与解读、金融合规与安全检查。
- 适合本项目的部分：金融计算、风险评估、研报总结、投资建议/合规安全。
- 使用建议：优先抽取主观题、合规风险、风险提示类样本，转成我们的 `question/reference_answer/evidence/refusal_expected` schema。

### 2. CFinBench

- 地址：https://cfinbench.github.io/
- 类型：中文金融知识综合评测。
- 覆盖：金融学科、金融资格、金融实务、金融法律。
- 规模：约 99,100 道题，43 个二级分类，包含单选、多选、判断。
- 使用建议：适合做客观题 accuracy 子集；需要注意单选/多选/判断和生成式问答评测不同，可以转写成生成式问题，也可以保留 choice 格式单独算 exact match。

### 3. FinEval

- 地址：https://fineval.readthedocs.io/zh-cn/latest/
- 类型：中文金融领域知识评测。
- 覆盖：金融、经济、会计、从业资格等主题。
- 规模：早期版本约 4,661 道题、34 个主题。
- 使用建议：适合做轻量知识评测子集，尤其用于多模型横向对比。

### 4. DISC-Fin-Eval / DISC-FinLLM

- 地址：https://github.com/FudanDISC/DISC-FinLLM
- 类型：复旦 DISC 的中文金融大模型与金融评测资源。
- 覆盖：金融 NLP、人类试题、资料分析、时事分析。
- 使用建议：适合参考其任务拆分方式；如果使用其中数据，要注意时事分析问题的时效性，不要让模型编造实时信息。

### 5. PIXIU / FinBen

- 地址：https://github.com/The-FinAI/PIXIU
- 类型：金融 LLM、指令数据和评测基准，包含 FinBen。
- 语言：英文、西班牙文、中文资源均有。
- 覆盖：情感分析、分类、知识抽取、数值理解、文本摘要、问答等。
- 使用建议：如果你想把项目从“中文金融 QA”扩展到“金融 NLP 综合评测”，可以接入 PIXIU/FinBen；但它包含很多分类任务，和我们当前的生成式 QA judge pipeline 需要做适配。

### 6. CNFinBench

- 地址：https://cnfinbench.opencompass.org.cn/
- 类型：金融大模型评测体系和服务平台。
- 覆盖：金融专业知识问答、业务理解与分析、事实推理与计算、合规与风险控制、安全等维度。
- 使用建议：如果数据下载/使用权限允许，可以抽取其公开集；否则也可以只参考它的维度设计，完善我们自己的 golden set 分类。

## 推荐落地方案

第一阶段不要一下子接入全部数据集。建议这样做：

1. 保留当前 30 条人工 golden set，作为 smoke/e2e test。
2. 从 CFBenchmark 和 FinEval/CFinBench 各抽 50-100 条，构造 `knowledge_accuracy` 和 `calculation` 子集。
3. 从 CFBenchmark/DISC-Fin-Eval 抽 50 条合规、安全、投资建议类样本，构造 `refusal` 和 `risk_disclosure` 子集。
4. 从 PIXIU/FinBen 抽 50 条数值理解或金融 NLP 样本，构造 `faithfulness` 和 `format_following` 子集。
5. 最终形成 200-300 条评测集即可，重点是 schema、rubric 和 bad case 分析清晰，而不是盲目堆数量。

## 转换到本项目 schema

公开数据集通常是 choice、classification、summarization 或 QA 格式。转换时统一成：

```json
{
  "id": "public_cfbenchmark_0001",
  "domain": "finance",
  "category": "calculation",
  "risk_level": "low",
  "question": "...",
  "reference_answer": "...",
  "evidence": ["..."],
  "expected_format": "plain_text",
  "must_include": ["..."],
  "must_not_include": ["..."],
  "refusal_expected": false,
  "refusal_reason": "",
  "judge_focus": ["accuracy", "faithfulness"]
}
```

## 注意事项

- 检查 license，尤其是商用限制。
- 不要把训练数据和评测数据混用。
- 对带答案的公开 benchmark，要避免被模型训练语料污染；可以做 rephrase 或人工改写。
- 对实时金融/政策类题目，要标注数据时间，或者明确要求模型拒绝编造实时信息。
- 最终报告里要说明 public dataset 只是来源之一，项目核心贡献是评测 schema、rubric、judge prompt、regression check 和 bad case taxonomy。
