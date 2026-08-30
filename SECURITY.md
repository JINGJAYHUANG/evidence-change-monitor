# Security Policy

Report security concerns through a private GitHub security advisory when available.

The v0.1.0 core intentionally does not fetch the network or execute monitored content. It treats input files, registries, feed XML, HTML, JSON, and state directories as untrusted.

Security boundaries include:

- no symbolic-link following for monitored files;
- relative-path validation;
- per-source byte limits;
- no target-code execution;
- HTML output escaping;
- spreadsheet-formula neutralization;
- atomic state pointers and exclusive locks;
- integrity manifests for generated artifacts.

Integrity manifests are tamper-evident checks, not signatures or immutable storage.
