# Source Registry

The registry is fail-closed: unknown fields, unsafe paths, duplicate IDs, invalid regexes, unsupported formats, or non-HTTPS locators are rejected.

Source fields include:

- `source_id`: stable kebab-case identifier;
- `locator`: an HTTPS URL without embedded credentials, or a URN;
- `input_path`: relative path inside the explicit capture directory;
- `format`: `text`, `html`, `json`, or `feed`;
- `priority`: `low`, `medium`, `high`, or `critical`;
- `independence_group`: declared source family;
- `max_bytes`: per-source capture limit;
- `normalization`: ignored regexes, ignored JSON pointers, case handling, and whitespace handling.

Normalization is part of the evidence scope. Every ignored field can create a false negative if chosen too broadly.
