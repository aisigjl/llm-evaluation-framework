from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from utils import project_path, read_jsonl, write_json


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine multiple golden-set JSONL files with id de-duplication.")
    parser.add_argument("--input", action="append", required=True, help="Input JSONL path. Can be repeated.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary-output")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    source_counts: dict[str, int] = {}
    duplicate_count = 0
    for input_path in args.input:
        input_rows = read_jsonl(input_path)
        source_counts[str(project_path(input_path))] = len(input_rows)
        for row in input_rows:
            row_id = str(row.get("id", ""))
            if not row_id or row_id in seen:
                duplicate_count += 1
                continue
            seen.add(row_id)
            rows.append(row)

    output = project_path(args.output)
    write_jsonl(output, rows)

    def count_by(key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            value = str(row.get(key))
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    summary = {
        "output": str(output),
        "total": len(rows),
        "input_counts": source_counts,
        "duplicate_count": duplicate_count,
        "source_counts": count_by("source"),
        "category_counts": count_by("category"),
        "risk_level_counts": count_by("risk_level"),
        "refusal_expected_count": sum(1 for row in rows if row.get("refusal_expected")),
    }
    summary_path = args.summary_output or str(output.with_suffix(".summary.json"))
    write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
