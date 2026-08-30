# Architecture

```text
registry.json
    │
    ├── source identity, format, priority, independence group
    ├── normalization scope
    └── severity rules
             │
explicit capture directory
             │
     safe regular-file reader
             │
 format-specific normalizer
             │
 raw hash + normalized hash
             │
 last committed state ─── structured diff
             │                  │
             └──────────── change events
                                │
                          severity promotion
                                │
                  JSON / Markdown / HTML / CSV
                                │
                       integrity manifest
                                │
                    optional state commit
```

The acquisition boundary is outside the v0.1.0 core. This permits a separate process to use a browser, HTTP client, document connector, or manual export without giving those credentials or network privileges to the comparison engine.

State snapshots are versioned under `state/snapshots/<run_id>`. `state/index.json` is the atomic pointer to the latest committed baseline. Failed current captures retain the previous last-known-good snapshot when one exists.
