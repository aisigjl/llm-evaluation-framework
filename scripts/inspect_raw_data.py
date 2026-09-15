from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.ipc as ipc

from utils import project_path, write_json


def read_arrow(path: Path) -> Any:
    with pa.memory_map(str(path), "r") as source:
        return ipc.open_stream(source).read_all()


def count_csv(path: Path) -> tuple[int, list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = sum(1 for _ in reader)
        return rows, list(reader.fieldnames or [])


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect raw public finance datasets.")
    parser.add_argument("--raw-dir", default="data/raw_data")
    parser.add_argument("--output", default="reports/raw_data_inventory.json")
    args = parser.parse_args()

    raw_dir = project_path(args.raw_dir)
    inventory: dict[str, Any] = {"raw_dir": str(raw_dir), "sources": {}}

    fineval_dir = raw_dir / "FinEval"
    if fineval_dir.exists():
        fineval: dict[str, Any] = {}
        for split in ["dev", "val", "test"]:
            split_dir = fineval_dir / split
            rows = 0
            files = []
            fields = None
            for path in sorted(split_dir.glob("*.csv")):
                count, fieldnames = count_csv(path)
                rows += count
                fields = fields or fieldnames
                files.append({"path": str(path.relative_to(raw_dir)), "rows": count})
            fineval[split] = {"rows": rows, "fields": fields, "files": files}
        inventory["sources"]["FinEval"] = fineval

    disc_dir = raw_dir / "DISC-FinLLM"
    if disc_dir.exists():
        disc = []
        for path in sorted(disc_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            fields = sorted(data[0].keys()) if data else []
            disc.append({"path": str(path.relative_to(raw_dir)), "rows": len(data), "fields": fields})
        inventory["sources"]["DISC-FinLLM"] = disc

    cf_dir = raw_dir / "CFBenchmark" / "CFBenchmark"
    if cf_dir.exists():
        cf = []
        for path in sorted(cf_dir.glob("*/data-*.arrow")):
            table = read_arrow(path)
            cf.append(
                {
                    "task": path.parent.name,
                    "path": str(path.relative_to(raw_dir)),
                    "rows": table.num_rows,
                    "fields": table.column_names,
                }
            )
        inventory["sources"]["CFBenchmark"] = cf

    pixiu_dir = raw_dir / "PIXIU"
    if pixiu_dir.exists():
        pixiu = []
        for info_path in sorted(pixiu_dir.glob("ChanceFocus___*/default/0.0.0/*/dataset_info.json")):
            info = json.loads(info_path.read_text(encoding="utf-8"))
            splits = info.get("splits", {})
            rows = sum(split.get("num_examples", 0) for split in splits.values())
            arrow_files = [str(path.relative_to(raw_dir)) for path in info_path.parent.glob("*.arrow")]
            pixiu.append(
                {
                    "dataset": info.get("dataset_name") or info_path.parts[-5],
                    "path": str(info_path.relative_to(raw_dir)),
                    "rows": rows,
                    "fields": sorted((info.get("features") or {}).keys()),
                    "arrow_files": arrow_files,
                }
            )
        inventory["sources"]["PIXIU"] = pixiu

    write_json(args.output, inventory)
    print(f"inventory={project_path(args.output)}")


if __name__ == "__main__":
    main()
