# Evidence Model

Each snapshot records:

- source ID and title;
- public locator or URN;
- source independence group;
- explicit observation timestamp;
- input path and format;
- capture status;
- raw and normalized SHA-256 values;
- normalization version;
- normalized representation or parse error.

Each event records:

- stable event ID;
- baseline and current normalized hashes;
- source and independence group;
- change type and structural path;
- bounded before and after excerpts;
- severity, matched rules, and tags.

The independence group does not prove independence. It records the evaluator's source-family classification so multiple pages from one publisher are not mistaken for multiple independent origins.

An integrity manifest detects later modification of generated files. It is not a signature, trusted timestamp, or immutable audit log.
