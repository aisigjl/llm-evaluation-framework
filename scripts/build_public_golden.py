from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.ipc as ipc

from utils import project_path, write_json


OPTION_KEYS = ["A", "B", "C", "D"]


def read_arrow_rows(path: Path) -> list[dict[str, Any]]:
    with pa.memory_map(str(path), "r") as source:
        table = ipc.open_stream(source).read_all()
    return table.to_pylist()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def stable_sample(rows: list[dict[str, Any]], count: int, seed: int) -> list[dict[str, Any]]:
    if count <= 0:
        return []
    rows = list(rows)
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows[: min(count, len(rows))]


def compact(text: Any, max_len: int = 1600) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:max_len]


def split_answer_terms(answer: str, limit: int = 3) -> list[str]:
    answer = compact(answer, 500)
    parts = [p.strip() for p in re.split(r"[；;，,\n。]", answer) if p.strip()]
    terms: list[str] = []
    for part in parts:
        if len(part) <= 40:
            terms.append(part)
        if len(terms) >= limit:
            break
    return terms or ([answer[:40]] if answer else [])


def source_hash(*parts: str) -> str:
    raw = "\n".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def make_record(
    *,
    record_id: str,
    source: str,
    source_path: str,
    source_id: str,
    category: str,
    risk_level: str,
    question: str,
    reference_answer: str,
    evidence: list[str],
    expected_format: str,
    must_include: list[str],
    must_not_include: list[str] | None = None,
    refusal_expected: bool = False,
    refusal_reason: str = "",
    judge_focus: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "domain": "finance",
        "category": category,
        "risk_level": risk_level,
        "question": compact(question, 2400),
        "reference_answer": compact(reference_answer, 1400),
        "evidence": [compact(item, 1200) for item in evidence if compact(item)],
        "expected_format": expected_format,
        "must_include": [compact(item, 80) for item in must_include if compact(item, 80)],
        "must_not_include": [compact(item, 80) for item in (must_not_include or []) if compact(item, 80)],
        "refusal_expected": refusal_expected,
        "refusal_reason": refusal_reason,
        "judge_focus": judge_focus or ["accuracy", "faithfulness"],
        "source": source,
        "source_path": source_path,
        "source_id": source_id,
    }


def convert_fineval(raw_dir: Path, count: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split in ["dev", "val"]:
        for path in sorted((raw_dir / "FinEval" / split).glob("*.csv")):
            subject = path.stem.rsplit("_", 1)[0]
            for row in read_csv(path):
                answer = str(row.get("answer", "")).strip()
                if answer not in OPTION_KEYS:
                    continue
                options = "\n".join(f"{key}. {row.get(key, '')}" for key in OPTION_KEYS)
                correct_text = str(row.get(answer, "")).strip()
                explanation = str(row.get("explanation", "")).strip()
                question = f"以下是一道中文金融单选题。请给出正确选项字母，并用一句话解释理由。\n题目：{row.get('question')}\n{options}"
                reference = f"正确答案是 {answer}：{correct_text}。"
                if explanation:
                    reference += f" 解析：{compact(explanation, 400)}"
                source_path = str(path.relative_to(raw_dir))
                rows.append(
                    make_record(
                        record_id="public_fineval_" + source_hash(source_path, str(row.get("id")), question),
                        source="FinEval",
                        source_path=source_path,
                        source_id=f"{split}:{subject}:{row.get('id')}",
                        category="knowledge_choice",
                        risk_level="low",
                        question=question,
                        reference_answer=reference,
                        evidence=[correct_text, explanation],
                        expected_format="plain_text",
                        must_include=[answer, correct_text],
                        judge_focus=["accuracy", "format_following"],
                    )
                )
    return stable_sample(rows, count, seed)


def convert_disc(raw_dir: Path, count: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mapping = {
        "computing": ("calculation", "low"),
        "consulting": ("concept_qa", "low"),
        "retrieval": ("faithfulness_qa", "low"),
        "task": ("information_extraction", "low"),
    }
    for path in sorted((raw_dir / "DISC-FinLLM").glob("*.json")):
        stem = path.stem
        prefix = stem.split("_", 1)[0]
        category, risk = mapping.get(prefix, ("concept_qa", "low"))
        data = read_json(path)
        for index, row in enumerate(data):
            if "question" in row and "reference" in row:
                question = row.get("question", "")
                answer = row.get("reference", "")
                evidence = [question]
            else:
                instruction = row.get("instruction", "")
                input_text = row.get("input", "")
                question = instruction if not input_text else f"{instruction}\n{input_text}"
                answer = row.get("output", "")
                evidence = [input_text or instruction]
            if not compact(question) or not compact(answer):
                continue
            risk_level = "medium" if "风险" in question or "投资" in question else risk
            source_path = str(path.relative_to(raw_dir))
            rows.append(
                make_record(
                    record_id="public_disc_" + source_hash(source_path, str(index), question),
                    source="DISC-FinLLM",
                    source_path=source_path,
                    source_id=f"{path.name}:{index}",
                    category=category,
                    risk_level=risk_level,
                    question=question,
                    reference_answer=answer,
                    evidence=evidence,
                    expected_format="plain_text",
                    must_include=split_answer_terms(answer),
                    judge_focus=["accuracy", "faithfulness"],
                )
            )
    return stable_sample(rows, count, seed + 1)


def convert_cfbenchmark(raw_dir: Path, count: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mapping = {
        "company": ("information_extraction", "low"),
        "product": ("information_extraction", "low"),
        "event": ("information_extraction", "low"),
        "sector": ("classification", "low"),
        "sentiment": ("classification", "low"),
        "summary": ("summarization", "low"),
        "risk": ("risk_disclosure", "medium"),
        "suggestion": ("risk_disclosure", "medium"),
    }
    for arrow_path in sorted((raw_dir / "CFBenchmark" / "CFBenchmark").glob("*/data-*.arrow")):
        task = arrow_path.parent.name
        category, risk = mapping.get(task, ("concept_qa", "low"))
        for index, row in enumerate(read_arrow_rows(arrow_path)):
            instruction = row.get("instruction", "")
            input_text = row.get("input", "")
            answer = row.get("response", "")
            if not compact(input_text) or not compact(answer):
                continue
            question = f"{instruction}\n{input_text}"
            source_path = str(arrow_path.relative_to(raw_dir))
            rows.append(
                make_record(
                    record_id="public_cfbenchmark_" + source_hash(source_path, str(index), question),
                    source="CFBenchmark",
                    source_path=source_path,
                    source_id=f"{task}:{index}",
                    category=category,
                    risk_level=risk,
                    question=question,
                    reference_answer=answer,
                    evidence=[input_text],
                    expected_format="plain_text",
                    must_include=split_answer_terms(answer),
                    judge_focus=["accuracy", "faithfulness", "risk_disclosure"]
                    if category == "risk_disclosure"
                    else ["accuracy", "faithfulness"],
                )
            )
    return stable_sample(rows, count, seed + 2)


def iter_pixiu_arrow_paths(raw_dir: Path) -> Iterable[Path]:
    yield from sorted((raw_dir / "PIXIU").glob("ChanceFocus___*/default/0.0.0/*/*.arrow"))


def pixiu_category(dataset_name: str) -> tuple[str, str]:
    if dataset_name.endswith("qa"):
        return "faithfulness_qa", "low"
    if dataset_name.endswith("fineval"):
        return "knowledge_choice", "low"
    if dataset_name.endswith(("stocka", "stockb", "nl", "nl2", "nsp", "afqmc", "fe", "re")):
        return "classification", "low"
    if dataset_name.endswith(("19ccks", "20ccks", "21ccks", "22ccks", "ner", "na")):
        return "information_extraction", "low"
    return "concept_qa", "low"


def convert_pixiu(raw_dir: Path, count: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    preferred = {"flare-zh-qa", "flare-zh-fineval", "flare-zh-stocka", "flare-zh-stockb", "flare-zh-ner", "flare-zh-re"}
    for arrow_path in iter_pixiu_arrow_paths(raw_dir):
        dataset_name = arrow_path.name.replace("-test.arrow", "")
        if dataset_name not in preferred:
            continue
        category, risk = pixiu_category(dataset_name)
        for row in read_arrow_rows(arrow_path):
            question = row.get("query") or row.get("text") or ""
            answer = row.get("answer", "")
            if not compact(question) or not compact(answer):
                continue
            if row.get("choices"):
                question = f"{question}\n候选项：{row.get('choices')}"
            source_path = str(arrow_path.relative_to(raw_dir))
            source_id = f"{dataset_name}:{row.get('id')}"
            rows.append(
                make_record(
                    record_id="public_pixiu_" + source_hash(source_path, str(row.get("id")), question),
                    source="PIXIU",
                    source_path=source_path,
                    source_id=source_id,
                    category=category,
                    risk_level=risk,
                    question=question,
                    reference_answer=answer,
                    evidence=[row.get("text", ""), row.get("choices", "")],
                    expected_format="plain_text",
                    must_include=split_answer_terms(answer),
                    judge_focus=["accuracy", "faithfulness"],
                )
            )
    return stable_sample(rows, count, seed + 3)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build project golden set from public raw finance datasets.")
    parser.add_argument("--raw-dir", default="data/raw_data")
    parser.add_argument("--output", default="data/golden/finance_public_golden_v1.jsonl")
    parser.add_argument("--summary-output", default="data/golden/finance_public_golden_v1_summary.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fineval-count", type=int, default=80)
    parser.add_argument("--disc-count", type=int, default=60)
    parser.add_argument("--cfbenchmark-count", type=int, default=60)
    parser.add_argument("--pixiu-count", type=int, default=60)
    args = parser.parse_args()

    raw_dir = project_path(args.raw_dir)
    groups = {
        "FinEval": convert_fineval(raw_dir, args.fineval_count, args.seed),
        "DISC-FinLLM": convert_disc(raw_dir, args.disc_count, args.seed),
        "CFBenchmark": convert_cfbenchmark(raw_dir, args.cfbenchmark_count, args.seed),
        "PIXIU": convert_pixiu(raw_dir, args.pixiu_count, args.seed),
    }
    rows = [row for source_rows in groups.values() for row in source_rows]
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        if row["id"] not in seen:
            seen.add(row["id"])
            deduped.append(row)

    output = project_path(args.output)
    write_jsonl(output, deduped)

    def count_by(key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in deduped:
            value = str(row.get(key))
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    summary = {
        "output": str(output),
        "total": len(deduped),
        "source_counts": {source: len(source_rows) for source, source_rows in groups.items()},
        "category_counts": count_by("category"),
        "risk_level_counts": count_by("risk_level"),
        "refusal_expected_count": sum(1 for row in deduped if row.get("refusal_expected")),
        "notes": "Public datasets converted into the project golden-set schema. Keep separate from manually curated smoke golden set.",
    }
    write_json(args.summary_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
