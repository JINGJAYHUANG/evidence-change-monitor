"""Deterministic source normalization."""

from __future__ import annotations

import copy
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any

from .util import canonical_json_bytes, sha256_bytes

_SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "canvas"}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.casefold() in _SKIP_TAGS:
            self._skip_depth += 1
        elif self._skip_depth == 0 and tag.casefold() in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif self._skip_depth == 0 and tag.casefold() in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self.parts.append(data)


def _normalize_text(text: str, options: dict[str, Any]) -> list[str]:
    flags = 0 if options.get("case_sensitive", True) else re.IGNORECASE
    for pattern in options.get("ignore_regexes", []):
        text = re.sub(pattern, "", text, flags=flags)
    if not options.get("case_sensitive", True):
        text = text.casefold()
    lines: list[str] = []
    collapse = options.get("collapse_whitespace", True)
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = re.sub(r"\s+", " ", raw_line).strip() if collapse else raw_line.rstrip()
        if line:
            lines.append(line)
    return lines


def normalize_text_bytes(data: bytes, *, encoding: str, options: dict[str, Any]) -> list[str]:
    return _normalize_text(data.decode(encoding), options)


def normalize_html_bytes(data: bytes, *, encoding: str, options: dict[str, Any]) -> list[str]:
    parser = VisibleTextParser()
    parser.feed(data.decode(encoding))
    parser.close()
    return _normalize_text("".join(parser.parts), options)


def _decode_pointer(pointer: str) -> list[str]:
    if pointer == "":
        return []
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def _remove_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return None
    parts = _decode_pointer(pointer)
    current = value
    for part in parts[:-1]:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return value
    final = parts[-1]
    if isinstance(current, dict):
        current.pop(final, None)
    elif isinstance(current, list) and final.isdigit() and int(final) < len(current):
        current.pop(int(final))
    return value


def _canonicalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonicalize_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_canonicalize_json(item) for item in value]
    return value


def normalize_json_bytes(data: bytes, *, encoding: str, options: dict[str, Any]) -> Any:
    value = json.loads(data.decode(encoding))
    value = copy.deepcopy(value)
    for pointer in options.get("ignore_json_pointers", []):
        value = _remove_pointer(value, pointer)
    return _canonicalize_json(value)


def _text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in list(element):
        local = child.tag.rsplit("}", 1)[-1].casefold()
        if local in names:
            if local == "link":
                href = child.attrib.get("href")
                if href:
                    return href.strip()
            return "".join(child.itertext()).strip()
    return ""


def normalize_feed_bytes(data: bytes, *, encoding: str, options: dict[str, Any]) -> list[dict[str, str]]:
    del encoding
    root = ET.fromstring(data)
    items: list[dict[str, str]] = []
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1].casefold()
        if local not in {"item", "entry"}:
            continue
        title = _text(element, ("title",))
        link = _text(element, ("link",))
        published = _text(element, ("published", "updated", "pubdate"))
        summary = _text(element, ("summary", "description", "content"))
        identifier = _text(element, ("id", "guid")) or link or title
        normalized_summary = " ".join(summary.split())
        if not options.get("case_sensitive", True):
            title = title.casefold()
            normalized_summary = normalized_summary.casefold()
        items.append(
            {
                "id": identifier.strip(),
                "title": " ".join(title.split()),
                "link": link.strip(),
                "published": published.strip(),
                "summary": normalized_summary,
            }
        )
    items.sort(key=lambda item: (item["id"], item["title"], item["link"]))
    return items


def normalize_bytes(
    data: bytes,
    *,
    source_format: str,
    encoding: str,
    options: dict[str, Any],
) -> tuple[Any, str]:
    if source_format == "text":
        normalized = normalize_text_bytes(data, encoding=encoding, options=options)
    elif source_format == "html":
        normalized = normalize_html_bytes(data, encoding=encoding, options=options)
    elif source_format == "json":
        normalized = normalize_json_bytes(data, encoding=encoding, options=options)
    elif source_format == "feed":
        normalized = normalize_feed_bytes(data, encoding=encoding, options=options)
    else:
        raise ValueError(f"unsupported source format: {source_format}")
    return normalized, sha256_bytes(canonical_json_bytes(normalized))
