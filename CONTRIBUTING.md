# Contributing

Changes should preserve deterministic output and explicit evidence boundaries.

Before opening a pull request:

```bash
PYTHONPATH=src python tools/release_check.py
```

A change to normalization, event identity, scoring, source validation, or state semantics must include:

1. a regression test;
2. a documented migration or compatibility note;
3. an example showing the old and new behavior;
4. no real private target, credential, personal data, or unverifiable monitoring claim.

Do not add automatic network fetching without a separate threat model covering redirects, DNS rebinding, SSRF, credentials, size limits, content types, and acquisition provenance.
