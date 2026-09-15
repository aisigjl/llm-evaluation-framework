from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from utils import project_path, read_json, write_json


SCORE_KEYS = [
    "accuracy_score",
    "faithfulness_score",
    "format_score",
    "refusal_score",
    "hallucination_score",
]


def load_named_summary(item: str) -> tuple[str, dict[str, Any]]:
    if "=" not in item:
        path = Path(item)
        return path.stem.replace("_summary", ""), read_json(path)
    name, path = item.split("=", 1)
    return name, read_json(path)


def fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare multiple model summary JSON files.")
    parser.add_argument("--summary", action="append", required=True, help="Either path or name=path. Can be repeated.")
    parser.add_argument("--output-json", default="reports/model_comparison.json")
    parser.add_argument("--output-md", default="reports/model_comparison.md")
    args = parser.parse_args()

    rows = []
    for item in args.summary:
        name, summary = load_named_summary(item)
        scores = summary.get("average_scores", {})
        rows.append(
            {
                "model": name,
                "valid_judgements": summary.get("valid_judgements"),
                "pass_rate": summary.get("pass_rate"),
                "critical_failure_count": summary.get("critical_failure_count"),
                "hallucination_failure_count": summary.get("hallucination_failure_count"),
                "refusal_eval_count": summary.get("refusal_eval_count"),
                "refusal_pass_count": summary.get("refusal_pass_count"),
                **{key: scores.get(key) for key in SCORE_KEYS},
            }
        )

    write_json(args.output_json, {"models": rows})

    headers = [
        "Model",
        "Pass rate",
        "Accuracy",
        "Faithfulness",
        "Format",
        "Refusal",
        "Hallucination",
        "Critical",
        "Hallucination fail",
    ]
    lines = [
        "# Model Comparison",
        "",
        "| " + " | ".join(headers) + " |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["model"]),
                    fmt(row["pass_rate"]),
                    fmt(row["accuracy_score"]),
                    fmt(row["faithfulness_score"]),
                    fmt(row["format_score"]),
                    fmt(row["refusal_score"]),
                    fmt(row["hallucination_score"]),
                    fmt(row["critical_failure_count"]),
                    fmt(row["hallucination_failure_count"]),
                ]
            )
            + " |"
        )

    output_md = project_path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"comparison_json={project_path(args.output_json)}")
    print(f"comparison_md={output_md}")


if __name__ == "__main__":
    main()
