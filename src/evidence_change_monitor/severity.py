"""Deterministic severity assignment."""

from __future__ import annotations

import re
from typing import Any

from .constants import SEVERITY_RANK
from .util import normalize_excerpt

_BASE_BY_PRIORITY = {
    "low": "info",
    "medium": "low",
    "high": "medium",
    "critical": "high",
}
_FAILURE_MINIMUM = {
    "source.missing": "high",
    "source.parse_error": "high",
    "source.oversize": "high",
}


def _promote(current: str, candidate: str) -> str:
    return candidate if SEVERITY_RANK[candidate] > SEVERITY_RANK[current] else current


def _search_text(event: dict[str, Any]) -> str:
    values = (
        event.get("summary"),
        normalize_excerpt(event.get("before")),
        normalize_excerpt(event.get("after")),
        event.get("path"),
    )
    return " ".join(str(value) for value in values if value is not None)


def assign_severity(
    raw_event: dict[str, Any],
    source: dict[str, Any],
    rules: list[dict[str, Any]],
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    severity = _BASE_BY_PRIORITY[source["priority"]]
    minimum = _FAILURE_MINIMUM.get(raw_event["change_type"])
    if minimum:
        severity = _promote(severity, minimum)

    matched: list[str] = []
    tags: list[str] = []
    text = _search_text(raw_event)
    for rule in rules:
        if rule.get("source_ids") and source["source_id"] not in rule["source_ids"]:
            continue
        if rule.get("change_types") and raw_event["change_type"] not in rule["change_types"]:
            continue
        if rule.get("path_regex") and not re.search(rule["path_regex"], raw_event.get("path") or ""):
            continue
        if rule.get("text_regex") and not re.search(rule["text_regex"], text):
            continue
        severity = _promote(severity, rule["severity"])
        matched.append(rule["rule_id"])
        tags.extend(rule.get("tags", []))
    return severity, tuple(matched), tuple(dict.fromkeys(tags))
