"""Versioned state and atomic artifact storage."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable

from .integrity import build_manifest, verify_manifest
from .models import Snapshot
from .util import atomic_write_text, exclusive_lock, sha256_json


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_snapshot_set(directory: Path, snapshots: Iterable[Snapshot]) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    source_files: list[dict[str, Any]] = []
    for snapshot in snapshots:
        path = directory / f"{snapshot.source_id}.snapshot.json"
        atomic_write_text(path, _json_text(snapshot.to_dict()))
        source_files.append(
            {
                "source_id": snapshot.source_id,
                "path": path.name,
                "snapshot_sha256": sha256_json(snapshot.to_dict()),
                "normalized_sha256": snapshot.normalized_sha256,
                "status": snapshot.status,
            }
        )
    index = {"schema_version": 1, "sources": source_files}
    atomic_write_text(directory / "snapshot-index.json", _json_text(index))
    manifest = build_manifest(directory)
    atomic_write_text(directory / "manifest.json", _json_text(manifest))
    return index


def load_snapshot(path: Path) -> Snapshot:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Snapshot(
        schema_version=data["schema_version"],
        source_id=data["source_id"],
        title=data["title"],
        locator=data["locator"],
        independence_group=data["independence_group"],
        source_format=data["source_format"],
        priority=data["priority"],
        observed_at=data["observed_at"],
        input_path=data["input_path"],
        status=data["status"],
        raw_sha256=data.get("raw_sha256"),
        normalized_sha256=data.get("normalized_sha256"),
        normalizer_version=data["normalizer_version"],
        normalized=data.get("normalized"),
        raw_bytes=data["raw_bytes"],
        error=data.get("error"),
    )


def load_snapshot_set(directory: Path) -> dict[str, Snapshot]:
    ok, errors = verify_manifest(directory)
    if not ok:
        raise ValueError("snapshot manifest failed: " + "; ".join(errors))
    index = json.loads((directory / "snapshot-index.json").read_text(encoding="utf-8"))
    result: dict[str, Snapshot] = {}
    for item in index["sources"]:
        snapshot = load_snapshot(directory / item["path"])
        if snapshot.source_id != item["source_id"]:
            raise ValueError(f"snapshot index mismatch for {item['source_id']}")
        if sha256_json(snapshot.to_dict()) != item["snapshot_sha256"]:
            raise ValueError(f"snapshot envelope hash mismatch for {item['source_id']}")
        result[snapshot.source_id] = snapshot
    return result


def load_latest_state(state_dir: Path) -> tuple[str | None, dict[str, Snapshot]]:
    index_path = state_dir / "index.json"
    if not index_path.exists():
        return None, {}
    index = json.loads(index_path.read_text(encoding="utf-8"))
    run_id = index.get("latest_run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("state index has no latest_run_id")
    snapshot_dir = state_dir / "snapshots" / run_id
    return run_id, load_snapshot_set(snapshot_dir)


def commit_state(state_dir: Path, run_id: str, snapshots: tuple[Snapshot, ...]) -> Path:
    snapshots_root = state_dir / "snapshots"
    destination = snapshots_root / run_id
    with exclusive_lock(state_dir / ".lock"):
        state_dir.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            existing = load_snapshot_set(destination)
            incoming = {item.source_id: item.to_dict() for item in snapshots}
            current = {key: value.to_dict() for key, value in existing.items()}
            if incoming != current:
                raise FileExistsError(f"state snapshot conflict for run_id {run_id}")
        else:
            snapshots_root.mkdir(parents=True, exist_ok=True)
            temporary = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=snapshots_root))
            try:
                write_snapshot_set(temporary, snapshots)
                os.replace(temporary, destination)
            except BaseException:
                shutil.rmtree(temporary, ignore_errors=True)
                raise
        pointer = {
            "schema_version": 1,
            "latest_run_id": run_id,
            "snapshot_directory": f"snapshots/{run_id}",
        }
        atomic_write_text(state_dir / "index.json", _json_text(pointer))
    return destination
