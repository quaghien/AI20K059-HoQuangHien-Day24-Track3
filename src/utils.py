from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def parse_json_with_fallback(text: str, default: dict[str, Any]) -> dict[str, Any]:
    cleaned = strip_code_fences(text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return default.copy()


def dump_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
