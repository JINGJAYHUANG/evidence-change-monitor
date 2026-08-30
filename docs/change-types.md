# Change Types

| Type | Meaning |
|---|---|
| `source.first_seen` | No usable baseline exists |
| `source.missing` | Expected input file was absent |
| `source.parse_error` | Input could not be read or parsed |
| `source.oversize` | Input exceeded the configured byte limit |
| `content.normalized_unchanged` | Raw bytes changed but monitored normalized content did not |
| `text.added` | Normalized lines were added |
| `text.removed` | Normalized lines were removed |
| `text.modified` | A normalized text block was replaced |
| `json.added` | A JSON Pointer path was added |
| `json.removed` | A JSON Pointer path was removed |
| `json.modified` | A JSON Pointer value or list changed |
| `feed.item_added` | A feed item identifier appeared |
| `feed.item_removed` | A feed item identifier disappeared |
| `feed.item_modified` | An existing feed item changed |

Feed item removal can reflect retention-window behavior rather than source retraction. It requires interpretation.
