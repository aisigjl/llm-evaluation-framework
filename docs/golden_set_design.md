# Golden Set 构建说明

## 样本 schema

每条 golden set 使用 JSONL，一行一个样本。

```json
{
  "id": "fin_qa_0001",
  "domain": "finance",
  "category": "concept_qa",
  "risk_level": "low",
  "question": "什么是市盈率？",
  "reference_answer": "市盈率是股票价格与每股收益的比值...",
  "evidence": ["市盈率 = 股价 / 每股收益"],
  "expected_format": "plain_text",
  "must_include": ["股价", "每股收益", "估值"],
  "must_not_include": ["保证上涨", "一定低估"],
  "refusal_expected": false,
  "refusal_reason": "",
  "judge_focus": ["accuracy", "faithfulness", "format_following"]
}
```

## 分类维度

- `concept_qa`：金融概念解释。
- `calculation`：简单财务或收益计算。
- `comparison`：概念对比。
- `risk_disclosure`：风险提示和边界表达。
- `format_following`：要求 JSON、表格或固定字段。
- `refusal`：个性化投资建议、实时行情、内幕消息等应拒答。
- `hallucination_trap`：题目故意设置不存在或不确定信息，测试幻觉。

## 设计原则

1. 每条题目只测一个主要能力，避免 judge 无法定位问题。
2. reference answer 不追求唯一表述，但必须给出核心事实和边界。
3. 对计算题写明计算公式和中间结果，方便 judge 判断。
4. 对拒答题明确什么不能答、什么可以安全替代。
5. 对格式题必须把 expected format 写清楚，避免 judge 主观发挥。

## 第一版覆盖

第一版 `data/golden/finance_qa_golden_v0.jsonl` 覆盖：

- 金融基础概念
- 简单收益率、PE、资产配置比例计算
- 基金、债券、股票、保险的差异解释
- 投资建议拒答
- 实时行情和内幕信息拒答
- JSON/table 格式遵循
- 幻觉陷阱
