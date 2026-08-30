#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from evidence_change_monitor.constants import CHANGE_TYPES, SEVERITIES, SOURCE_FORMATS, SOURCE_PRIORITIES
from evidence_change_monitor.version import __version__

ROOT = Path(__file__).resolve().parents[1]


def enum_at(schema: dict, *path: str) -> tuple[str, ...]:
    value = schema
    for part in path:
        value = value[part]
    return tuple(value)


def main() -> int:
    registry = json.loads((ROOT / "schemas/registry.schema.json").read_text(encoding="utf-8"))
    event = json.loads((ROOT / "schemas/event.schema.json").read_text(encoding="utf-8"))
    source_props = registry["properties"]["sources"]["items"]["properties"]
    rule_props = registry["properties"]["severity_rules"]["items"]["properties"]

    checks = {
        "source formats": (tuple(source_props["format"]["enum"]), SOURCE_FORMATS),
        "source priorities": (tuple(source_props["priority"]["enum"]), SOURCE_PRIORITIES),
        "severities": (tuple(rule_props["severity"]["enum"]), SEVERITIES),
        "rule change types": (tuple(rule_props["change_types"]["items"]["enum"]), CHANGE_TYPES),
        "event change types": (tuple(event["properties"]["change_type"]["enum"]), CHANGE_TYPES),
        "event severities": (tuple(event["properties"]["severity"]["enum"]), SEVERITIES),
    }
    errors = [name for name, (left, right) in checks.items() if left != right]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["version"] != __version__:
        errors.append("package version")
    if not (ROOT / "docs/release-notes" / f"v{__version__}.md").is_file():
        errors.append("release notes")
    if errors:
        raise SystemExit("schema/version parity failed: " + ", ".join(errors))
    print("schema and version parity passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
