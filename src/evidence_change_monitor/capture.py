"""Capture local source files into deterministic snapshot envelopes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import NORMALIZER_VERSION, SCHEMA_VERSION
from .models import Snapshot
from .normalization import normalize_bytes
from .util import read_regular_file, resolve_beneath, sha256_bytes


def capture_source(source: dict[str, Any], input_root: Path, observed_at: str, default_max_bytes: int) -> Snapshot:
    source_id = source["source_id"]
    path = resolve_beneath(input_root, source["input_path"])
    max_bytes = int(source.get("max_bytes", default_max_bytes))
    base = {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "title": source["title"],
        "locator": source["locator"],
        "independence_group": source["independence_group"],
        "source_format": source["format"],
        "priority": source["priority"],
        "observed_at": observed_at,
        "input_path": source["input_path"],
        "normalizer_version": NORMALIZER_VERSION,
    }
    try:
        data = read_regular_file(path, max_bytes=max_bytes)
    except FileNotFoundError:
        return Snapshot(
            **base,
            status="missing",
            raw_sha256=None,
            normalized_sha256=None,
            normalized=None,
            raw_bytes=0,
            error="input file was not found",
        )
    except OverflowError as exc:
        return Snapshot(
            **base,
            status="oversize",
            raw_sha256=None,
            normalized_sha256=None,
            normalized=None,
            raw_bytes=path.stat().st_size if path.exists() else 0,
            error=str(exc),
        )
    except (OSError, ValueError) as exc:
        return Snapshot(
            **base,
            status="error",
            raw_sha256=None,
            normalized_sha256=None,
            normalized=None,
            raw_bytes=0,
            error=str(exc),
        )

    raw_sha = sha256_bytes(data)
    try:
        normalized, normalized_sha = normalize_bytes(
            data,
            source_format=source["format"],
            encoding=source.get("encoding", "utf-8"),
            options=source.get("normalization", {}),
        )
    except (UnicodeError, ValueError, TypeError) as exc:
        return Snapshot(
            **base,
            status="parse_error",
            raw_sha256=raw_sha,
            normalized_sha256=None,
            normalized=None,
            raw_bytes=len(data),
            error=f"{type(exc).__name__}: {exc}",
        )
    return Snapshot(
        **base,
        status="ok",
        raw_sha256=raw_sha,
        normalized_sha256=normalized_sha,
        normalized=normalized,
        raw_bytes=len(data),
        error=None,
    )


def capture_all(registry: dict[str, Any], input_root: Path, observed_at: str) -> tuple[Snapshot, ...]:
    return tuple(
        capture_source(source, input_root, observed_at, int(registry.get("default_max_bytes", 1_000_000)))
        for source in registry["sources"]
    )
