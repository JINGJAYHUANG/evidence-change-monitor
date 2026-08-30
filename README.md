# Evidence Change Monitor

A deterministic, evidence-preserving pipeline for comparing captured public-source representations without confusing **change detection** with **truth, causality, legal effect, or materiality**.

The project separates five states that ordinary hash monitors often collapse:

1. **unchanged** — raw and normalized representations are unchanged;
2. **ignored change** — raw bytes changed, but configured normalization removed the difference;
3. **changed** — monitored normalized content changed;
4. **capture failure** — the source file was missing, oversized, unreadable, or unparsable;
5. **first seen** — no usable baseline existed.

## What v0.1.0 provides

- strict, versioned source registries;
- deterministic normalization for text, HTML, JSON, RSS, and Atom captures;
- line-level, JSON-pointer, and feed-item change events;
- source-priority and rule-based severity promotion;
- provenance fields for locator, source identity, independence group, timestamps, and hashes;
- versioned state with last-known-good retention for failed captures;
- atomic writes, exclusive state locking, and integrity manifests;
- deterministic JSON, Markdown, HTML, and spreadsheet-safe CSV reports;
- a fully synthetic multi-source example;
- Python 3.11–3.13 CI and reproducible Wheel verification.

## Deliberate v0.1.0 boundary

The core **does not fetch the network**. It consumes explicit local captures.

This makes acquisition independently reviewable and prevents the monitor from silently inheriting browser credentials, private network access, redirects, cookies, or an SSRF surface. A scheduler or dedicated acquisition process can place public captures into the input directory; this project then validates, normalizes, compares, stores, and reports them.

## Five-minute demonstration

```bash
python -m pip install -e .

rm -rf /tmp/evidence-monitor-demo
mkdir -p /tmp/evidence-monitor-demo/state

evidence-monitor run \
  --registry examples/synthetic_public_monitor/registry.json \
  --input-dir examples/synthetic_public_monitor/baseline \
  --state-dir /tmp/evidence-monitor-demo/state \
  --output-dir /tmp/evidence-monitor-demo/baseline-run \
  --as-of 2026-08-29T00:00:00Z \
  --commit-state

evidence-monitor run \
  --registry examples/synthetic_public_monitor/registry.json \
  --input-dir examples/synthetic_public_monitor/current \
  --state-dir /tmp/evidence-monitor-demo/state \
  --output-dir /tmp/evidence-monitor-demo/current-run \
  --as-of 2026-08-30T08:00:00Z \
  --commit-state

evidence-monitor verify /tmp/evidence-monitor-demo/current-run
```

The second run demonstrates:

- a critical policy suspension;
- a compatibility change in JSON;
- an updated and a newly added feed item;
- a raw whitespace change that normalizes to unchanged monitored content.

## Core commands

```text
evidence-monitor init
evidence-monitor validate
evidence-monitor capture
evidence-monitor run
evidence-monitor report
evidence-monitor verify
```

## Data flow

```text
explicit local captures
        ↓
strict source registry
        ↓
format-specific normalization
        ↓
raw + normalized SHA-256
        ↓
baseline/current structured diff
        ↓
severity and tagging rules
        ↓
JSON / Markdown / HTML / CSV
        ↓
integrity manifest
        ↓
optional atomic state commit
```

## Evidence semantics

A detected event establishes only that two captured, normalized representations differ within the configured scope. It does not establish:

- that the source is correct;
- that the underlying real-world state changed;
- why the change occurred;
- that the change is legally effective;
- that the change is material to a particular decision;
- that no other relevant source changed.

Likewise, “no detected change” means only that no monitored normalized difference was found between the available captures.

## Repository map

```text
src/evidence_change_monitor/   capture, normalize, diff, state, reports, CLI
config/                        public example registry
schemas/                       registry, snapshot, event, and run schemas
examples/synthetic_public_monitor/
                               synthetic baseline/current inputs and generated reports
docs/                          method, threat model, scheduling, and limits
tests/                         unit, integration, CLI, and publication tests
tools/                         example generation, schema/docs/workflow checks
.github/workflows/             pinned-SHA CI and release workflows
```

## Public boundary

The repository contains no:

- personal inbox or task contents;
- private monitoring targets;
- API keys, cookies, webhooks, or account credentials;
- private network addresses;
- autonomous background service;
- claim that an external source was checked in real time;
- claim that generated severity is a legal, medical, financial, or operational verdict.

See [the methodology](docs/methodology.md), [evidence model](docs/evidence-model.md), [threat model](docs/threat-model.md), and [Chinese overview](docs/README.zh-CN.md).
