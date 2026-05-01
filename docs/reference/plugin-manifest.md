# Plugin Manifest and Hookspec Catalog

Every Harbor plugin distribution declares a `PluginManifest` and registers under exactly one of `harbor.tools`, `harbor.skills`, `harbor.stores`, or `harbor.packs`. This page is the canonical hookspec catalog (AC-16.5) — the nine hooks Harbor core declares and that plugins may implement.

## Manifest fields

| Field         | Type    | Required | Description                                                              |
|---------------|---------|----------|--------------------------------------------------------------------------|
| `api_version` | str     | yes      | SemVer string Harbor checks before importing the plugin module.          |
| `name`        | str     | yes      | Human-readable plugin name.                                              |
| `kind`        | enum    | yes      | One of `tool`, `skill`, `store`, `pack`.                                 |
| `provides`    | list    | no       | Capabilities the plugin advertises (used by graph resolution).           |
| `requires`    | list    | no       | Other plugin capabilities this plugin depends on.                        |

## Hookspec catalog

The nine hooks declared by Harbor core (full signatures land with task 1.35):

1. `harbor_register_tools(registry)` — declare tool factories.
2. `harbor_register_skills(registry)` — declare skill factories.
3. `harbor_register_stores(registry)` — declare store/checkpointer factories.
4. `harbor_register_packs(registry)` — declare Bosun packs.
5. `harbor_compile_ir(ir, ctx)` — IR-time rewrite/validation hook.
6. `harbor_before_node(node, state)` — pre-execution hook for tracing/policy.
7. `harbor_after_node(node, state, result)` — post-execution hook.
8. `harbor_provide_facts(ctx)` — contribute facts to the Fathom session.
9. `harbor_emit_trace(event)` — sink for trace events (e.g. OTLP exporters).

> TODO: replace this catalog with the auto-generated hookspec dump once 1.35 declares the canonical signatures.
