# Tutorial: Your First Graph

Walk through composing a Harbor graph from a tool, a skill, and an in-memory store.

## What you'll build

A two-node graph: a `fetch` tool feeds a `summarize` skill; the result lands in the default store.

## Steps

1. Scaffold a project with `uv init` and add `harbor` as a dependency.
2. Declare the graph in `graph.yaml`.
3. Run `harbor run graph.yaml --trace`.

> TODO: write the full lesson once the runtime, default store, and CLI ship.
