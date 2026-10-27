#!/usr/bin/env python3
"""Render Catkins pixelmaps into edition assets and previews."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

try:
    from PIL import Image
except ImportError as error:
    raise SystemExit("Pillow is required. Run pip install -r requirements.txt first.") from error


ROOT = Path(__file__).resolve().parents[1]
PIXELMAP_DIR = ROOT / "tools" / "pixelmaps"
PREVIEW_DIR = ROOT / "tools" / "preview"
PIXELMAP_SIZE = 16
PREVIEW_SCALE = 16


@dataclass(frozen=True)
class Output:
    path: str
    scale: int = 1


OUTPUTS = {
    "carved_pumpkin.pixelmap": (
        Output("java/assets/minecraft/textures/block/carved_pumpkin.png"),
        Output("java/pack.png", scale=8),
    ),
    "jack_o_lantern.pixelmap": (
        Output("java/assets/minecraft/textures/block/jack_o_lantern.png"),
    ),
}

PALETTE_LINE = re.compile(r"^(\S) = #([0-9A-Fa-f]{8})$")


def parse_pixelmap(path: Path) -> tuple[dict[str, tuple[int, int, int, int]], list[str]]:
    lines = path.read_text(encoding="ascii").splitlines()
    if not lines or lines[0] != "palette:":
        raise ValueError(f"{path}: first line must be 'palette:'")

    palette: dict[str, tuple[int, int, int, int]] = {}
    index = 1
    while index < len(lines) and lines[index] != "pixels:":
        match = PALETTE_LINE.fullmatch(lines[index])
        if not match:
            raise ValueError(f"{path}:{index + 1}: invalid palette entry")
        symbol, rgba = match.groups()
        if symbol in palette:
            raise ValueError(f"{path}:{index + 1}: duplicate palette key {symbol!r}")
        palette[symbol] = tuple(
            int(rgba[offset : offset + 2], 16) for offset in range(0, 8, 2)
        )
        index += 1

    if index == len(lines):
        raise ValueError(f"{path}: missing 'pixels:' line")

    pixels = lines[index + 1 :]
    if len(pixels) != PIXELMAP_SIZE:
        raise ValueError(f"{path}: expected {PIXELMAP_SIZE} pixel rows")
    for row_number, row in enumerate(pixels, start=index + 2):
        if len(row) != PIXELMAP_SIZE:
            raise ValueError(
                f"{path}:{row_number}: expected {PIXELMAP_SIZE} characters"
            )
        unknown = set(row) - palette.keys()
        if unknown:
            raise ValueError(
                f"{path}:{row_number}: unknown palette keys {sorted(unknown)!r}"
            )

    return palette, pixels


def render_image(
    palette: dict[str, tuple[int, int, int, int]], pixels: list[str]
) -> Image.Image:
    image = Image.new("RGBA", (PIXELMAP_SIZE, PIXELMAP_SIZE))
    image.putdata([palette[symbol] for row in pixels for symbol in row])
    return image


def save_scaled(image: Image.Image, path: Path, scale: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = image
    if scale != 1:
        output = image.resize(
            (image.width * scale, image.height * scale), Image.Resampling.NEAREST
        )
    output.save(path, format="PNG", optimize=False)


def render_all() -> list[Path]:
    written: list[Path] = []
    for pixelmap_name, outputs in OUTPUTS.items():
        source = PIXELMAP_DIR / pixelmap_name
        palette, pixels = parse_pixelmap(source)
        image = render_image(palette, pixels)

        for output in outputs:
            destination = ROOT / output.path
            save_scaled(image, destination, output.scale)
            written.append(destination)

        preview = PREVIEW_DIR / f"{source.stem}.png"
        save_scaled(image, preview, PREVIEW_SCALE)
        written.append(preview)

    return written


def main() -> None:
    written = render_all()
    print(f"Rendered {len(OUTPUTS)} pixelmaps to {len(written)} files.")


if __name__ == "__main__":
    main()
