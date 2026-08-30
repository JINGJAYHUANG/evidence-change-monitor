# Repository Operating Rules

- Treat monitored inputs and configuration as untrusted.
- Preserve deterministic output when an explicit `as_of` timestamp is supplied.
- Do not add network access, code execution, credentials, or private targets silently.
- Do not convert file presence, HTTP success, or one source into a truth or materiality claim.
- Keep missing, failed, ignored, unchanged, first-seen, and changed states distinct.
- Add regression tests for every change to normalization, event identity, severity, state, or report semantics.
- Run `PYTHONPATH=src python tools/release_check.py` before release.
