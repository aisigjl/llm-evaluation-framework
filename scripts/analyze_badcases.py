from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from utils import append_jsonl, bool_pass, load_config, project_path, read_jsonl


def judge(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("judge_result") if isinstance(row.get("judge_result"), dict) else {}


def is_bad(row: dict[str, Any]) -> bool:
    result = judge(row)
    if not result:
        return True
    return not bool_pass(result.get("pass")) or bool_pass(result.get("critical_failure")) or bool(result.get("bad_case_labels"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Export and categorize bad cases.")
    parser.add_argument("--config", default="configs/finance_eval_v0.json")
    parser.add_argument("--judgements-path")
    parser.add_argument("--badcase-path")
    parser.add_argument("--markdown-path")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    judgements_path = args.judgements_path or cfg["default_outputs"]["judgements_path"]
    badcase_path = args.badcase_path or cfg["default_outputs"]["badcase_path"]
    markdown_path = args.markdown_path or str(Path(badcase_path).with_suffix(".md"))

    rows = read_jsonl(judgements_path)
    bad = [row for row in rows if is_bad(row)]
    output = project_path(badcase_path)
    if args.overwrite and output.exists():
        output.unlink()

    label_counts = Counter()
    category_counts: dict[str, int] = defaultdict(int)
    risk_counts: dict[str, int] = defaultdict(int)
    for row in bad:
        result = judge(row)
        labels = result.get("bad_case_labels", []) if result else ["judge_parse_error"]
        for label in labels:
            label_counts[str(label)] += 1
        category_counts[str(row.get("category"))] += 1
        risk_counts[str(row.get("risk_level"))] += 1
        append_jsonl(
            output,
            {
                "id": row.get("id"),
                "category": row.get("category"),
                "risk_level": row.get("risk_level"),
                "question": row.get("question"),
                "model_response": row.get("model_response"),
                "judge_result": result,
            },
        )

    md = project_path(markdown_path)
    md.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Bad Case Analysis",
        "",
        f"- total bad cases: {len(bad)}",
        "",
        "## Label Counts",
        "",
        "| Label | Count |",
        "|---|---:|",
    ]
    for label, count in label_counts.most_common():
        lines.append(f"| {label} | {count} |")
    lines.extend(["", "## Category Counts", "", "```json", json.dumps(category_counts, ensure_ascii=False, indent=2), "```"])
    lines.extend(["", "## Risk Counts", "", "```json", json.dumps(risk_counts, ensure_ascii=False, indent=2), "```"])
    lines.extend(["", "## Top Cases", ""])
    for row in bad[:10]:
        result = judge(row)
        lines.append(f"### {row.get('id')} / {row.get('category')} / {row.get('risk_level')}")
        lines.append("")
        lines.append(f"- question: {row.get('question')}")
        lines.append(f"- labels: {result.get('bad_case_labels') if result else ['judge_parse_error']}")
        lines.append(f"- rationale: {result.get('rationale') if result else row.get('judge_parse_error')}")
        lines.append("")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"badcases={output}")
    print(f"markdown={md}")


if __name__ == "__main__":
    main()
