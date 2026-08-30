# Synthetic Public Monitor Example

This fixture contains four fictional source types:

1. an HTML policy notice;
2. JSON release metadata;
3. an Atom research feed;
4. a plain-text service status.

The baseline is captured on `2026-08-29T00:00:00Z`. The current snapshot is captured on `2026-08-30T08:00:00Z`.

Expected current-run behavior:

- policy suspension promoted to `critical`;
- minimum Python compatibility promoted to `high`;
- release version change at the source-priority default;
- one feed item added and one modified;
- a whitespace-only raw change reported as `content.normalized_unchanged`.

Everything is synthetic. The example does not claim that any real policy, software release, research finding, or service status changed.
