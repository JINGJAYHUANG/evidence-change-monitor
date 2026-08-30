from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evidence_change_monitor.models import ChangeEvent, MonitorRun
from evidence_change_monitor.reporting import run_csv, run_html, run_markdown


def sample_run(summary_text: str = "Changed") -> MonitorRun:
    event = ChangeEvent(
        event_id="a" * 24,
        source_id="sample",
        source_title="<Synthetic>",
        locator="https://example.invalid/item?x=1&y=2",
        independence_group="synthetic",
        change_type="text.modified",
        severity="high",
        observed_at="2026-08-30T00:00:00Z",
        baseline_sha256="b" * 64,
        current_sha256="c" * 64,
        path="lines:1-1:1-1",
        before="<old>",
        after="=danger",
        summary=summary_text,
        matched_rule_ids=("rule-one",),
        tags=("tag-one",),
    )
    return MonitorRun(
        schema_version=1,
        monitor_id="sample-monitor",
        run_id="2026-08-30-example",
        as_of="2026-08-30T00:00:00Z",
        registry_sha256="d" * 64,
        baseline_run_id=None,
        current_snapshot_count=1,
        events=(event,),
        source_outcomes=(
            {
                "source_id": "sample",
                "status": "changed",
                "raw_changed": True,
                "normalized_changed": True,
                "event_count": 1,
                "baseline_status": "ok",
                "current_status": "ok",
            },
        ),
        summary={
            "event_count": 1,
            "material_event_count": 1,
            "ignored_change_count": 0,
            "failed_source_count": 0,
            "severity_counts": {"high": 1},
            "change_type_counts": {"text.modified": 1},
            "highest_severity": "high",
        },
        limitations=("Synthetic limitation.",),
    )


class ReportingTests(unittest.TestCase):
    def test_html_escapes_untrusted_values(self) -> None:
        output = run_html(sample_run())
        self.assertIn("&lt;Synthetic&gt;", output)
        self.assertIn("&lt;old&gt;", output)
        self.assertNotIn("<old>", output)
        self.assertIn("rel=\"noreferrer\"", output)

    def test_markdown_states_decision_boundary(self) -> None:
        output = run_markdown(sample_run())
        self.assertIn("does not prove causality", output)
        self.assertIn("Source outcomes", output)

    def test_csv_neutralizes_formula_prefix(self) -> None:
        output = run_csv(sample_run(summary_text="+SUM(A1:A2)"))
        self.assertIn("'+SUM(A1:A2)", output)
        self.assertIn("'=danger", output)

    def test_html_is_standalone(self) -> None:
        output = run_html(sample_run())
        self.assertIn("<!doctype html>", output)
        self.assertNotIn("<script", output.casefold())
        self.assertNotIn("src=\"http", output.casefold())


if __name__ == "__main__":
    unittest.main()
