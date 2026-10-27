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

## Java pack formats

`PACK_FORMATS` in `tools/build.py` lists every supported Minecraft version with its resource pack format, taken from <https://minecraft.wiki/w/Pack_format>. The build groups consecutive versions that share a format and writes one release zip per group. Each zip gets its own `pack.mcmeta` pinned to that format. The copy under `java/` keeps a permissive `pack.mcmeta` that spans every format, for development only.

To support a new Minecraft version, add its row to `PACK_FORMATS`. A version with a new format produces a new zip. A version that keeps the previous format joins the previous zip.

When one format needs a different file, put the replacement under `java-overrides/<pack format>/` at the same path it replaces inside `java/`. The build copies it over the base file for that zip only.

## Commands

```text
.venv/bin/python -m unittest discover --start-directory tests
.venv/bin/python tools/render_pixelmaps.py
.venv/bin/python tools/build.py --version 1.0.0
```

The tests cover the pack format grouping, the generated `pack.mcmeta`, and the changelog extraction. Every release workflow runs them before building.

The renderer updates edition assets and writes 256x256 previews to `tools/preview/`. The build runs the renderer, writes `java/pack.mcmeta`, and creates one release archive per pack format in `dist/`, listed in `dist/manifest.json`.

## Pull requests

Include:

- Preview PNGs.
- In-game screenshots from at least one 1.21.x client and one 26.x client.
- Bedrock screenshots once Bedrock support ships.
- The path and version of every vanilla file being overridden.
- A short test report covering the affected block, item, held, worn, and entity views.

## Releases

Release tags use the form `v1.0.0`. There are no pre-releases; test locally across every supported Minecraft version before tagging. Before publishing, add a `## [<version>] - <date>` section to `CHANGELOG.md` and commit it. Every workflow extracts that section with `tools/changelog_section.py` and fails when it is missing, so a release never ships without notes. Then publish a release on GitHub with the tag, from the Releases page or with `gh release create`. Publishing the release triggers three workflows. Pushing a tag on its own triggers nothing. Each workflow builds the archives from the tag on its own, and the build is deterministic, so all three produce identical zips.

| Workflow | File | What it does |
| --- | --- | --- |
| GitHub release | `.github/workflows/release.yml` | Replaces the release notes with the `CHANGELOG.md` section, attaches every archive, and fails if any is missing afterwards. Run manually, it needs the release to exist already. |
| CurseForge | `.github/workflows/curseforge.yml` | Uploads each archive as its own CurseForge file through [mc-publish](https://github.com/Kira-NT/mc-publish), tagged with the Minecraft versions it supports. One job per archive. |
| Modrinth | `.github/workflows/modrinth.yml` | Uploads each archive as its own Modrinth version through mc-publish, numbered `<version>+mc<minecraft versions>`. Skipped until `MODRINTH_PROJECT_ID` is set. |

The CurseForge and Modrinth workflows are thin callers of `.github/workflows/publish.yml`, which holds the shared build and upload jobs. The build steps themselves live in `.github/actions/build-release/`.

CurseForge and Modrinth receive the same `CHANGELOG.md` section as their changelog, so the three places never drift. Notes typed into the GitHub release form are overwritten.

Configure these GitHub repository variables and secrets before the first release. The CurseForge pair is required. Set the Modrinth pair once the Modrinth project is approved, and later tags upload there automatically.

| Kind | Name |
| --- | --- |
| Variable | `CURSEFORGE_PROJECT_ID` |
| Secret | `CURSEFORGE_TOKEN` |
| Variable | `MODRINTH_PROJECT_ID` |
| Secret | `MODRINTH_TOKEN` |

To upload an existing release to a platform later, such as the releases that shipped before Modrinth approval, run that platform's workflow manually from the Actions tab with the tag. The optional `targets` input limits the run to the listed archive labels, such as `1.21.4 26.3`. Upload jobs are named by label, so a failed run shows which labels to retry.

Both platform projects must already exist and accept Java resource-pack uploads. Never commit access tokens.
