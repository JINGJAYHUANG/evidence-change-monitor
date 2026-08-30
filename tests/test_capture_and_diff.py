from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from evidence_change_monitor.capture import capture_all, capture_source
from evidence_change_monitor.diffing import compare_snapshots
from evidence_change_monitor.models import Snapshot

from helpers import EXAMPLE, cloned_registry


class CaptureTests(unittest.TestCase):
    def test_example_capture_is_complete(self) -> None:
        registry = cloned_registry()
        snapshots = capture_all(registry, EXAMPLE / "baseline", "2026-08-29T00:00:00Z")
        self.assertEqual(len(snapshots), 4)
        self.assertTrue(all(item.status == "ok" for item in snapshots))

    def test_missing_file_is_explicit(self) -> None:
        registry = cloned_registry()
        with tempfile.TemporaryDirectory() as directory:
            snapshot = capture_source(
                registry["sources"][0],
                Path(directory),
                "2026-08-30T00:00:00Z",
                1000,
            )
        self.assertEqual(snapshot.status, "missing")
        self.assertIsNone(snapshot.normalized_sha256)

    def test_oversize_file_is_explicit(self) -> None:
        registry = cloned_registry()
        source = registry["sources"][3]
        source["max_bytes"] = 3
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, source["input_path"]).write_text("too large", encoding="utf-8")
            snapshot = capture_source(source, Path(directory), "2026-08-30T00:00:00Z", 1000)
        self.assertEqual(snapshot.status, "oversize")

    def test_invalid_json_is_parse_error(self) -> None:
        registry = cloned_registry()
        source = registry["sources"][1]
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, source["input_path"]).write_text("{", encoding="utf-8")
            snapshot = capture_source(source, Path(directory), "2026-08-30T00:00:00Z", 1000)
        self.assertEqual(snapshot.status, "parse_error")

    @unittest.skipIf(not hasattr(os, "symlink"), "symbolic links unavailable")
    def test_symlink_input_is_not_followed(self) -> None:
        registry = cloned_registry()
        source = registry["sources"][3]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "outside.txt"
            target.write_text("secret", encoding="utf-8")
            os.symlink(target, base / source["input_path"])
            snapshot = capture_source(source, base, "2026-08-30T00:00:00Z", 1000)
        self.assertEqual(snapshot.status, "error")
        self.assertIn("symbolic", snapshot.error or "")


class DiffTests(unittest.TestCase):
    def _captured(self):
        registry = cloned_registry()
        baseline = {x.source_id: x for x in capture_all(registry, EXAMPLE / "baseline", "2026-08-29T00:00:00Z")}
        current = {x.source_id: x for x in capture_all(registry, EXAMPLE / "current", "2026-08-30T08:00:00Z")}
        sources = {x["source_id"]: x for x in registry["sources"]}
        return registry, baseline, current, sources

    def test_policy_change_is_critical(self) -> None:
        registry, baseline, current, sources = self._captured()
        events, outcome = compare_snapshots(
            baseline["policy-notice"],
            current["policy-notice"],
            sources["policy-notice"],
            registry["severity_rules"],
        )
        self.assertEqual(outcome["status"], "changed")
        self.assertTrue(any(event.severity == "critical" for event in events))
        self.assertTrue(any("policy-suspension" in event.matched_rule_ids for event in events))

    def test_json_diff_uses_pointer(self) -> None:
        registry, baseline, current, sources = self._captured()
        events, _ = compare_snapshots(
            baseline["release-metadata"],
            current["release-metadata"],
            sources["release-metadata"],
            registry["severity_rules"],
        )
        pointers = {event.path for event in events}
        self.assertIn("/compatibility/minimum_python", pointers)
        self.assertIn("/version", pointers)

    def test_ignored_json_pointer_produces_no_generated_at_event(self) -> None:
        registry, baseline, current, sources = self._captured()
        events, _ = compare_snapshots(
            baseline["release-metadata"],
            current["release-metadata"],
            sources["release-metadata"],
            registry["severity_rules"],
        )
        self.assertNotIn("/generated_at", {event.path for event in events})

    def test_feed_added_and_modified(self) -> None:
        registry, baseline, current, sources = self._captured()
        events, _ = compare_snapshots(
            baseline["research-feed"],
            current["research-feed"],
            sources["research-feed"],
            registry["severity_rules"],
        )
        types = {event.change_type for event in events}
        self.assertIn("feed.item_added", types)
        self.assertIn("feed.item_modified", types)

    def test_raw_only_change_is_explicit(self) -> None:
        registry, baseline, current, sources = self._captured()
        events, outcome = compare_snapshots(
            baseline["service-status"],
            current["service-status"],
            sources["service-status"],
            registry["severity_rules"],
        )
        self.assertEqual(outcome["status"], "ignored_change")
        self.assertEqual([event.change_type for event in events], ["content.normalized_unchanged"])

    def test_first_seen_is_distinct(self) -> None:
        registry, _, current, sources = self._captured()
        events, outcome = compare_snapshots(
            None,
            current["service-status"],
            sources["service-status"],
            registry["severity_rules"],
        )
        self.assertEqual(outcome["status"], "first_seen")
        self.assertEqual(events[0].change_type, "source.first_seen")

    def test_missing_source_has_high_minimum_severity(self) -> None:
        registry, baseline, current, sources = self._captured()
        missing = Snapshot(**{**current["service-status"].to_dict(), "status": "missing", "normalized": None,
                              "normalized_sha256": None, "raw_sha256": None, "raw_bytes": 0,
                              "error": "input file was not found"})
        events, _ = compare_snapshots(
            baseline["service-status"],
            missing,
            sources["service-status"],
            registry["severity_rules"],
        )
        self.assertEqual(events[0].severity, "high")
        self.assertEqual(events[0].change_type, "source.missing")

    def test_event_ids_are_stable(self) -> None:
        registry, baseline, current, sources = self._captured()
        first, _ = compare_snapshots(
            baseline["release-metadata"], current["release-metadata"],
            sources["release-metadata"], registry["severity_rules"],
        )
        second, _ = compare_snapshots(
            baseline["release-metadata"], current["release-metadata"],
            sources["release-metadata"], registry["severity_rules"],
        )
        self.assertEqual([x.event_id for x in first], [x.event_id for x in second])


if __name__ == "__main__":
    unittest.main()
