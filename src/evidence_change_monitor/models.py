"""Typed result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str
    level: str = "error"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(item.level == "error" for item in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "issues": [item.to_dict() for item in self.issues]}


@dataclass(frozen=True)
class Snapshot:
    schema_version: int
    source_id: str
    title: str
    locator: str
    independence_group: str
    source_format: str
    priority: str
    observed_at: str
    input_path: str
    status: str
    raw_sha256: str | None
    normalized_sha256: str | None
    normalizer_version: str
    normalized: Any
    raw_bytes: int
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChangeEvent:
    event_id: str
    source_id: str
    source_title: str
    locator: str
    independence_group: str
    change_type: str
    severity: str
    observed_at: str
    baseline_sha256: str | None
    current_sha256: str | None
    path: str | None
    before: Any
    after: Any
    summary: str
    matched_rule_ids: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["matched_rule_ids"] = list(self.matched_rule_ids)
        data["tags"] = list(self.tags)
        return data


@dataclass(frozen=True)
class MonitorRun:
    schema_version: int
    monitor_id: str
    run_id: str
    as_of: str
    registry_sha256: str
    baseline_run_id: str | None
    current_snapshot_count: int
    events: tuple[ChangeEvent, ...]
    source_outcomes: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "monitor_id": self.monitor_id,
            "run_id": self.run_id,
            "as_of": self.as_of,
            "registry_sha256": self.registry_sha256,
            "baseline_run_id": self.baseline_run_id,
            "current_snapshot_count": self.current_snapshot_count,
            "events": [event.to_dict() for event in self.events],
            "source_outcomes": list(self.source_outcomes),
            "summary": self.summary,
            "limitations": list(self.limitations),
        }
