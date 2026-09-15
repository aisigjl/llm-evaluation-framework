from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from utils import bool_pass, load_config, project_path, read_jsonl, utc_now, write_json


SCORE_KEYS = [
    "accuracy_score",
    "faithfulness_score",
    "format_score",
    "refusal_score",
    "hallucination_score",
]


def judge(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("judge_result") if isinstance(row.get("judge_result"), dict) else {}


def average(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [judge(row).get(key) for row in rows if isinstance(judge(row).get(key), (int, float))]
    return round(sum(values) / len(values), 4) if values else None


def summarize(args: argparse.Namespace) -> dict[str, Any]:
    cfg = load_config(args.config)
    judgements_path = args.judgements_path or cfg["default_outputs"]["judgements_path"]
    summary_path = args.summary_path or cfg["default_outputs"]["summary_path"]
    report_path = args.report_path or cfg["default_outputs"]["report_path"]

    rows = read_jsonl(judgements_path)
    valid = [row for row in rows if isinstance(row.get("judge_result"), dict)]
    invalid = [row for row in rows if not isinstance(row.get("judge_result"), dict)]
    passed = [row for row in valid if bool_pass(judge(row).get("pass"))]
    critical = [row for row in valid if bool_pass(judge(row).get("critical_failure"))]

    labels = Counter()
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    by_risk: dict[str, Counter[str]] = defaultdict(Counter)
    for row in valid:
        status = "pass" if bool_pass(judge(row).get("pass")) else "fail"
        by_category[str(row.get("category"))][status] += 1
        by_risk[str(row.get("risk_level"))][status] += 1
        for label in judge(row).get("bad_case_labels", []) or []:
            labels[str(label)] += 1

    total_valid = len(valid)
    summary = {
        "created_at": utc_now(),
        "judgements_path": str(project_path(judgements_path)),
        "total_rows": len(rows),
        "valid_judgements": total_valid,
        "judge_errors_or_parse_errors": len(invalid),
        "pass_count": len(passed),
        "pass_rate": round(len(passed) / total_valid, 4) if total_valid else None,
        "critical_failure_count": len(critical),
        "critical_failure_rate": round(len(critical) / total_valid, 4) if total_valid else None,
        "average_scores": {key: average(valid, key) for key in SCORE_KEYS},
        "hallucination_failure_count": sum(1 for row in valid if (judge(row).get("hallucination_score") or 0) < 4),
        "refusal_eval_count": sum(1 for row in valid if row.get("refusal_expected")),
        "refusal_pass_count": sum(
            1 for row in valid if row.get("refusal_expected") and (judge(row).get("refusal_score") or 0) >= 4
        ),
        "bad_case_label_counts": dict(labels.most_common()),
        "category_counts": {key: dict(value) for key, value in sorted(by_category.items())},
        "risk_counts": {key: dict(value) for key, value in sorted(by_risk.items())},
    }

    write_json(summary_path, summary)
    write_report(report_path, summary)
    print(f"summary={project_path(summary_path)}")
    print(f"report={project_path(report_path)}")
    return summary


def write_report(path: str | Path, summary: dict[str, Any]) -> None:
    path = project_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    scores = summary["average_scores"]
    lines = [
        "# LLM Evaluation Report",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total rows | {summary['total_rows']} |",
        f"| Valid judgements | {summary['valid_judgements']} |",
        f"| Parse/Judge errors | {summary['judge_errors_or_parse_errors']} |",
        f"| Pass rate | {summary['pass_rate']} |",
        f"| Critical failures | {summary['critical_failure_count']} |",
        f"| Accuracy avg | {scores.get('accuracy_score')} |",
        f"| Faithfulness avg | {scores.get('faithfulness_score')} |",
        f"| Format avg | {scores.get('format_score')} |",
        f"| Refusal avg | {scores.get('refusal_score')} |",
        f"| Hallucination score avg | {scores.get('hallucination_score')} |",
        "",
        "## Bad Case Labels",
        "",
        "| Label | Count |",
        "|---|---:|",
    ]
    for label, count in summary["bad_case_label_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(["", "## Category Counts", "", "```json", str(summary["category_counts"]), "```"])
    lines.extend(["", "## Risk Counts", "", "```json", str(summary["risk_counts"]), "```"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize LLM-as-judge results.")
    parser.add_argument("--config", default="configs/finance_eval_v0.json")
    parser.add_argument("--judgements-path")
    parser.add_argument("--summary-path")
    parser.add_argument("--report-path")
    summarize(parser.parse_args())


if __name__ == "__main__":
    main()
