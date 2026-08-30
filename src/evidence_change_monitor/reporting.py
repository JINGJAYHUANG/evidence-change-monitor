"""Deterministic JSON, Markdown, HTML, and CSV reports."""

from __future__ import annotations

import csv
import html
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .models import MonitorRun
from .util import atomic_write_text


def run_json(run: MonitorRun) -> str:
    return json.dumps(run.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def run_markdown(run: MonitorRun) -> str:
    data = run.to_dict()
    lines = [
        f"# Evidence Change Report — {data['monitor_id']}",
        "",
        f"- **Run ID:** `{data['run_id']}`",
        f"- **As of:** `{data['as_of']}`",
        f"- **Baseline run:** `{data['baseline_run_id'] or 'none'}`",
        f"- **Sources captured:** `{data['current_snapshot_count']}`",
        f"- **Material events:** `{data['summary']['material_event_count']}`",
        f"- **Ignored normalized changes:** `{data['summary']['ignored_change_count']}`",
        f"- **Failed sources:** `{data['summary']['failed_source_count']}`",
        "",
        "## Decision boundary",
        "",
        "A detected event proves that the monitored representation changed between the named snapshots. "
        "It does not prove causality, legal effect, completeness, source truthfulness, or operational impact.",
        "",
        "## Source outcomes",
        "",
        "| Source | Status | Raw changed | Monitored content changed | Events |",
        "|---|---|---:|---:|---:|",
    ]
    for item in data["source_outcomes"]:
        lines.append(
            f"| `{item['source_id']}` | `{item['status']}` | "
            f"{'yes' if item['raw_changed'] else 'no'} | "
            f"{'yes' if item['normalized_changed'] else 'no'} | {item['event_count']} |"
        )
    lines.extend(["", "## Events", ""])
    if not data["events"]:
        lines.append("No events were produced within the configured monitoring scope.")
    for event in data["events"]:
        lines.extend(
            [
                f"### [{event['severity'].upper()}] {event['source_title']} — `{event['change_type']}`",
                "",
                f"- **Event ID:** `{event['event_id']}`",
                (
                    f"- **Source:** [{event['locator']}]({event['locator']})"
                    if event["locator"].startswith("https://")
                    else f"- **Source:** `{event['locator']}`"
                ),
                f"- **Independence group:** `{event['independence_group']}`",
                f"- **Path:** `{event['path'] or 'n/a'}`",
                f"- **Summary:** {event['summary']}",
                f"- **Before:** `{_fmt(event['before'])}`",
                f"- **After:** `{_fmt(event['after'])}`",
                f"- **Matched rules:** `{', '.join(event['matched_rule_ids']) or 'none'}`",
                f"- **Tags:** `{', '.join(event['tags']) or 'none'}`",
                "",
            ]
        )
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in data["limitations"])
    return "\n".join(lines).rstrip() + "\n"


def run_html(run: MonitorRun) -> str:
    data = run.to_dict()
    cards = []
    for event in data["events"]:
        cards.append(
            f"""<article class="event severity-{html.escape(event['severity'])}">
<h3>{html.escape(event['source_title'])}</h3>
<p><code>{html.escape(event['change_type'])}</code> · <strong>{html.escape(event['severity'].upper())}</strong></p>
<p>{html.escape(event['summary'])}</p>
<dl>
<dt>Path</dt><dd><code>{html.escape(event['path'] or 'n/a')}</code></dd>
<dt>Before</dt><dd><code>{html.escape(_fmt(event['before']))}</code></dd>
<dt>After</dt><dd><code>{html.escape(_fmt(event['after']))}</code></dd>
<dt>Rules</dt><dd>{html.escape(', '.join(event['matched_rule_ids']) or 'none')}</dd>
</dl>
<p><a href="{html.escape(event['locator'], quote=True)}" rel="noreferrer">Source locator</a></p>
</article>"""
        )
    outcomes = "".join(
        "<tr>"
        f"<td><code>{html.escape(item['source_id'])}</code></td>"
        f"<td>{html.escape(item['status'])}</td>"
        f"<td>{'yes' if item['raw_changed'] else 'no'}</td>"
        f"<td>{'yes' if item['normalized_changed'] else 'no'}</td>"
        f"<td>{item['event_count']}</td>"
        "</tr>"
        for item in data["source_outcomes"]
    )
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in data["limitations"])
    events = "\n".join(cards) if cards else "<p>No events were produced within the configured scope.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evidence Change Report — {html.escape(data['monitor_id'])}</title>
<style>
:root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
body {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1rem; line-height: 1.55; }}
header, section {{ margin-bottom: 2rem; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .8rem; }}
.metric, .event {{ border: 1px solid #8886; border-radius: .7rem; padding: 1rem; overflow-wrap: anywhere; }}
.events {{ display: grid; gap: 1rem; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border-bottom: 1px solid #8885; padding: .6rem; text-align: left; }}
.table-wrap {{ overflow-x: auto; }}
code {{ overflow-wrap: anywhere; }}
.severity-critical {{ border-inline-start: .45rem solid currentColor; }}
.severity-high {{ border-inline-start: .35rem solid currentColor; }}
@media (max-width: 520px) {{ body {{ padding: 1rem .7rem; }} }}
@media print {{ a {{ color: inherit; text-decoration: none; }} .event {{ break-inside: avoid; }} }}
</style>
</head>
<body>
<header>
<h1>Evidence Change Report</h1>
<p><strong>{html.escape(data['monitor_id'])}</strong> · as of <code>{html.escape(data['as_of'])}</code></p>
<p>A detected event proves only that the monitored representation changed between the named snapshots.</p>
</header>
<section class="summary">
<div class="metric"><strong>{data['summary']['material_event_count']}</strong><br>material events</div>
<div class="metric"><strong>{data['summary']['ignored_change_count']}</strong><br>ignored normalized changes</div>
<div class="metric"><strong>{data['summary']['failed_source_count']}</strong><br>failed sources</div>
<div class="metric"><strong>{data['current_snapshot_count']}</strong><br>captured sources</div>
</section>
<section>
<h2>Source outcomes</h2>
<div class="table-wrap"><table>
<thead><tr><th>Source</th><th>Status</th><th>Raw changed</th><th>Monitored changed</th><th>Events</th></tr></thead>
<tbody>{outcomes}</tbody>
</table></div>
</section>
<section>
<h2>Events</h2>
<div class="events">{events}</div>
</section>
<section>
<h2>Limitations</h2>
<ul>{limitations}</ul>
</section>
</body>
</html>
"""


def _spreadsheet_safe(value: Any) -> str:
    text = _fmt(value)
    if text and text[0] in "=+-@":
        return "'" + text
    return text


def run_csv(run: MonitorRun) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "event_id",
            "source_id",
            "change_type",
            "severity",
            "observed_at",
            "path",
            "summary",
            "before",
            "after",
            "matched_rule_ids",
            "tags",
        ]
    )
    for event in run.events:
        writer.writerow(
            [
                event.event_id,
                event.source_id,
                event.change_type,
                event.severity,
                event.observed_at,
                event.path or "",
                _spreadsheet_safe(event.summary),
                _spreadsheet_safe(event.before),
                _spreadsheet_safe(event.after),
                ",".join(event.matched_rule_ids),
                ",".join(event.tags),
            ]
        )
    return buffer.getvalue()


def write_reports(run: MonitorRun, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(output_dir / "run.json", run_json(run))
    atomic_write_text(output_dir / "report.md", run_markdown(run))
    atomic_write_text(output_dir / "report.html", run_html(run))
    atomic_write_text(output_dir / "events.csv", run_csv(run))
