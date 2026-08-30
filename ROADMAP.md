# Roadmap

## 0.1.x

- add Windows and macOS state-lock integration jobs;
- add richer XML namespace and malformed-feed fixtures;
- add report-level source-group aggregation;
- add optional signed release provenance.

## 0.2.0

- add a separate HTTPS acquisition adapter with exact-host allowlists;
- defend against redirects, DNS rebinding, private-address resolution, SSRF, and oversized responses;
- record response headers, status, redirect chain, TLS endpoint, and content type;
- add conditional requests with explicit `ETag` and `Last-Modified` provenance;
- add notification adapters that remain disabled until explicitly configured.

No roadmap item authorizes private-account monitoring, hidden credentials, or autonomous external actions.
