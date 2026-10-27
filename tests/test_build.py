"""Tests for the pure parts of tools/build.py."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402


class TargetsTest(unittest.TestCase):
    def test_consecutive_versions_sharing_a_format_share_one_target(self) -> None:
        result = build.targets((("1.21", 34), ("1.21.1", 34), ("1.21.2", 42)))
        self.assertEqual(
            [(t["pack_format"], t["game_versions"]) for t in result],
            [(34, ["1.21", "1.21.1"]), (42, ["1.21.2"])],
        )

    def test_label_is_single_version_or_first_to_last(self) -> None:
        result = build.targets((("26.1", 84), ("26.1.1", 84), ("26.1.2", 84), ("26.2", 88)))
        self.assertEqual([t["label"] for t in result], ["26.1-26.1.2", "26.2"])

    def test_decreasing_format_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build.targets((("1.21.4", 46), ("1.21.5", 42)))

    def test_real_table_has_unique_labels_and_increasing_formats(self) -> None:
        result = build.targets()
        labels = [t["label"] for t in result]
        formats = [t["pack_format"] for t in result]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(formats, sorted(set(formats)))
        self.assertEqual(sum(len(t["game_versions"]) for t in result), len(build.PACK_FORMATS))


class VersionPatternTest(unittest.TestCase):
    def test_accepts_three_numbers_without_leading_zeros(self) -> None:
        for version in ("1.0.0", "0.1.0", "10.20.30"):
            self.assertIsNotNone(build.VERSION_PATTERN.fullmatch(version), version)

    def test_rejects_other_shapes(self) -> None:
        for version in ("01.2.3", "1.0", "v1.0.0", "1.0.0-beta.1", "1.0.0.0", ""):
            self.assertIsNone(build.VERSION_PATTERN.fullmatch(version), version)


class BuildTest(unittest.TestCase):
    def test_build_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first"
            second = Path(temp) / "second"
            with mock.patch.object(build, "DIST_DIR", first):
                build.build("1.0.0")
            with mock.patch.object(build, "DIST_DIR", second):
                build.build("1.0.0")
            names = sorted(path.name for path in first.iterdir())
            self.assertEqual(names, sorted(path.name for path in second.iterdir()))
            self.assertEqual(len(names), len(build.targets()) + 1)
            for name in names:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)

    def test_manifest_carries_platform_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(build, "DIST_DIR", Path(temp)):
                manifest = build.build("1.2.3")
            written = json.loads((Path(temp) / "manifest.json").read_text(encoding="ascii"))
        self.assertEqual(manifest, written)
        by_label = {target["label"]: target for target in manifest["targets"]}
        self.assertEqual(by_label["1.21.7-1.21.8"]["name"], "Catkins 1.2.3 for Minecraft 1.21.7-1.21.8")
        self.assertEqual(by_label["1.21.7-1.21.8"]["platform_version"], "1.2.3+mc1.21.7-1.21.8")
        self.assertEqual(by_label["1.21.7-1.21.8"]["file"], "catkins-java-1.2.3-mc1.21.7-1.21.8.zip")

    def test_platform_names(self) -> None:
        self.assertEqual(
            build.platform_names("1.0.0", "26.3"),
            {"name": "Catkins 1.0.0 for Minecraft 26.3", "platform_version": "1.0.0+mc26.3"},
        )


class PackMetadataTest(unittest.TestCase):
    def test_legacy_format_pins_pack_format_only(self) -> None:
        pack = build.pack_metadata(64)["pack"]
        self.assertEqual(pack["pack_format"], 64)
        self.assertNotIn("min_format", pack)
        self.assertNotIn("max_format", pack)
        self.assertNotIn("supported_formats", pack)

    def test_modern_format_pins_min_and_max_to_the_major(self) -> None:
        pack = build.pack_metadata(69)["pack"]
        self.assertEqual((pack["pack_format"], pack["min_format"], pack["max_format"]), (69, 69, 69))

    def test_first_modern_format_boundary(self) -> None:
        self.assertNotIn("min_format", build.pack_metadata(build.FIRST_MODERN_FORMAT - 1)["pack"])
        self.assertIn("min_format", build.pack_metadata(build.FIRST_MODERN_FORMAT)["pack"])

    def test_dev_metadata_matches_committed_pack_mcmeta(self) -> None:
        committed = json.loads((ROOT / "java" / "pack.mcmeta").read_text(encoding="ascii"))
        self.assertEqual(committed, build.dev_pack_metadata())


class PackFilesTest(unittest.TestCase):
    def test_pack_mcmeta_is_never_copied_from_java(self) -> None:
        files = build.pack_files(34)
        self.assertNotIn("pack.mcmeta", files)
        self.assertIn("assets/minecraft/models/block/carved_pumpkin.json", files)

    def test_override_directory_applies_to_its_format_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            java = Path(temp) / "java"
            overrides = Path(temp) / "java-overrides"
            (java / "assets").mkdir(parents=True)
            (java / "assets" / "base.json").write_text("base")
            (java / "assets" / "shared.json").write_text("base")
            (java / "pack.mcmeta").write_text("{}")
            (overrides / "69" / "assets").mkdir(parents=True)
            (overrides / "69" / "assets" / "shared.json").write_text("override")
            (overrides / "69" / "assets" / "extra.json").write_text("extra")
            (overrides / "69" / "pack.mcmeta").write_text("{}")
            with mock.patch.object(build, "JAVA_DIR", java), mock.patch.object(build, "OVERRIDES_DIR", overrides):
                modern = build.pack_files(69)
                legacy = build.pack_files(34)
            self.assertEqual(modern["assets/shared.json"], overrides / "69" / "assets" / "shared.json")
            self.assertEqual(modern["assets/base.json"], java / "assets" / "base.json")
            self.assertEqual(modern["assets/extra.json"], overrides / "69" / "assets" / "extra.json")
            self.assertNotIn("pack.mcmeta", modern)
            self.assertEqual(legacy["assets/shared.json"], java / "assets" / "shared.json")
            self.assertNotIn("assets/extra.json", legacy)


if __name__ == "__main__":
    unittest.main()
