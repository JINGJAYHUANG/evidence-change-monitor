# Data Dictionary

## Registry

| Field | Meaning |
|---|---|
| `monitor_id` | Stable identifier for one monitoring contract |
| `source_id` | Stable source identifier |
| `locator` | Public HTTPS locator or non-network URN |
| `input_path` | Relative local capture path |
| `format` | Text, HTML, JSON, or feed parser |
| `priority` | Base operational triage priority |
| `independence_group` | Declared source family |
| `normalization` | Explicit monitored-scope rules |
| `severity_rules` | Post-detection promotion rules |

## Snapshot

| Field | Meaning |
|---|---|
| `status` | `ok`, `missing`, `oversize`, `parse_error`, or `error` |
| `raw_sha256` | Hash of exact captured bytes |
| `normalized_sha256` | Hash of the monitored representation |
| `normalized` | Deterministic parser output |
| `observed_at` | Explicit timezone-aware capture timestamp |

## Run

| Field | Meaning |
|---|---|
| `baseline_run_id` | State pointer used for comparison |
| `source_outcomes` | Per-source capture and comparison status |
| `events` | Evidence-preserving structured changes |
| `summary` | Counts and highest detected severity |
| `limitations` | Explicit interpretation constraints |
