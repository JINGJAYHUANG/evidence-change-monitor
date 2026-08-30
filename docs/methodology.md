# Methodology

## 1. Define the claim surface

A monitoring registry should state what representation is captured, where it came from, which parser is used, and which volatile fields are intentionally excluded.

## 2. Preserve two hashes

- `raw_sha256` records the exact captured bytes.
- `normalized_sha256` records the monitored representation.

A raw-only difference may be noise, formatting, timestamps, or a genuine change hidden by an over-broad normalization rule. The system therefore reports it as `content.normalized_unchanged` rather than silently calling the source unchanged.

## 3. Compare structure where possible

- text and HTML use normalized line blocks;
- JSON uses JSON Pointer paths;
- RSS and Atom use stable item identifiers;
- source capture failures remain events rather than empty content.

## 4. Apply severity after detection

Detection identifies what changed. Severity rules express a decision context. They are separate so a policy keyword can promote an event without changing the underlying evidence.

## 5. Commit state only after a complete run

A run writes reports and integrity metadata before optional state promotion. A failed capture does not erase a prior usable baseline.

## 6. Keep conclusions bounded

No change event is automatically a truth claim, causal claim, legal conclusion, or business recommendation.
