from __future__ import annotations

import unittest

from evidence_change_monitor.normalization import normalize_bytes


class NormalizationTests(unittest.TestCase):
    def test_text_collapses_whitespace(self) -> None:
        left, left_hash = normalize_bytes(
            b"System status: operational\n",
            source_format="text",
            encoding="utf-8",
            options={"collapse_whitespace": True, "case_sensitive": True},
        )
        right, right_hash = normalize_bytes(
            b"System   status:   operational\r\n",
            source_format="text",
            encoding="utf-8",
            options={"collapse_whitespace": True, "case_sensitive": True},
        )
        self.assertEqual(left, right)
        self.assertEqual(left_hash, right_hash)

    def test_case_insensitive_mode(self) -> None:
        left, _ = normalize_bytes(
            b"Alpha",
            source_format="text",
            encoding="utf-8",
            options={"case_sensitive": False},
        )
        right, _ = normalize_bytes(
            b"ALPHA",
            source_format="text",
            encoding="utf-8",
            options={"case_sensitive": False},
        )
        self.assertEqual(left, right)

    def test_html_skips_script_and_style(self) -> None:
        value, _ = normalize_bytes(
            b"<style>hidden</style><main>Hello<script>alert(1)</script> world</main>",
            source_format="html",
            encoding="utf-8",
            options={},
        )
        self.assertEqual(value, ["Hello world"])

    def test_html_ignore_regex_removes_volatile_timestamp(self) -> None:
        value, _ = normalize_bytes(
            b"<p>Notice</p><p>Last checked: 2026-08-30T08:00:00Z</p>",
            source_format="html",
            encoding="utf-8",
            options={"ignore_regexes": [r"Last checked: [0-9:T+Z-]+"]},
        )
        self.assertEqual(value, ["Notice"])

    def test_json_keys_are_canonical(self) -> None:
        left, left_hash = normalize_bytes(
            b'{"b":2,"a":1}',
            source_format="json",
            encoding="utf-8",
            options={},
        )
        right, right_hash = normalize_bytes(
            b'{"a":1,"b":2}',
            source_format="json",
            encoding="utf-8",
            options={},
        )
        self.assertEqual(left, {"a": 1, "b": 2})
        self.assertEqual(left_hash, right_hash)

    def test_json_pointer_is_ignored(self) -> None:
        value, _ = normalize_bytes(
            b'{"generated_at":"now","payload":{"value":2}}',
            source_format="json",
            encoding="utf-8",
            options={"ignore_json_pointers": ["/generated_at"]},
        )
        self.assertEqual(value, {"payload": {"value": 2}})

    def test_nested_json_pointer_is_ignored(self) -> None:
        value, _ = normalize_bytes(
            b'{"meta":{"volatile":"x","stable":"y"}}',
            source_format="json",
            encoding="utf-8",
            options={"ignore_json_pointers": ["/meta/volatile"]},
        )
        self.assertEqual(value, {"meta": {"stable": "y"}})

    def test_atom_entries_are_sorted_by_id(self) -> None:
        xml = b"""<feed xmlns='http://www.w3.org/2005/Atom'>
        <entry><id>b</id><title>B</title></entry>
        <entry><id>a</id><title>A</title></entry></feed>"""
        value, _ = normalize_bytes(xml, source_format="feed", encoding="utf-8", options={})
        self.assertEqual([item["id"] for item in value], ["a", "b"])

    def test_malformed_feed_raises(self) -> None:
        with self.assertRaises(Exception):
            normalize_bytes(b"<feed>", source_format="feed", encoding="utf-8", options={})


if __name__ == "__main__":
    unittest.main()
