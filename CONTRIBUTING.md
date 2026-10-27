# Contributing

Every resource added to Catkins must follow the cat theme. Use a different pack for unrelated themes.

## Add a restyle

1. Identify the exact vanilla file being overridden.
2. Save each target version's vanilla file under `tools/vanilla-reference/<edition>/<version>/` before editing a model or geometry override.
3. Add or update edition-neutral source art in `tools/pixelmaps/`.
4. Add destination paths to `OUTPUTS` in `tools/render_pixelmaps.py`.
5. Put Java texture overrides under `java/assets/minecraft/textures/` and model overrides under `java/assets/minecraft/models/`.
6. Once Bedrock support ships, also put Bedrock texture overrides under `bedrock/textures/` and entity geometry overrides under `bedrock/models/entity/`.
7. Run `tools/build.py`, which also runs the renderer.
8. Test every supported view affected by the override.

The carved pumpkin and jack o'lantern Java block models override these vanilla paths:

```text
java/assets/minecraft/models/block/carved_pumpkin.json
java/assets/minecraft/models/block/jack_o_lantern.json
```

The face textures override these paths:

```text
java/assets/minecraft/textures/block/carved_pumpkin.png
java/assets/minecraft/textures/block/jack_o_lantern.png
```

Bedrock outputs will be added to `OUTPUTS` when Bedrock support ships. Snow golem geometry belongs under `bedrock/models/entity/`. Confirm the current vanilla path before adding the override.

## Pixelmap format

Pixelmaps are ASCII text. A palette block comes first, followed by exactly 16 rows of 16 characters:

```text
palette:
A = #E3901DFF
B = #2D0003FF
pixels:
AAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAA
```

Each palette key is one non-whitespace character. Each color is eight hexadecimal RGBA digits. Every pixel character must exist in the palette.

PNGs are build outputs. Do not hand-edit them. Pull requests with hand-edited PNGs will be sent back for the pixelmap.

## Java overlays

Use overlays only when a target version needs a different file. Add a row to `FORMAT_TABLE` in `tools/build.py` with the `version`, `format`, `legacy`, and `overlay` fields filled in. Put overlay files under the matching directory inside `java/`, using the same path they replace. The build writes `supported_formats` for pre-1.21.9 clients and `min_format`/`max_format` for current clients, so each selects the correct range.

## Commands

```text
.venv/bin/python tools/render_pixelmaps.py
.venv/bin/python tools/build.py --version 1.0.0
```

The renderer updates edition assets and writes 256x256 previews to `tools/preview/`. The build runs the renderer, writes `java/pack.mcmeta`, and creates the release archive in `dist/`.

## Pull requests

Include:

- Preview PNGs.
- In-game screenshots from at least one 1.21.x client and one 26.x client.
- Bedrock screenshots once Bedrock support ships.
- The path and version of every vanilla file being overridden.
- A short test report covering the affected block, item, held, worn, and entity views.

## Releases

Release tags use the form `v1.0.0`, or `v1.0.0-beta.1` for a pre-release. Pushing one builds the Java archive, publishes the same file to Modrinth and CurseForge, and creates a GitHub release.

Configure these GitHub repository variables before pushing the first release tag:

- `MODRINTH_PROJECT_ID`
- `CURSEFORGE_PROJECT_ID`

Configure these GitHub repository secrets:

- `MODRINTH_TOKEN`
- `CURSEFORGE_TOKEN`

Both platform projects must already exist and accept Java resource-pack uploads. Never commit access tokens.
