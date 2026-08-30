"""Integrity manifests for run artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .util import canonical_json_bytes, sha256_bytes


def build_manifest(directory: Path, *, exclude: set[str] | None = None) -> dict[str, Any]:
    exclude = exclude or {"manifest.json"}
    entries: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(directory).as_posix()
        if relative in exclude:
            continue
        data = path.read_bytes()
        entries.append({"path": relative, "bytes": len(data), "sha256": sha256_bytes(data)})
    payload = {"schema_version": 1, "files": entries}
    payload["manifest_sha256"] = sha256_bytes(canonical_json_bytes(payload["files"]))
    return payload


def verify_manifest(directory: Path) -> tuple[bool, list[str]]:
    path = directory / "manifest.json"
    if not path.is_file():
        return False, ["manifest.json is missing"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, [f"manifest cannot be read: {exc}"]
    errors: list[str] = []
    expected_files = manifest.get("files", [])
    expected_hash = manifest.get("manifest_sha256")
    if expected_hash != sha256_bytes(canonical_json_bytes(expected_files)):
        errors.append("manifest_sha256 does not match the file entry list")
    for entry in expected_files:
        relative = entry.get("path")
        if not isinstance(relative, str):
            errors.append("manifest entry has no valid path")
            continue
        target = directory / relative
        if target.is_symlink() or not target.is_file():
            errors.append(f"missing or non-regular artifact: {relative}")
            continue
        data = target.read_bytes()
        if len(data) != entry.get("bytes"):
            errors.append(f"byte count mismatch: {relative}")
        if sha256_bytes(data) != entry.get("sha256"):
            errors.append(f"sha256 mismatch: {relative}")
    return not errors, errors
