from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from utils import load_config, read_json


def get(summary: dict[str, Any], dotted: str) -> float:
    current: Any = summary
    for part in dotted.split("."):
        current = current[part]
    return float(current)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare baseline and candidate eval summaries.")
    parser.add_argument("--config", default="configs/finance_eval_v0.json")
    parser.add_argument("--baseline-summary", required=True)
    parser.add_argument("--candidate-summary", required=True)
    parser.add_argument("--no-fail", action="store_true", help="Print result but do not exit non-zero.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    thresholds = cfg.get("regression_thresholds", {})
    baseline = read_json(args.baseline_summary)
    candidate = read_json(args.candidate_summary)

    checks = []
    pass_rate_drop = get(baseline, "pass_rate") - get(candidate, "pass_rate")
    overall_drop = get(baseline, "average_scores.accuracy_score") - get(candidate, "average_scores.accuracy_score")
    critical_increase = get(candidate, "critical_failure_count") - get(baseline, "critical_failure_count")

    checks.append(("pass_rate_drop", pass_rate_drop, float(thresholds.get("pass_rate_drop", 0.02))))
    checks.append(("accuracy_avg_drop", overall_drop, float(thresholds.get("overall_avg_drop", 0.05))))
    checks.append(("critical_failure_increase", critical_increase, float(thresholds.get("critical_failure_increase", 0))))

    failed = [(name, value, threshold) for name, value, threshold in checks if value > threshold]
    print("Regression check")
    for name, value, threshold in checks:
        status = "FAIL" if value > threshold else "PASS"
        print(f"- {name}: value={value:.4f} threshold={threshold:.4f} {status}")

    if failed and not args.no_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
