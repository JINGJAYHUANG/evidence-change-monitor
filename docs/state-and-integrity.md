# State and Integrity

State is versioned:

```text
state/
├── index.json
└── snapshots/
    └── <run-id>/
        ├── <source-id>.snapshot.json
        ├── snapshot-index.json
        └── manifest.json
```

Promotion uses an exclusive lock and an atomic pointer update. If the destination run ID already exists with different content, the operation fails.

When a current capture fails and a prior usable snapshot exists, the next state retains the prior snapshot. This prevents a missing file from becoming the new empty baseline.

The state lock is a process-level coordination mechanism. It is not a distributed consensus protocol; multiple hosts sharing eventually consistent storage require an external lock service.
