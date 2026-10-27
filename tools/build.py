#!/usr/bin/env python3
"""Build one Catkins Java release archive per resource pack format."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
JAVA_DIR = ROOT / "java"
OVERRIDES_DIR = ROOT / "java-overrides"
DIST_DIR = ROOT / "dist"
DEFAULT_PACK_VERSION = "1.0.0"
VERSION_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){2}$")
DESCRIPTION = "Catkins: cat-inspired carved pumpkins"

# Resource pack format of every supported release, oldest first, from
# https://minecraft.wiki/w/Pack_format. Consecutive releases that share a
# format share one archive. The wiki writes formats from 1.21.9 on as
# major.minor; only the major is listed here because each archive pins
# min_format and max_format to the major, which covers every minor of it.
PACK_FORMATS = (
    ("1.21", 34),
    ("1.21.1", 34),
    ("1.21.2", 42),
    ("1.21.3", 42),
    ("1.21.4", 46),
    ("1.21.5", 55),
    ("1.21.6", 63),
    ("1.21.7", 64),
    ("1.21.8", 64),
    ("1.21.9", 69),
    ("1.21.10", 69),
    ("1.21.11", 75),
    ("26.1", 84),
    ("26.1.1", 84),
    ("26.1.2", 84),
    ("26.2", 88),
    ("26.3", 97),
)
# 1.21.9 replaced pack_format and supported_formats with min_format and max_format.
FIRST_MODERN_FORMAT = 69
# Ceiling for the development copy under java/, so snapshots load it without a warning.
DEV_MAX_FORMAT = 999

ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def targets(pack_formats: Sequence[tuple[str, int]] = PACK_FORMATS) -> list[dict[str, Any]]:
    """Group consecutive game versions that share a pack format, oldest first."""
    grouped: list[dict[str, Any]] = []
    for game_version, pack_format in pack_formats:
        if grouped and grouped[-1]["pack_format"] == pack_format:
            grouped[-1]["game_versions"].append(game_version)
            continue
        if grouped and grouped[-1]["pack_format"] > pack_format:
            raise ValueError(f"PACK_FORMATS must not decrease, but {game_version} does")
        grouped.append({"pack_format": pack_format, "game_versions": [game_version]})
    for target in grouped:
        versions = target["game_versions"]
        if len(versions) == 1:
            target["label"] = versions[0]
        else:
            target["label"] = f"{versions[0]}-{versions[-1]}"
    return grouped


def pack_metadata(pack_format: int) -> dict[str, Any]:
    """pack.mcmeta for one release archive, pinned to one format."""
    pack: dict[str, Any] = {"description": DESCRIPTION, "pack_format": pack_format}
    if pack_format >= FIRST_MODERN_FORMAT:
        pack["min_format"] = pack_format
        pack["max_format"] = pack_format
    return {"pack": pack}


def dev_pack_metadata() -> dict[str, Any]:
    """pack.mcmeta for the development copy under java/, spanning every supported format."""
    formats = [pack_format for _, pack_format in PACK_FORMATS]
    legacy_formats = [pack_format for pack_format in formats if pack_format < FIRST_MODERN_FORMAT]
    return {
        "pack": {
            "description": DESCRIPTION,
            "pack_format": legacy_formats[0],
            "supported_formats": {
                "min_inclusive": legacy_formats[0],
                "max_inclusive": legacy_formats[-1],
            },
            "min_format": formats[0],
            "max_format": DEV_MAX_FORMAT,
        }
    }


def encode_json(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def write_dev_pack_metadata() -> Path:
    destination = JAVA_DIR / "pack.mcmeta"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(encode_json(dev_pack_metadata()))
    return destination


def pack_files(pack_format: int) -> dict[str, Path]:
    """Map archive paths to source files.

    Files under java-overrides/<pack_format>/ replace the file at the same
    path under java/. pack.mcmeta is generated per archive, never copied.
    """
    files: dict[str, Path] = {}
    for directory in (JAVA_DIR, OVERRIDES_DIR / str(pack_format)):
        if not directory.is_dir():
            continue
        for source in directory.rglob("*"):
            if source.is_file():
                files[source.relative_to(directory).as_posix()] = source
    files.pop("pack.mcmeta", None)
    return files


def write_archive(destination: Path, files: dict[str, Path], metadata: dict[str, Any]) -> None:
    entries = {name: source.read_bytes() for name, source in files.items()}
    entries["pack.mcmeta"] = encode_json(metadata)
    with ZipFile(destination, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(entries):
            info = ZipInfo(name, ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, entries[name], compresslevel=9)


def platform_names(version: str, label: str) -> dict[str, str]:
    """Display name and version number of one archive on CurseForge and Modrinth."""
    return {
        "name": f"Catkins {version} for Minecraft {label}",
        "platform_version": f"{version}+mc{label}",
    }


def build(version: str) -> dict[str, Any]:
    """Write one archive per target plus dist/manifest.json describing them."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"version": version, "targets": []}
    for target in targets():
        pack_format = target["pack_format"]
        file_name = f"catkins-java-{version}-mc{target['label']}.zip"
        write_archive(DIST_DIR / file_name, pack_files(pack_format), pack_metadata(pack_format))
        manifest["targets"].append({**target, "file": file_name, **platform_names(version, target["label"])})
    (DIST_DIR / "manifest.json").write_bytes(encode_json(manifest))
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        default=DEFAULT_PACK_VERSION,
        help=f"release version used in archive names (default: {DEFAULT_PACK_VERSION})",
    )
    args = parser.parse_args()
    if not VERSION_PATTERN.fullmatch(args.version):
        parser.error("version must be three numbers such as 1.0.0")
    return args


def main() -> None:
    args = parse_args()
    subprocess.run([sys.executable, ROOT / "tools" / "render_pixelmaps.py"], check=True)
    write_dev_pack_metadata()
    manifest = build(args.version)
    for target in manifest["targets"]:
        print(f"Built dist/{target['file']} for {', '.join(target['game_versions'])}")
    print("Wrote dist/manifest.json")


if __name__ == "__main__":
    main()
