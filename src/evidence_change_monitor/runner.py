"""End-to-end monitoring pipeline."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .capture import capture_all
from .config import validate_registry
from .constants import SCHEMA_VERSION, SEVERITY_RANK
from .diffing import compare_snapshots
from .integrity import build_manifest
from .models import MonitorRun, Snapshot
from .reporting import write_reports
from .storage import commit_state, load_latest_state, write_snapshot_set
from .util import atomic_write_text, canonical_json_bytes, sha256_bytes, sha256_json


def validate_as_of(value: str) -> str:
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError("as_of must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("as_of must include Z or an explicit UTC offset")
    return value


def _run_id(
    monitor_id: str,
    as_of: str,
    registry_sha: str,
    baseline_run_id: str | None,
    snapshots: tuple[Snapshot, ...],
) -> str:
    payload = {
        "monitor_id": monitor_id,
        "as_of": as_of,
        "registry_sha256": registry_sha,
        "baseline_run_id": baseline_run_id,
        "snapshots": [
            {
                "source_id": item.source_id,
                "status": item.status,
                "raw_sha256": item.raw_sha256,
                "normalized_sha256": item.normalized_sha256,
                "error": item.error,
            }
            for item in snapshots
        ],
    }
    return f"{as_of[:10]}-{sha256_json(payload)[:16]}"


def _next_state(
    registry: dict[str, Any],
    baseline: dict[str, Snapshot],
    current: tuple[Snapshot, ...],
) -> tuple[Snapshot, ...]:
    result: list[Snapshot] = []
    for source in registry["sources"]:
        source_id = source["source_id"]
        candidate = next(item for item in current if item.source_id == source_id)
        if candidate.status == "ok":
            result.append(candidate)
        elif source_id in baseline and baseline[source_id].status == "ok":
            result.append(baseline[source_id])
        else:
            result.append(candidate)
    return tuple(result)


def run_monitor(
    registry: dict[str, Any],
    *,
    input_dir: Path,
    state_dir: Path,
    output_dir: Path,
    as_of: str,
    commit: bool = False,
) -> MonitorRun:
    result = validate_registry(registry, strict=True)
    if not result.ok:
        detail = "; ".join(f"{item.code}@{item.path}: {item.message}" for item in result.issues)
        raise ValueError(f"registry validation failed: {detail}")
    as_of = validate_as_of(as_of)
    registry_sha = sha256_bytes(canonical_json_bytes(registry))
    baseline_run_id, baseline = load_latest_state(state_dir)
    snapshots = capture_all(registry, input_dir, as_of)

    events = []
    outcomes = []
    source_map = {source["source_id"]: source for source in registry["sources"]}
    for snapshot in snapshots:
        source = source_map[snapshot.source_id]
        source_events, outcome = compare_snapshots(
            baseline.get(snapshot.source_id),
            snapshot,
            source,
            registry.get("severity_rules", []),
        )
        events.extend(source_events)
        outcomes.append(outcome)

    events.sort(
        key=lambda event: (
            -SEVERITY_RANK[event.severity],
            event.source_id,
            event.change_type,
            event.event_id,
        )
    )
    severity_counts = Counter(event.severity for event in events if event.change_type != "content.normalized_unchanged")
    type_counts = Counter(event.change_type for event in events)
    material = [event for event in events if event.change_type != "content.normalized_unchanged"]
    failed = [item for item in outcomes if item["current_status"] != "ok"]
    ignored = [item for item in events if item.change_type == "content.normalized_unchanged"]
    summary = {
        "event_count": len(events),
        "material_event_count": len(material),
        "ignored_change_count": len(ignored),
        "failed_source_count": len(failed),
        "severity_counts": dict(sorted(severity_counts.items())),
        "change_type_counts": dict(sorted(type_counts.items())),
        "highest_severity": material[0].severity if material else None,
    }
    run_id = _run_id(registry["monitor_id"], as_of, registry_sha, baseline_run_id, snapshots)
    limitations = tuple(
        registry.get(
            "limitations",
            [
                "The monitor compares captured representations, not the full external source.",
                "A detected change does not prove legal effect, causality, truthfulness, or material impact.",
                "No detected change does not prove that the source or underlying reality was unchanged.",
            ],
        )
    )
    run = MonitorRun(
        schema_version=SCHEMA_VERSION,
        monitor_id=registry["monitor_id"],
        run_id=run_id,
        as_of=as_of,
        registry_sha256=registry_sha,
        baseline_run_id=baseline_run_id,
        current_snapshot_count=len(snapshots),
        events=tuple(events),
        source_outcomes=tuple(outcomes),
        summary=summary,
        limitations=limitations,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_reports(run, output_dir)
    write_snapshot_set(output_dir / "current-snapshots", snapshots)
    manifest = build_manifest(output_dir)
    atomic_write_text(
        output_dir / "manifest.json",
        __import__("json").dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    if commit:
        commit_state(state_dir, run_id, _next_state(registry, baseline, snapshots))
    return run
