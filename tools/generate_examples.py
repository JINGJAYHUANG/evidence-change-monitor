#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
import shutil
import tempfile
from pathlib import Path

from evidence_change_monitor.config import load_registry
from evidence_change_monitor.runner import run_monitor

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic_public_monitor"
GENERATED = EXAMPLE / "generated"


def generate(target: Path) -> None:
    registry = load_registry(EXAMPLE / "registry.json", strict=True)
    state = target / "state"
    run_monitor(
        registry,
        input_dir=EXAMPLE / "baseline",
        state_dir=state,
        output_dir=target / "baseline-run",
        as_of="2026-08-29T00:00:00Z",
        commit=True,
    )
    run_monitor(
        registry,
        input_dir=EXAMPLE / "current",
        state_dir=state,
        output_dir=target / "current-run",
        as_of="2026-08-30T08:00:00Z",
        commit=True,
    )


def _tree(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def check_generated() -> None:
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        generate(temporary)
        produced = temporary / "current-run"
        expected = _tree(GENERATED) if GENERATED.is_dir() else {}
        actual = _tree(produced)
        if expected != actual:
            missing = sorted(set(actual) - set(expected))
            extra = sorted(set(expected) - set(actual))
            changed = sorted(
                key for key in set(actual) & set(expected)
                if actual[key] != expected[key]
            )
            raise SystemExit(
                f"generated example drift: missing={missing}, extra={extra}, changed={changed}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_generated()
        print("generated example is current")
        return 0
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        generate(temporary)
        produced = temporary / "current-run"
        if GENERATED.exists():
            shutil.rmtree(GENERATED)
        shutil.copytree(produced, GENERATED)
    print(GENERATED)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
