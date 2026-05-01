# Plugin Model

Harbor uses a two-stage plugin loader built on `importlib.metadata` entry points and `pluggy` hooks. Distributions register under one of four groups: `harbor.tools`, `harbor.skills`, `harbor.stores`, or `harbor.packs`. Each distribution exposes a single `harbor_plugin()` callable plus a stdlib-only `PluginManifest` so Harbor can check `api_version` **before** importing the module.

## Why two stages

- **Discovery without import.** Entry points are enumerated, not loaded — startup stays cheap.
- **Compatibility gating.** Manifests are read from the dist-info; an incompatible plugin never imports.
- **Hook composition.** Once gated, `pluggy` registers the module and composes hooks deterministically.

> TODO: link to the hookspec catalog in `reference/plugin-manifest.md` once it lists the nine hooks declared by Harbor core.
