from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from utils import load_config, project_path, read_jsonl


REQUIRED_FIELDS = {
    "id",
    "domain",
    "category",
    "risk_level",
    "question",
    "reference_answer",
    "evidence",
    "expected_format",
    "must_include",
    "must_not_include",
    "refusal_expected",
    "refusal_reason",
    "judge_focus",
}


def validate_row(row: dict[str, Any], seen: set[str]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(row))
    if missing:
        errors.append(f"missing fields: {missing}")
    row_id = str(row.get("id", ""))
    if not row_id:
        errors.append("empty id")
    elif row_id in seen:
        errors.append(f"duplicate id: {row_id}")
    seen.add(row_id)

    for key in ["evidence", "must_include", "must_not_include", "judge_focus"]:
        if key in row and not isinstance(row[key], list):
            errors.append(f"{key} must be list")
    if row.get("refusal_expected") and not str(row.get("refusal_reason", "")).strip():
        errors.append("refusal_expected=true but refusal_reason is empty")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate golden set schema.")
    parser.add_argument("--config", default="configs/finance_eval_v0.json")
    parser.add_argument("--golden-set", type=Path)
    args = parser.parse_args()

    cfg = load_config(args.config)
    golden_path = args.golden_set or cfg["golden_set_path"]
    rows = read_jsonl(golden_path)
    seen: set[str] = set()
    all_errors: list[str] = []
    for index, row in enumerate(rows, 1):
        errors = validate_row(row, seen)
        for error in errors:
            all_errors.append(f"{project_path(golden_path)}:{index}:{row.get('id')}: {error}")

    if all_errors:
        for error in all_errors:
            print(error)
        raise SystemExit(1)

    categories = sorted({row["category"] for row in rows})
    refusal_count = sum(1 for row in rows if row.get("refusal_expected"))
    print(f"validated={len(rows)} categories={categories} refusal={refusal_count}")


if __name__ == "__main__":
    main()
