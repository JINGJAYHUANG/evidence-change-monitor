"""Strict monitor registry validation."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .constants import CHANGE_TYPES, SCHEMA_VERSION, SEVERITIES, SOURCE_FORMATS, SOURCE_PRIORITIES
from .models import ValidationIssue, ValidationResult
from .util import safe_relative_path

_ROOT_FIELDS = {
    "schema_version",
    "monitor_id",
    "title",
    "timezone",
    "default_max_bytes",
    "sources",
    "severity_rules",
    "limitations",
}
_SOURCE_FIELDS = {
    "source_id",
    "title",
    "locator",
    "input_path",
    "format",
    "priority",
    "independence_group",
    "max_bytes",
    "encoding",
    "normalization",
}
_NORMALIZATION_FIELDS = {
    "ignore_regexes",
    "ignore_json_pointers",
    "case_sensitive",
    "collapse_whitespace",
}
_RULE_FIELDS = {
    "rule_id",
    "severity",
    "source_ids",
    "change_types",
    "text_regex",
    "path_regex",
    "tags",
}
_SLUG = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def _extra_fields(value: dict[str, Any], allowed: set[str], path: str) -> list[ValidationIssue]:
    return [
        ValidationIssue("unknown_field", f"{path}.{key}", "field is not allowed")
        for key in sorted(set(value) - allowed)
    ]


def _valid_locator(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
        return True
    return value.startswith("urn:")


def validate_registry(registry: Any, *, strict: bool = True) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if not isinstance(registry, dict):
        return ValidationResult((ValidationIssue("type", "$", "registry must be an object"),))
    issues.extend(_extra_fields(registry, _ROOT_FIELDS, "$"))

    if registry.get("schema_version") != SCHEMA_VERSION:
        issues.append(ValidationIssue("schema_version", "$.schema_version", f"must equal {SCHEMA_VERSION}"))

    monitor_id = registry.get("monitor_id")
    if not isinstance(monitor_id, str) or not _SLUG.fullmatch(monitor_id):
        issues.append(ValidationIssue("monitor_id", "$.monitor_id", "must be a lowercase kebab-case identifier"))
    for field in ("title", "timezone"):
        if not isinstance(registry.get(field), str) or not registry[field].strip():
            issues.append(ValidationIssue("required_text", f"$.{field}", "must be a non-empty string"))

    default_max = registry.get("default_max_bytes", 1_000_000)
    if isinstance(default_max, bool) or not isinstance(default_max, int) or not 1 <= default_max <= 10_000_000:
        issues.append(ValidationIssue("default_max_bytes", "$.default_max_bytes", "must be an integer from 1 to 10000000"))

    limitations = registry.get("limitations", [])
    if not isinstance(limitations, list) or not all(isinstance(item, str) and item.strip() for item in limitations):
        issues.append(ValidationIssue("limitations", "$.limitations", "must be a list of non-empty strings"))

    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        issues.append(ValidationIssue("sources", "$.sources", "must be a non-empty list"))
        sources = []

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, source in enumerate(sources):
        path = f"$.sources[{index}]"
        if not isinstance(source, dict):
            issues.append(ValidationIssue("type", path, "source must be an object"))
            continue
        issues.extend(_extra_fields(source, _SOURCE_FIELDS, path))
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not _SLUG.fullmatch(source_id):
            issues.append(ValidationIssue("source_id", f"{path}.source_id", "must be lowercase kebab-case"))
        elif source_id in seen_ids:
            issues.append(ValidationIssue("duplicate_source", f"{path}.source_id", "source_id must be unique"))
        else:
            seen_ids.add(source_id)
        for field in ("title", "independence_group"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                issues.append(ValidationIssue("required_text", f"{path}.{field}", "must be a non-empty string"))
        locator = source.get("locator")
        if not isinstance(locator, str) or not _valid_locator(locator):
            issues.append(ValidationIssue("locator", f"{path}.locator", "must be an HTTPS URL without credentials or a URN"))
        input_path = source.get("input_path")
        if not isinstance(input_path, str):
            issues.append(ValidationIssue("input_path", f"{path}.input_path", "must be a relative path string"))
        else:
            try:
                safe_relative_path(input_path)
            except ValueError as exc:
                issues.append(ValidationIssue("input_path", f"{path}.input_path", str(exc)))
            if input_path in seen_paths:
                issues.append(ValidationIssue("duplicate_input_path", f"{path}.input_path", "input_path must be unique"))
            seen_paths.add(input_path)
        if source.get("format") not in SOURCE_FORMATS:
            issues.append(ValidationIssue("format", f"{path}.format", f"must be one of {SOURCE_FORMATS}"))
        if source.get("priority") not in SOURCE_PRIORITIES:
            issues.append(ValidationIssue("priority", f"{path}.priority", f"must be one of {SOURCE_PRIORITIES}"))
        encoding = source.get("encoding", "utf-8")
        if encoding not in {"utf-8", "utf-8-sig"}:
            issues.append(ValidationIssue("encoding", f"{path}.encoding", "must be utf-8 or utf-8-sig"))
        max_bytes = source.get("max_bytes", default_max)
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1 <= max_bytes <= 10_000_000:
            issues.append(ValidationIssue("max_bytes", f"{path}.max_bytes", "must be an integer from 1 to 10000000"))
        normalization = source.get("normalization", {})
        if not isinstance(normalization, dict):
            issues.append(ValidationIssue("normalization", f"{path}.normalization", "must be an object"))
            normalization = {}
        else:
            issues.extend(_extra_fields(normalization, _NORMALIZATION_FIELDS, f"{path}.normalization"))
        for field in ("ignore_regexes", "ignore_json_pointers"):
            values = normalization.get(field, [])
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                issues.append(ValidationIssue(field, f"{path}.normalization.{field}", "must be a list of strings"))
            elif field == "ignore_regexes":
                for rule_index, pattern in enumerate(values):
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        issues.append(ValidationIssue("regex", f"{path}.normalization.{field}[{rule_index}]", str(exc)))
            else:
                for pointer_index, pointer in enumerate(values):
                    if pointer and not pointer.startswith("/"):
                        issues.append(ValidationIssue("json_pointer", f"{path}.normalization.{field}[{pointer_index}]", "must be empty or start with /"))
        for field in ("case_sensitive", "collapse_whitespace"):
            value = normalization.get(field, True)
            if not isinstance(value, bool):
                issues.append(ValidationIssue(field, f"{path}.normalization.{field}", "must be Boolean"))

    rules = registry.get("severity_rules", [])
    if not isinstance(rules, list):
        issues.append(ValidationIssue("severity_rules", "$.severity_rules", "must be a list"))
        rules = []
    seen_rules: set[str] = set()
    for index, rule in enumerate(rules):
        path = f"$.severity_rules[{index}]"
        if not isinstance(rule, dict):
            issues.append(ValidationIssue("type", path, "rule must be an object"))
            continue
        issues.extend(_extra_fields(rule, _RULE_FIELDS, path))
        rule_id = rule.get("rule_id")
        if not isinstance(rule_id, str) or not _SLUG.fullmatch(rule_id):
            issues.append(ValidationIssue("rule_id", f"{path}.rule_id", "must be lowercase kebab-case"))
        elif rule_id in seen_rules:
            issues.append(ValidationIssue("duplicate_rule", f"{path}.rule_id", "rule_id must be unique"))
        else:
            seen_rules.add(rule_id)
        if rule.get("severity") not in SEVERITIES:
            issues.append(ValidationIssue("severity", f"{path}.severity", f"must be one of {SEVERITIES}"))
        source_ids = rule.get("source_ids", [])
        if not isinstance(source_ids, list) or not all(isinstance(item, str) for item in source_ids):
            issues.append(ValidationIssue("source_ids", f"{path}.source_ids", "must be a list of strings"))
        else:
            for source_id in source_ids:
                if source_id not in seen_ids:
                    issues.append(ValidationIssue("unknown_source", f"{path}.source_ids", f"unknown source_id: {source_id}"))
        change_types = rule.get("change_types", [])
        if not isinstance(change_types, list) or not all(item in CHANGE_TYPES for item in change_types):
            issues.append(ValidationIssue("change_types", f"{path}.change_types", f"must contain only {CHANGE_TYPES}"))
        for field in ("text_regex", "path_regex"):
            pattern = rule.get(field)
            if pattern is not None:
                if not isinstance(pattern, str):
                    issues.append(ValidationIssue(field, f"{path}.{field}", "must be a string"))
                else:
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        issues.append(ValidationIssue("regex", f"{path}.{field}", str(exc)))
        tags = rule.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(item, str) and item.strip() for item in tags):
            issues.append(ValidationIssue("tags", f"{path}.tags", "must be a list of non-empty strings"))

    if strict:
        issues = [
            ValidationIssue(item.code, item.path, item.message, "error")
            if item.level == "warning" else item
            for item in issues
        ]
    return ValidationResult(tuple(issues))


def load_registry(path: Path, *, strict: bool = True) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = validate_registry(data, strict=strict)
    if not result.ok:
        detail = "; ".join(f"{item.code}@{item.path}: {item.message}" for item in result.issues)
        raise ValueError(f"registry validation failed: {detail}")
    return data
