"""Tests for tools/changelog_section.py."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import changelog_section  # noqa: E402

CHANGELOG = """# Changelog

## [Unreleased]

- Not yet

## [1.1.0] - 2027-01-01

### Added

- Second thing

## [1.0.0] - 2026-10-27

First release.

## [0.9.0] - 2026-10-01

[Unreleased]: https://example.test/compare/v1.1.0...HEAD
[1.1.0]: https://example.test/tag/v1.1.0
[1.0.0]: https://example.test/tag/v1.0.0
"""


class SectionTest(unittest.TestCase):
    def test_section_ends_at_next_heading(self) -> None:
        self.assertEqual(changelog_section.section(CHANGELOG, "1.1.0"), "### Added\n\n- Second thing\n")

    def test_section_ends_at_link_reference(self) -> None:
        self.assertEqual(changelog_section.section(CHANGELOG, "1.0.0"), "First release.\n")

    def test_missing_section_is_none(self) -> None:
        self.assertIsNone(changelog_section.section(CHANGELOG, "2.0.0"))

    def test_empty_section_is_empty_string(self) -> None:
        self.assertEqual(changelog_section.section(CHANGELOG, "0.9.0"), "")

    def test_version_must_match_exactly(self) -> None:
        self.assertIsNone(changelog_section.section(CHANGELOG, "1.0"))

    def test_headings_are_listed_in_order(self) -> None:
        self.assertEqual(changelog_section.version_headings(CHANGELOG), ["Unreleased", "1.1.0", "1.0.0", "0.9.0"])


if __name__ == "__main__":
    unittest.main()
