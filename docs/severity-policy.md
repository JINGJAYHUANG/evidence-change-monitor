# Severity Policy

Source priority establishes the base severity:

| Priority | Base severity |
|---|---|
| low | info |
| medium | low |
| high | medium |
| critical | high |

Capture failures have a minimum `high` severity because they create monitoring blindness.

Rules may promote severity based on:

- source IDs;
- change types;
- path regular expressions;
- bounded event text regular expressions;
- tags.

Rules never demote severity. A severity result is an operational triage label, not an objective statement of real-world materiality.
