# Scheduling

The core is scheduler-agnostic.

Recommended patterns:

- **manual** for a new source or changing normalization rules;
- **event-driven** when an upstream export or connector produces a capture;
- **cron** when capture timing is fixed and source semantics are stable;
- **workflow** when acquisition, human review, notification, and archival require checkpoints;
- **heartbeat** only for lightweight context-aware review, not high-impact external actions.

A scheduler success means the process ran. It does not mean every source was captured or that no material change occurred. Inspect the per-source outcomes and failed-source count.
