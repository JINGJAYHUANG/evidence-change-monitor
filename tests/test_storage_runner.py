from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evidence_change_monitor.capture import capture_all
from evidence_change_monitor.integrity import verify_manifest
from evidence_change_monitor.runner import run_monitor
from evidence_change_monitor.storage import (
    commit_state,
    load_latest_state,
    load_snapshot_set,
    write_snapshot_set,
)

from helpers import EXAMPLE, cloned_registry


class StorageTests(unittest.TestCase):
    def test_snapshot_set_roundtrip(self) -> None:
        registry = cloned_registry()
        snapshots = capture_all(registry, EXAMPLE / "baseline", "2026-08-29T00:00:00Z")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "snapshots"
            write_snapshot_set(target, snapshots)
            loaded = load_snapshot_set(target)
            self.assertEqual(set(loaded), {item.source_id for item in snapshots})
            self.assertTrue(verify_manifest(target)[0])

    def test_manifest_detects_tampering(self) -> None:
        registry = cloned_registry()
        snapshots = capture_all(registry, EXAMPLE / "baseline", "2026-08-29T00:00:00Z")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "snapshots"
            write_snapshot_set(target, snapshots)
            (target / "service-status.snapshot.json").write_text("{}\n", encoding="utf-8")
            ok, errors = verify_manifest(target)
            self.assertFalse(ok)
            self.assertTrue(any("service-status" in item for item in errors))

    def test_commit_state_and_load_latest(self) -> None:
        registry = cloned_registry()
        snapshots = capture_all(registry, EXAMPLE / "baseline", "2026-08-29T00:00:00Z")
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            commit_state(state, "run-one", snapshots)
            run_id, loaded = load_latest_state(state)
            self.assertEqual(run_id, "run-one")
            self.assertEqual(len(loaded), 4)

    def test_identical_state_commit_is_idempotent(self) -> None:
        registry = cloned_registry()
        snapshots = capture_all(registry, EXAMPLE / "baseline", "2026-08-29T00:00:00Z")
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            first = commit_state(state, "run-one", snapshots)
            second = commit_state(state, "run-one", snapshots)
            self.assertEqual(first, second)

    def test_conflicting_state_run_id_fails(self) -> None:
        registry = cloned_registry()
        baseline = capture_all(registry, EXAMPLE / "baseline", "2026-08-29T00:00:00Z")
        current = capture_all(registry, EXAMPLE / "current", "2026-08-30T08:00:00Z")
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            commit_state(state, "same-run", baseline)
            with self.assertRaises(FileExistsError):
                commit_state(state, "same-run", current)


class RunnerTests(unittest.TestCase):
    def test_two_run_demo_has_expected_summary(self) -> None:
        registry = cloned_registry()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            state = base / "state"
            run_monitor(
                registry,
                input_dir=EXAMPLE / "baseline",
                state_dir=state,
                output_dir=base / "baseline-run",
                as_of="2026-08-29T00:00:00Z",
                commit=True,
            )
            current = run_monitor(
                registry,
                input_dir=EXAMPLE / "current",
                state_dir=state,
                output_dir=base / "current-run",
                as_of="2026-08-30T08:00:00Z",
                commit=True,
            )
            self.assertEqual(current.summary["failed_source_count"], 0)
            self.assertEqual(current.summary["ignored_change_count"], 1)
            self.assertEqual(current.summary["highest_severity"], "critical")
            self.assertGreaterEqual(current.summary["material_event_count"], 5)
            self.assertTrue((base / "current-run" / "report.html").is_file())
            self.assertTrue(verify_manifest(base / "current-run")[0])

    def test_dry_run_does_not_update_state(self) -> None:
        registry = cloned_registry()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            state = base / "state"
            run_monitor(
                registry,
                input_dir=EXAMPLE / "baseline",
                state_dir=state,
                output_dir=base / "run",
                as_of="2026-08-29T00:00:00Z",
                commit=False,
            )
            self.assertFalse((state / "index.json").exists())

    def test_same_inputs_and_as_of_are_deterministic(self) -> None:
        registry = cloned_registry()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            first = run_monitor(
                registry,
                input_dir=EXAMPLE / "baseline",
                state_dir=base / "state-a",
                output_dir=base / "run-a",
                as_of="2026-08-29T00:00:00Z",
                commit=False,
            )
            second = run_monitor(
                registry,
                input_dir=EXAMPLE / "baseline",
                state_dir=base / "state-b",
                output_dir=base / "run-b",
                as_of="2026-08-29T00:00:00Z",
                commit=False,
            )
            self.assertEqual(first.to_dict(), second.to_dict())
            self.assertEqual(
                (base / "run-a" / "report.md").read_bytes(),
                (base / "run-b" / "report.md").read_bytes(),
            )

    def test_failed_capture_retains_last_known_good_baseline(self) -> None:
        registry = cloned_registry()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            state = base / "state"
            run_monitor(
                registry,
                input_dir=EXAMPLE / "baseline",
                state_dir=state,
                output_dir=base / "baseline-run",
                as_of="2026-08-29T00:00:00Z",
                commit=True,
            )
            broken = base / "broken"
            broken.mkdir()
            for path in (EXAMPLE / "current").iterdir():
                if path.name != "policy-notice.html":
                    (broken / path.name).write_bytes(path.read_bytes())
            result = run_monitor(
                registry,
                input_dir=broken,
                state_dir=state,
                output_dir=base / "broken-run",
                as_of="2026-08-30T08:00:00Z",
                commit=True,
            )
            self.assertEqual(result.summary["failed_source_count"], 1)
            latest_id, latest = load_latest_state(state)
            self.assertEqual(latest_id, result.run_id)
            self.assertEqual(latest["policy-notice"].observed_at, "2026-08-29T00:00:00Z")

    def test_first_run_records_first_seen_events(self) -> None:
        registry = cloned_registry()
        with tempfile.TemporaryDirectory() as directory:
            result = run_monitor(
                registry,
                input_dir=EXAMPLE / "baseline",
                state_dir=Path(directory) / "state",
                output_dir=Path(directory) / "run",
                as_of="2026-08-29T00:00:00Z",
                commit=False,
            )
            self.assertEqual(
                {event.change_type for event in result.events},
                {"source.first_seen"},
            )


if __name__ == "__main__":
    unittest.main()
