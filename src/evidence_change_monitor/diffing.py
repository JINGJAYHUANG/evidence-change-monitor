"""Evidence-preserving change detection."""

from __future__ import annotations

import difflib
from typing import Any

from .constants import SCHEMA_VERSION
from .models import ChangeEvent, Snapshot
from .severity import assign_severity
from .util import normalize_excerpt, sha256_json


def _event_id(source_id: str, change_type: str, path: str | None, before: Any, after: Any) -> str:
    return sha256_json(
        {
            "source_id": source_id,
            "change_type": change_type,
            "path": path,
            "before": before,
            "after": after,
        }
    )[:24]


def _raw_event(change_type: str, *, path: str | None, before: Any, after: Any, summary: str) -> dict[str, Any]:
    return {
        "change_type": change_type,
        "path": path,
        "before": normalize_excerpt(before),
        "after": normalize_excerpt(after),
        "summary": summary,
    }


def _json_pointer(part: str) -> str:
    return part.replace("~", "~0").replace("/", "~1")


def _diff_json(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if type(before) is not type(after):
        return [_raw_event("json.modified", path=path or "/", before=before, after=after, summary=f"Value type or content changed at {path or '/'}")]
    if isinstance(before, dict):
        for key in sorted(set(before) | set(after)):
            child = f"{path}/{_json_pointer(str(key))}"
            if key not in before:
                events.append(_raw_event("json.added", path=child, before=None, after=after[key], summary=f"JSON value added at {child}"))
            elif key not in after:
                events.append(_raw_event("json.removed", path=child, before=before[key], after=None, summary=f"JSON value removed at {child}"))
            else:
                events.extend(_diff_json(before[key], after[key], child))
        return events
    if isinstance(before, list):
        if before != after:
            events.append(_raw_event("json.modified", path=path or "/", before=before, after=after, summary=f"JSON list changed at {path or '/'}"))
        return events
    if before != after:
        events.append(_raw_event("json.modified", path=path or "/", before=before, after=after, summary=f"JSON value changed at {path or '/'}"))
    return events


def _diff_text(before: list[str], after: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old = before[a1:a2]
        new = after[b1:b2]
        path = f"lines:{a1 + 1}-{a2}:{b1 + 1}-{b2}"
        if tag == "insert":
            change_type = "text.added"
            summary = f"Added {len(new)} normalized line(s)"
        elif tag == "delete":
            change_type = "text.removed"
            summary = f"Removed {len(old)} normalized line(s)"
        else:
            change_type = "text.modified"
            summary = f"Replaced {len(old)} normalized line(s) with {len(new)} line(s)"
        events.append(_raw_event(change_type, path=path, before=old, after=new, summary=summary))
    return events


def _feed_map(items: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {item["id"]: item for item in items}


def _diff_feed(before: list[dict[str, str]], after: list[dict[str, str]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    old = _feed_map(before)
    new = _feed_map(after)
    for item_id in sorted(set(old) | set(new)):
        path = f"item:{item_id}"
        if item_id not in old:
            events.append(_raw_event("feed.item_added", path=path, before=None, after=new[item_id], summary=f"Feed item added: {new[item_id].get('title') or item_id}"))
        elif item_id not in new:
            events.append(_raw_event("feed.item_removed", path=path, before=old[item_id], after=None, summary=f"Feed item removed: {old[item_id].get('title') or item_id}"))
        elif old[item_id] != new[item_id]:
            events.append(_raw_event("feed.item_modified", path=path, before=old[item_id], after=new[item_id], summary=f"Feed item changed: {new[item_id].get('title') or item_id}"))
    return events


def compare_snapshots(
    baseline: Snapshot | None,
    current: Snapshot,
    source: dict[str, Any],
    rules: list[dict[str, Any]],
) -> tuple[tuple[ChangeEvent, ...], dict[str, Any]]:
    raw_events: list[dict[str, Any]] = []
    outcome = {
        "source_id": current.source_id,
        "status": "unchanged",
        "raw_changed": False,
        "normalized_changed": False,
        "event_count": 0,
        "baseline_status": baseline.status if baseline else None,
        "current_status": current.status,
    }

    if current.status != "ok":
        mapping = {
            "missing": "source.missing",
            "parse_error": "source.parse_error",
            "oversize": "source.oversize",
            "error": "source.parse_error",
        }
        change_type = mapping[current.status]
        raw_events.append(
            _raw_event(
                change_type,
                path=current.input_path,
                before=baseline.status if baseline else None,
                after=current.error,
                summary=f"Source capture failed: {current.error}",
            )
        )
        outcome["status"] = current.status
    elif baseline is None or baseline.status != "ok":
        raw_events.append(
            _raw_event(
                "source.first_seen",
                path=current.input_path,
                before=None,
                after=current.normalized,
                summary="No usable baseline existed; current snapshot is recorded as first seen",
            )
        )
        outcome["status"] = "first_seen"
        outcome["raw_changed"] = True
        outcome["normalized_changed"] = True
    else:
        outcome["raw_changed"] = baseline.raw_sha256 != current.raw_sha256
        outcome["normalized_changed"] = baseline.normalized_sha256 != current.normalized_sha256
        if not outcome["normalized_changed"]:
            if outcome["raw_changed"]:
                raw_events.append(
                    _raw_event(
                        "content.normalized_unchanged",
                        path=current.input_path,
                        before=baseline.raw_sha256,
                        after=current.raw_sha256,
                        summary="Raw bytes changed, but the configured normalizer produced identical monitored content",
                    )
                )
                outcome["status"] = "ignored_change"
            else:
                outcome["status"] = "unchanged"
        elif current.source_format in {"text", "html"}:
            raw_events.extend(_diff_text(baseline.normalized, current.normalized))
            outcome["status"] = "changed"
        elif current.source_format == "json":
            raw_events.extend(_diff_json(baseline.normalized, current.normalized))
            outcome["status"] = "changed"
        elif current.source_format == "feed":
            raw_events.extend(_diff_feed(baseline.normalized, current.normalized))
            outcome["status"] = "changed"
        else:
            raise ValueError(f"unsupported source format: {current.source_format}")

    events: list[ChangeEvent] = []
    for raw in raw_events:
        severity, matched, tags = assign_severity(raw, source, rules)
        events.append(
            ChangeEvent(
                event_id=_event_id(current.source_id, raw["change_type"], raw["path"], raw["before"], raw["after"]),
                source_id=current.source_id,
                source_title=current.title,
                locator=current.locator,
                independence_group=current.independence_group,
                change_type=raw["change_type"],
                severity=severity,
                observed_at=current.observed_at,
                baseline_sha256=baseline.normalized_sha256 if baseline else None,
                current_sha256=current.normalized_sha256,
                path=raw["path"],
                before=raw["before"],
                after=raw["after"],
                summary=raw["summary"],
                matched_rule_ids=matched,
                tags=tags,
            )
        )
    outcome["event_count"] = len(events)
    return tuple(events), outcome
