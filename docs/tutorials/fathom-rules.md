# Tutorial: Add a Fathom Rule Pack

Layer deterministic, replayable governance onto your graph by attaching a Fathom rule pack.

## What you'll build

A rule pack that gates a tool call on a policy fact, emitting a deterministic decision into the trace.

## Steps

1. Create `packs/redact.fathom` with a rule and a fact.
2. Register the pack as a `harbor.packs` entry point.
3. Reference it from `graph.yaml` and re-run with `--trace`.

> TODO: complete after the Fathom integration lands and a working pack template exists.
