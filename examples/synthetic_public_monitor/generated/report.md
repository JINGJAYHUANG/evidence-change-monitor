# Evidence Change Report — synthetic-public-evidence

- **Run ID:** `2026-08-30-4a8e6631aa3ebf6a`
- **As of:** `2026-08-30T08:00:00Z`
- **Baseline run:** `2026-08-29-43f06d202db55226`
- **Sources captured:** `4`
- **Material events:** `5`
- **Ignored normalized changes:** `1`
- **Failed sources:** `0`

## Decision boundary

A detected event proves that the monitored representation changed between the named snapshots. It does not prove causality, legal effect, completeness, source truthfulness, or operational impact.

## Source outcomes

| Source | Status | Raw changed | Monitored content changed | Events |
|---|---|---:|---:|---:|
| `policy-notice` | `changed` | yes | yes | 1 |
| `release-metadata` | `changed` | yes | yes | 2 |
| `research-feed` | `changed` | yes | yes | 2 |
| `service-status` | `ignored_change` | yes | no | 1 |

## Events

### [CRITICAL] Synthetic policy notice — `text.modified`

- **Event ID:** `675cf95fb911efa5c4491894`
- **Source:** [https://example.invalid/policy-notice](https://example.invalid/policy-notice)
- **Independence group:** `synthetic-authority`
- **Path:** `lines:2-2:2-2`
- **Summary:** Replaced 1 normalized line(s) with 1 line(s)
- **Before:** `["Applications are open through 2026-09-30."]`
- **After:** `["Applications are suspended pending an eligibility review."]`
- **Matched rules:** `policy-suspension`
- **Tags:** `policy, action-required`

### [HIGH] Synthetic release metadata — `json.modified`

- **Event ID:** `400ff7f66d64244463fcce59`
- **Source:** [https://example.invalid/releases/latest.json](https://example.invalid/releases/latest.json)
- **Independence group:** `synthetic-project`
- **Path:** `/compatibility/minimum_python`
- **Summary:** JSON value changed at /compatibility/minimum_python
- **Before:** `3.11`
- **After:** `3.12`
- **Matched rules:** `breaking-compatibility`
- **Tags:** `release, compatibility`

### [MEDIUM] Synthetic release metadata — `json.modified`

- **Event ID:** `5616454cdffd79eb68772d44`
- **Source:** [https://example.invalid/releases/latest.json](https://example.invalid/releases/latest.json)
- **Independence group:** `synthetic-project`
- **Path:** `/version`
- **Summary:** JSON value changed at /version
- **Before:** `1.4.0`
- **After:** `2.0.0`
- **Matched rules:** `none`
- **Tags:** `none`

### [MEDIUM] Synthetic research feed — `feed.item_added`

- **Event ID:** `d1c4666bfdf5b62f5c49ea18`
- **Source:** [https://example.invalid/research.xml](https://example.invalid/research.xml)
- **Independence group:** `synthetic-research-publisher`
- **Path:** `item:research-002`
- **Summary:** Feed item added: New synthetic replication note
- **Before:** `—`
- **After:** `{"id": "research-002", "link": "https://example.invalid/research/002", "published": "2026-08-30T01:00:00Z", "summary": "A new synthetic replication result.", "title": "New synthetic replication note"}`
- **Matched rules:** `new-research-item`
- **Tags:** `research, new-item`

### [LOW] Synthetic research feed — `feed.item_modified`

- **Event ID:** `b37861b7762dcb2971e17399`
- **Source:** [https://example.invalid/research.xml](https://example.invalid/research.xml)
- **Independence group:** `synthetic-research-publisher`
- **Path:** `item:research-001`
- **Summary:** Feed item changed: Baseline methods note
- **Before:** `{"id": "research-001", "link": "https://example.invalid/research/001", "published": "2026-08-20T00:00:00Z", "summary": "Initial synthetic methods note.", "title": "Baseline methods note"}`
- **After:** `{"id": "research-001", "link": "https://example.invalid/research/001", "published": "2026-08-30T00:00:00Z", "summary": "Revised synthetic methods note with a larger sample.", "title": "Baseline methods note"}`
- **Matched rules:** `none`
- **Tags:** `none`

### [LOW] Synthetic service status — `content.normalized_unchanged`

- **Event ID:** `f80ee928be6204b54928bc1c`
- **Source:** `urn:synthetic:service-status`
- **Independence group:** `synthetic-operator`
- **Path:** `service-status.txt`
- **Summary:** Raw bytes changed, but the configured normalizer produced identical monitored content
- **Before:** `2883a2fcb9dcd14e20efc812e96c78600e836107c8208314be294917171801de`
- **After:** `7cbef19ef4829bc50562028c156fd140bbb85ddef449a4cca1e71e45b34772f0`
- **Matched rules:** `none`
- **Tags:** `none`

## Limitations

- The monitor compares captured representations, not the full external source.
- A detected change does not prove legal effect, causality, truthfulness, or material impact.
- No detected change does not prove that the source or underlying reality was unchanged.
- Normalization rules can intentionally hide volatile fields and must be reviewed as part of the monitoring scope.
- The v0.1.0 core does not fetch the network; it processes explicit local captures so acquisition can be isolated and audited.
