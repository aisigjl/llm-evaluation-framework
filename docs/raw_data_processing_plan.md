# Raw Data 处理方案

当前 `data/raw_data` 下有 4 个来源：CFBenchmark、DISC-FinLLM、FinEval、PIXIU。它们格式和适用场景不同，不能直接混在一起评测，需要统一转换为本项目的 golden set schema。

## 来源与用途

| 来源 | 当前格式 | 有答案 | 推荐用途 |
|---|---|---:|---|
| FinEval | CSV | dev/val 有答案，test 无答案 | 金融知识准确性、选择题 accuracy |
| DISC-FinLLM | JSON | 有 | 生成式金融问答、计算、咨询、检索式问答 |
| CFBenchmark | HuggingFace Arrow | 有 | 风险提示、投资建议、摘要、抽取、分类 |
| PIXIU | HuggingFace Arrow | 有 | 金融 QA、分类、抽取、关系识别、数值理解 |

## 处理原则

1. **FinEval 不用 test split**：test 没有 answer 字段，不能作为 golden set，除非后续补答案。
2. **保留来源追溯字段**：每条转换后的样本保留 `source/source_path/source_id`。
3. **公开数据只作为候选样本池**：转换后仍应抽检，不建议直接认为全部都是高质量样本。
4. **选择题和生成题分开看**：选择题主要看 accuracy，生成题主要看 faithfulness、format、risk disclosure。
5. **实时/投资建议类题目谨慎处理**：如果题目要求实时行情、未来预测、具体买卖建议，需要设置 `refusal_expected=true`；当前转换脚本只做保守结构化转换，不自动重写成拒答题。

## 已实现脚本

### 1. 数据盘点

```bash
python scripts/inspect_raw_data.py \
  --raw-dir data/raw_data \
  --output reports/raw_data_inventory.json
```

输出每个来源的文件、字段和样本数。

### 2. 构建 public golden set

```bash
python scripts/build_public_golden.py \
  --raw-dir data/raw_data \
  --output data/golden/finance_public_golden_v1.jsonl \
  --summary-output data/golden/finance_public_golden_v1_summary.json \
  --fineval-count 80 \
  --disc-count 60 \
  --cfbenchmark-count 60 \
  --pixiu-count 60
```

默认输出 260 条公开数据转换样本，和原先 30 条人工 smoke golden set 分开保存。

## 推荐下一步

1. 先运行转换脚本生成 `finance_public_golden_v1.jsonl`。
2. 用 `scripts/validate_golden.py` 校验 schema。
3. 抽检每个 source 各 10 条，删除题干太长、答案太短、reference 不可靠的样本。
4. 再把保留下来的 public golden set 用于正式多模型评测。

## 为什么不直接合并所有数据

所有 raw 数据加起来超过数万条，但项目求职展示的重点是评测方法，不是堆数量。更好的策略是保留 200-300 条高质量、多类型、可解释的 golden set，然后重点展示指标、judge prompt、regression check 和 bad case 分类。
