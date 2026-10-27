# catkins

Catkins is a cat-inspired Minecraft resource pack. Every added resource follows the cat theme. Unrelated themes belong in a different pack.

## Install

### Java Edition

Download `catkins-java-<version>.zip` and place it in the client's `resourcepacks` directory. Select Catkins in the Resource Packs screen. Do not extract the release zip.

For development, copy the `java/` directory into `resourcepacks/catkins` instead. Reload resources with `F3+T` after each change.

### Bedrock Edition

Bedrock support is not released yet. When it ships, open `catkins-bedrock-<version>.mcpack`, then activate Catkins in the world's Resource Packs settings.

## What changes

Catkins restyles the vanilla carved pumpkin and jack o'lantern. Recipes, item IDs, block behavior, and golem creation stay vanilla.

The Java pack adds symmetric cat ears to both block models and gives both blocks a happy carved cat face. The plain pumpkin is unchanged.

## Supported versions

| Edition | Status | Versions |
| --- | --- | --- |
| Java | Complete | 1.21 through 1.21.11 and 26.1 through 26.3 |
| Bedrock | Planned | Whichever Bedrock release is current when work starts |

One Java pack supports the full Java range. Overlays hold different files for the versions that need them.

## What differs on Bedrock

A Bedrock resource pack cannot replace vanilla block geometry. Placed carved pumpkins and jack o'lanterns get cat faces but no ears. The snow golem head can still get cat ears through its entity geometry, which resource packs may replace. Catkins will not use a behavior pack or custom block to bypass this limit.

## Build from source

Requires Python 3.10 or newer and Pillow.

```text
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build.py --version 1.0.0
```

The build runs `tools/render_pixelmaps.py`, which writes pack textures under `java/` and 256x256 previews under `tools/preview/`. The build then creates `dist/catkins-java-<version>.zip`. Generated PNGs are derived from the text pixelmaps in `tools/pixelmaps/`.

## License

Catkins is available under the MIT License.
