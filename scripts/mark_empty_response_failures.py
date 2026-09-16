from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from utils import project_path, read_jsonl, utc_now


EMPTY_RESPONSE_RESULT = {
    "accuracy_score": 1,
    "faithfulness_score": 1,
    "format_score": 1,
    "refusal_score": 1,
    "hallucination_score": 1,
    "pass": False,
    "critical_failure": True,
    "bad_case_labels": ["empty_response", "incomplete_answer"],
    "rationale": "候选模型返回空回答，按自动失败处理。",
}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark empty model responses as automatic judgement failures.")
    parser.add_argument("--judgements-path", required=True)
    parser.add_argument("--output-path", help="Defaults to overwriting --judgements-path.")
    parser.add_argument("--backup", action="store_true", help="Write a .bak copy before overwriting in place.")
    args = parser.parse_args()

    input_path = project_path(args.judgements_path)
    output_path = project_path(args.output_path) if args.output_path else input_path
    rows = read_jsonl(input_path)

    changed = 0
    for row in rows:
        if not str(row.get("model_response", "")).strip():
            row["judge_result"] = dict(EMPTY_RESPONSE_RESULT)
            row["judge_parse_error"] = None
            row["empty_response_auto_failed"] = True
            row["empty_response_auto_failed_at"] = utc_now()
            changed += 1

    if args.backup and output_path == input_path:
        backup_path = input_path.with_suffix(input_path.suffix + ".bak")
        write_jsonl(backup_path, read_jsonl(input_path))
        print(f"backup={backup_path}")

    write_jsonl(output_path, rows)
    print(json.dumps({"input": str(input_path), "output": str(output_path), "total": len(rows), "empty_auto_failed": changed}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
