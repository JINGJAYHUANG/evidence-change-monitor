from __future__ import annotations

import unittest

from evidence_change_monitor.config import validate_registry
from evidence_change_monitor.runner import validate_as_of

from helpers import cloned_registry


class RegistryValidationTests(unittest.TestCase):
    def test_example_registry_is_strictly_valid(self) -> None:
        self.assertTrue(validate_registry(cloned_registry(), strict=True).ok)

    def test_unknown_root_field_is_rejected(self) -> None:
        data = cloned_registry()
        data["surprise"] = True
        result = validate_registry(data)
        self.assertFalse(result.ok)
        self.assertIn("unknown_field", {item.code for item in result.issues})

    def test_duplicate_source_id_is_rejected(self) -> None:
        data = cloned_registry()
        data["sources"][1]["source_id"] = data["sources"][0]["source_id"]
        self.assertFalse(validate_registry(data).ok)

    def test_duplicate_input_path_is_rejected(self) -> None:
        data = cloned_registry()
        data["sources"][1]["input_path"] = data["sources"][0]["input_path"]
        self.assertFalse(validate_registry(data).ok)

    def test_path_traversal_is_rejected(self) -> None:
        data = cloned_registry()
        data["sources"][0]["input_path"] = "../secret.txt"
        self.assertFalse(validate_registry(data).ok)

    def test_http_locator_is_rejected(self) -> None:
        data = cloned_registry()
        data["sources"][0]["locator"] = "http://example.invalid/plain"
        self.assertFalse(validate_registry(data).ok)

    def test_url_credentials_are_rejected(self) -> None:
        data = cloned_registry()
        data["sources"][0]["locator"] = "https://user:pass@example.invalid/item"
        self.assertFalse(validate_registry(data).ok)

    def test_invalid_regex_is_rejected(self) -> None:
        data = cloned_registry()
        data["sources"][0]["normalization"]["ignore_regexes"] = ["("]
        self.assertFalse(validate_registry(data).ok)

    def test_unknown_rule_source_is_rejected(self) -> None:
        data = cloned_registry()
        data["severity_rules"][0]["source_ids"] = ["not-registered"]
        self.assertFalse(validate_registry(data).ok)

    def test_boolean_max_bytes_is_rejected(self) -> None:
        data = cloned_registry()
        data["default_max_bytes"] = True
        self.assertFalse(validate_registry(data).ok)

    def test_as_of_requires_timezone(self) -> None:
        with self.assertRaises(ValueError):
            validate_as_of("2026-08-30T08:00:00")

    def test_as_of_accepts_zulu(self) -> None:
        self.assertEqual(validate_as_of("2026-08-30T08:00:00Z"), "2026-08-30T08:00:00Z")


if __name__ == "__main__":
    unittest.main()
