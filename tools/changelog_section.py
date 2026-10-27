#!/usr/bin/env python3
"""Print one version's section of CHANGELOG.md for use as release notes."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHANGELOG = ROOT / "CHANGELOG.md"
HEADING_PATTERN = re.compile(r"^## \[(?P<version>[^\]]+)\]")
LINK_REFERENCE_PATTERN = re.compile(r"^\[[^\]]+\]:\s*\S")


def version_headings(changelog: str) -> list[str]:
    return [
        match.group("version")
        for line in changelog.splitlines()
        if (match := HEADING_PATTERN.match(line))
    ]


def section(changelog: str, version: str) -> str | None:
    """Return the text under the `## [version]` heading.

    Returns None when the heading is absent and "" when the section is empty.
    The section ends at the next `## ` heading or at the first link reference
    definition such as `[1.0.0]: https://...`.
    """
    lines = changelog.splitlines()
    for index, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)
        if match and match.group("version") == version:
            start = index + 1
            break
    else:
        return None
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## ") or LINK_REFERENCE_PATTERN.match(line):
            break
        body.append(line)
    text = "\n".join(body).strip()
    return text + "\n" if text else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="version whose section to print, such as 1.0.0")
    parser.add_argument("--changelog", type=Path, default=DEFAULT_CHANGELOG)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    changelog = args.changelog.read_text(encoding="utf-8")
    text = section(changelog, args.version)
    if text is None:
        available = ", ".join(version_headings(changelog)) or "none"
        sys.exit(
            f"{args.changelog.name} has no section for {args.version}. "
            f"Add a '## [{args.version}] - YYYY-MM-DD' section with the release notes. "
            f"Sections present: {available}"
        )
    if not text:
        sys.exit(
            f"The {args.version} section of {args.changelog.name} is empty. "
            "Add the release notes under its heading."
        )
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
