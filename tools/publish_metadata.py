#!/usr/bin/env python3
"""Write platform metadata for a Catkins Java release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


GAME_VERSIONS = (
    "1.21",
    "1.21.1",
    "1.21.2",
    "1.21.3",
    "1.21.4",
    "1.21.5",
    "1.21.6",
    "1.21.7",
    "1.21.8",
    "1.21.9",
    "1.21.10",
    "1.21.11",
    "26.1",
    "26.1.1",
    "26.1.2",
    "26.2",
    "26.3",
)


def modrinth_metadata(project_id: str, version: str, changelog: str) -> dict[str, Any]:
    return {
        "name": f"Catkins {version}",
        "version_number": version,
        "changelog": changelog,
        "dependencies": [],
        "game_versions": list(GAME_VERSIONS),
        "version_type": "release",
        "loaders": ["minecraft"],
        "featured": True,
        "status": "listed",
        "project_id": project_id,
        "file_parts": ["catkins"],
        "primary_file": "catkins",
        "environment": "client_only",
        "file_types": {"catkins": "optional-resource-pack"},
    }


def curseforge_metadata(version: str, changelog: str) -> dict[str, Any]:
    return {
        "changelog": changelog,
        "changelogType": "markdown",
        "displayName": f"Catkins {version}",
        "gameVersionNames": ["Client", *GAME_VERSIONS],
        "releaseType": "release",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("modrinth", "curseforge"))
    parser.add_argument("--version", required=True)
    parser.add_argument("--project-id")
    parser.add_argument("--changelog", type=Path, required=True)
    args = parser.parse_args()
    if args.platform == "modrinth" and not args.project_id:
        parser.error("--project-id is required for Modrinth metadata")
    return args


def main() -> None:
    args = parse_args()
    changelog = args.changelog.read_text(encoding="utf-8")
    if args.platform == "modrinth":
        metadata = modrinth_metadata(args.project_id, args.version, changelog)
    else:
        metadata = curseforge_metadata(args.version, changelog)
    json.dump(metadata, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
