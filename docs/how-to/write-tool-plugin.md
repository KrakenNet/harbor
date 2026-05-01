# How to Write a Tool Plugin

Ship a Harbor tool as an installable Python distribution.

## Outline

1. Create a package and declare a `harbor.tools` entry point.
2. Implement the `harbor_plugin()` factory and the tool's `__call__`.
3. Expose a `PluginManifest` with `api_version` so Harbor can gate compatibility.
4. Add tests, then publish to PyPI or your private index.

> TODO: fill in once the tool ABI and `harbor_plugin` contract are frozen (Phase 1).
