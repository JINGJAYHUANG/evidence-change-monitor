# Threat Model

## Protected assets

- integrity of baselines and reports;
- confidentiality of private targets and credentials;
- distinction between capture failure and no change;
- provenance of monitored representations;
- operator control over state promotion.

## Main threats

1. path traversal or symbolic-link escape from an input path;
2. oversized or malformed input exhausting resources;
3. HTML or feed text injecting active content into reports;
4. spreadsheet formula injection through CSV;
5. over-broad normalization suppressing material evidence;
6. missing sources being mistaken for unchanged sources;
7. state races or partial writes corrupting the baseline;
8. a severity label being misrepresented as a legal or factual verdict;
9. future network acquisition introducing SSRF, cookies, redirects, or private-address access;
10. one publisher's pages being counted as independent corroboration.

## v0.1.0 controls

- safe relative paths and no symbolic-link following;
- per-source byte limits;
- standard-library parsing without target-code execution;
- HTML escaping and CSV formula neutralization;
- explicit failure events;
- atomic files, versioned snapshots, and exclusive state locks;
- source-family fields and bounded claims;
- no network fetcher in the core.
