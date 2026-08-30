"""Shared constants."""

SCHEMA_VERSION = 1
NORMALIZER_VERSION = "1.0"

SOURCE_FORMATS = ("text", "html", "json", "feed")
SOURCE_PRIORITIES = ("low", "medium", "high", "critical")
SEVERITIES = ("info", "low", "medium", "high", "critical")
SEVERITY_RANK = {name: index for index, name in enumerate(SEVERITIES)}

CHANGE_TYPES = (
    "source.first_seen",
    "source.missing",
    "source.parse_error",
    "source.oversize",
    "content.normalized_unchanged",
    "text.added",
    "text.removed",
    "text.modified",
    "json.added",
    "json.removed",
    "json.modified",
    "feed.item_added",
    "feed.item_removed",
    "feed.item_modified",
)
