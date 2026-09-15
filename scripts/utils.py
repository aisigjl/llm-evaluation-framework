from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_project_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def project_path(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(project_path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    path = project_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    path = project_path(path)
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Bad JSONL at {path}:{line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Bad JSONL at {path}:{line_no}: expected object")
            rows.append(row)
    return rows


def append_jsonl(path: str | Path, row: dict[str, Any]) -> None:
    path = project_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def existing_ids(path: str | Path) -> set[str]:
    path = project_path(path)
    if not path.exists():
        return set()
    return {str(row.get("id")) for row in read_jsonl(path) if row.get("id")}


def load_config(path: str | Path) -> dict[str, Any]:
    return read_json(path)


def make_openai_client(api_key_env: str, base_url_env: str | None = None):
    from openai import OpenAI

    load_project_env()
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing environment variable: {api_key_env}")

    base_url = os.getenv(base_url_env) if base_url_env else None
    timeout = float(os.getenv("REQUEST_TIMEOUT", "60"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    kwargs: dict[str, Any] = {
        "api_key": api_key,
        "timeout": timeout,
        "max_retries": max_retries,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def chat_completion_text(
    client: Any,
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            raise
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("judge output is not a JSON object")
    return data


def bool_pass(value: Any) -> bool:
    return value is True or str(value).lower() == "true"
