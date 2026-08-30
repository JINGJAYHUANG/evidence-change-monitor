"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .capture import capture_all
from .config import load_registry, validate_registry
from .integrity import verify_manifest
from .reporting import run_csv, run_html, run_json, run_markdown
from .runner import run_monitor, validate_as_of
from .storage import load_snapshot_set, write_snapshot_set
from .version import __version__


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evidence-monitor",
        description="Evidence-preserving snapshot and change monitoring.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a registry or stored artifact directory.")
    validate.add_argument("path", type=Path)
    validate.add_argument("--strict", action="store_true")

    init = sub.add_parser("init", help="Create a starter registry and directory layout.")
    init.add_argument("directory", type=Path)

    capture = sub.add_parser("capture", help="Capture input files as a snapshot set.")
    capture.add_argument("--registry", type=Path, required=True)
    capture.add_argument("--input-dir", type=Path, required=True)
    capture.add_argument("--output-dir", type=Path, required=True)
    capture.add_argument("--as-of", required=True)

    run = sub.add_parser("run", help="Compare current inputs with the latest committed state.")
    run.add_argument("--registry", type=Path, required=True)
    run.add_argument("--input-dir", type=Path, required=True)
    run.add_argument("--state-dir", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--as-of", required=True)
    run.add_argument("--commit-state", action="store_true")

    report = sub.add_parser("report", help="Render a stored run.json.")
    report.add_argument("run_json", type=Path)
    report.add_argument("--format", choices=("json", "markdown", "html", "csv"), required=True)
    report.add_argument("--output", type=Path)

    verify = sub.add_parser("verify", help="Verify an integrity manifest.")
    verify.add_argument("directory", type=Path)
    return parser


def _starter_registry() -> dict:
    return {
        "schema_version": 1,
        "monitor_id": "starter-public-evidence",
        "title": "Starter Public Evidence Monitor",
        "timezone": "UTC",
        "default_max_bytes": 1000000,
        "sources": [
            {
                "source_id": "notice",
                "title": "Example notice",
                "locator": "urn:example:notice",
                "input_path": "notice.txt",
                "format": "text",
                "priority": "medium",
                "independence_group": "example-origin",
                "encoding": "utf-8",
                "normalization": {
                    "ignore_regexes": [],
                    "ignore_json_pointers": [],
                    "case_sensitive": True,
                    "collapse_whitespace": True,
                },
            }
        ],
        "severity_rules": [],
        "limitations": [
            "The monitor compares captured representations, not the full external source.",
            "A detected change does not prove legal effect, causality, truthfulness, or material impact.",
            "No detected change does not prove that the source or underlying reality was unchanged.",
        ],
    }


def _run_from_json(path: Path):
    from .models import ChangeEvent, MonitorRun

    data = json.loads(path.read_text(encoding="utf-8"))
    events = tuple(
        ChangeEvent(
            event_id=item["event_id"],
            source_id=item["source_id"],
            source_title=item["source_title"],
            locator=item["locator"],
            independence_group=item["independence_group"],
            change_type=item["change_type"],
            severity=item["severity"],
            observed_at=item["observed_at"],
            baseline_sha256=item.get("baseline_sha256"),
            current_sha256=item.get("current_sha256"),
            path=item.get("path"),
            before=item.get("before"),
            after=item.get("after"),
            summary=item["summary"],
            matched_rule_ids=tuple(item.get("matched_rule_ids", [])),
            tags=tuple(item.get("tags", [])),
        )
        for item in data["events"]
    )
    return MonitorRun(
        schema_version=data["schema_version"],
        monitor_id=data["monitor_id"],
        run_id=data["run_id"],
        as_of=data["as_of"],
        registry_sha256=data["registry_sha256"],
        baseline_run_id=data.get("baseline_run_id"),
        current_snapshot_count=data["current_snapshot_count"],
        events=events,
        source_outcomes=tuple(data["source_outcomes"]),
        summary=data["summary"],
        limitations=tuple(data["limitations"]),
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        if args.path.is_dir():
            ok, errors = verify_manifest(args.path)
            payload = {"ok": ok, "errors": errors}
        else:
            data = json.loads(args.path.read_text(encoding="utf-8"))
            payload = validate_registry(data, strict=args.strict).to_dict()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 1

    if args.command == "init":
        if args.directory.exists() and any(args.directory.iterdir()):
            raise SystemExit("target directory must be empty")
        args.directory.mkdir(parents=True, exist_ok=True)
        (args.directory / "inputs").mkdir()
        (args.directory / "state").mkdir()
        (args.directory / "runs").mkdir()
        (args.directory / "registry.json").write_text(
            json.dumps(_starter_registry(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.directory / "inputs" / "notice.txt").write_text("Initial notice.\n", encoding="utf-8")
        print(args.directory)
        return 0

    if args.command == "capture":
        registry = load_registry(args.registry, strict=True)
        as_of = validate_as_of(args.as_of)
        snapshots = capture_all(registry, args.input_dir, as_of)
        write_snapshot_set(args.output_dir, snapshots)
        print(json.dumps({"ok": True, "snapshots": len(snapshots)}, indent=2))
        return 0

    if args.command == "run":
        registry = load_registry(args.registry, strict=True)
        result = run_monitor(
            registry,
            input_dir=args.input_dir,
            state_dir=args.state_dir,
            output_dir=args.output_dir,
            as_of=args.as_of,
            commit=args.commit_state,
        )
        print(json.dumps(result.to_dict()["summary"], ensure_ascii=False, indent=2))
        return 0

    if args.command == "report":
        run = _run_from_json(args.run_json)
        renderers = {
            "json": run_json,
            "markdown": run_markdown,
            "html": run_html,
            "csv": run_csv,
        }
        text = renderers[args.format](run)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0

    if args.command == "verify":
        ok, errors = verify_manifest(args.directory)
        print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if ok else 1

    raise AssertionError(args.command)
