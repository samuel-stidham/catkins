#!/usr/bin/env python3
"""Build release archives from the Catkins source trees."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
JAVA_DIR = ROOT / "java"
DIST_DIR = ROOT / "dist"
DEFAULT_PACK_VERSION = "1.0.0"
VERSION_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]+){2}(?:[-+][0-9A-Za-z.-]+)?$")

# Official release changelogs:
# https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21
# https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-7
# https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-8
# https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-9
# https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11
# https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1
# https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2
# https://www.minecraft.net/en-us/article/minecraft-java-edition-26-3
# 1.21.8 was a graphics-only hotfix and retained 1.21.7's format 64.
# Exact 26.x formats are recorded in version.json inside each official client jar.
# Each overlay field is either None or (directory, minimum format, maximum format).
FORMAT_TABLE = (
    {"version": "1.21", "format": 34, "legacy": True, "overlay": None},
    {"version": "1.21.8", "format": 64, "legacy": True, "overlay": None},
    {"version": "1.21.9", "format": (69, 0), "legacy": False, "overlay": None},
    {"version": "1.21.11", "format": (75, 0), "legacy": False, "overlay": None},
    {"version": "26.1", "format": (84, 0), "legacy": False, "overlay": None},
    {"version": "26.2", "format": (88, 0), "legacy": False, "overlay": None},
    {"version": "26.3", "format": (97, 1), "legacy": False, "overlay": None},
    {"version": "future 26.x ceiling", "format": 999, "legacy": False, "overlay": None},
)

ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def pack_metadata() -> dict[str, Any]:
    legacy_formats = [row["format"] for row in FORMAT_TABLE if row["legacy"]]
    metadata: dict[str, Any] = {
        "pack": {
            "description": "Catkins: cat-inspired carved pumpkins",
            "pack_format": legacy_formats[0],
            "supported_formats": {
                "min_inclusive": legacy_formats[0],
                "max_inclusive": legacy_formats[-1],
            },
            "min_format": FORMAT_TABLE[0]["format"],
            "max_format": FORMAT_TABLE[-1]["format"],
        }
    }

    overlay_entries = []
    for row in FORMAT_TABLE:
        overlay = row["overlay"]
        if overlay is None:
            continue
        directory, minimum, maximum = overlay
        entry: dict[str, Any] = {"directory": directory}
        if row["legacy"]:
            entry["formats"] = {
                "min_inclusive": minimum,
                "max_inclusive": maximum,
            }
        else:
            entry["min_format"] = minimum
            entry["max_format"] = maximum
        overlay_entries.append(entry)

    if overlay_entries:
        metadata["overlays"] = {"entries": overlay_entries}
    return metadata


def write_pack_metadata() -> Path:
    destination = JAVA_DIR / "pack.mcmeta"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(pack_metadata(), indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    return destination


def zip_java_pack(version: str) -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    destination = DIST_DIR / f"catkins-java-{version}.zip"
    with ZipFile(destination, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(path for path in JAVA_DIR.rglob("*") if path.is_file()):
            relative = source.relative_to(JAVA_DIR)
            info = ZipInfo(relative.as_posix(), ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compresslevel=9)
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        default=DEFAULT_PACK_VERSION,
        help=f"release version used in archive names (default: {DEFAULT_PACK_VERSION})",
    )
    args = parser.parse_args()
    if not VERSION_PATTERN.fullmatch(args.version):
        parser.error("version must be a semantic version such as 1.0.0 or 1.0.0-beta.1")
    return args


def main() -> None:
    args = parse_args()
    subprocess.run([sys.executable, ROOT / "tools" / "render_pixelmaps.py"], check=True)
    write_pack_metadata()
    archive = zip_java_pack(args.version)
    print(f"Built {archive.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
