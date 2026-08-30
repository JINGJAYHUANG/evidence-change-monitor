# Limitations

- HTML normalization extracts visible text but is not a browser-rendered DOM or CSS selector engine.
- JSON list changes are reported as list-level modifications rather than a minimum edit script.
- RSS and Atom identifiers depend on `id`, `guid`, link, or title quality.
- A feed item disappearing may reflect feed truncation, not deletion or retraction.
- Regular-expression normalization can hide meaningful changes.
- File locks do not coordinate independent hosts over all network filesystems.
- Integrity manifests detect mismatches but do not authenticate the author.
- No network acquisition, notification adapter, semantic embedding, OCR, browser rendering, or database backend is included in v0.1.0.
