"""Load and validate the register."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schema" / "use-case.schema.json"


def _jsonable(value):
    """YAML turns 2026-10-01 into a date; the schema expects a string."""
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_register(folder: Path) -> list[tuple[Path, dict]]:
    files = sorted(list(folder.glob("*.yaml")) + list(folder.glob("*.yml")) + list(folder.glob("*.json")))
    out = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        data = json.loads(text) if f.suffix == ".json" else yaml.safe_load(text)
        out.append((f, _jsonable(data)))
    return out


def validate(entries: list[tuple[Path, dict]], schema: dict | None = None) -> list[str]:
    validator = Draft202012Validator(schema or load_schema(), format_checker=FormatChecker())
    errors: list[str] = []
    seen: dict[str, Path] = {}
    for path, uc in entries:
        for e in sorted(validator.iter_errors(uc), key=lambda e: list(e.path)):
            where = "/".join(str(p) for p in e.path) or "(top level)"
            errors.append(f"{path.name}: {where}: {e.message}")
        uid = uc.get("id") if isinstance(uc, dict) else None
        if uid in seen:
            errors.append(f"{path.name}: id {uid} is already used by {seen[uid].name}")
        elif uid:
            seen[uid] = path
    return errors
