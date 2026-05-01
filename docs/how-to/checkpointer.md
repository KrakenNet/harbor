# How to Persist with a Checkpointer

Attach a store-backed checkpointer so a Harbor graph can pause, resume, and replay.

## Outline

1. Pick a store plugin (e.g. `harbor-store-sqlite`) and add it to `[dependency-groups]`.
2. Declare the checkpointer in `graph.yaml` under `state.checkpointer`.
3. Verify with `harbor replay <run-id>`.

> TODO: write up once the store interface and `replay` CLI ship.
