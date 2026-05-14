# Tutorial: Serve and Replay

In this tutorial you'll boot the Harbor FastAPI app with `harbor serve`,
enqueue a run over HTTP, poll it to terminal state, and then replay it
deterministically with `harbor replay`. The replay produces a
counterfactual fork ID; with `--diff` you can render the parent vs.
forked `RunDiff` as JSON.

## What you'll build

```mermaid
flowchart LR
    client((curl)) -->|POST /v1/runs| api[harbor serve]
    api --> sched[Scheduler]
    sched --> ckpt[(SQLite Checkpointer)]
    client -->|GET /v1/runs/{id}| api
    cli[harbor replay] --> ckpt
```

Two CLIs talking to the same SQLite checkpointer DB. The scheduler
runs the graph in-process; checkpoints land row-by-row; the replay
CLI forks a counterfactual run from any persisted step.

## Prerequisites

- The graph from the [first graph](first-graph.md) tutorial
  (`graph.yaml`, `state.py`).
- `curl` or any HTTP client.
- A free port (default `8000`).

## Step 1 — Boot the API

```bash
uv run harbor serve \
  --profile oss-default \
  --host 127.0.0.1 \
  --port 8000 \
  --db ./.harbor/serve.sqlite \
  --audit-log ./.harbor/audit.jsonl
```

Pinning `--db` is critical. Without it `harbor serve` mints a
per-process temp DB and the replay CLI in step 5 will not see the
run. The lifespan factory:

1. Bootstraps the SQLite checkpointer (creates
   `runs_history` + `pending_runs` via migration 002).
2. Wires `RunHistory` over the same connection so `GET /v1/runs`
   returns live data.
3. Starts the `Scheduler` and the Nautilus broker (soft-fail if no
   `nautilus.yaml` is present).
4. Mounts the five POC routes plus the post-Phase-2 surfaces
   (`/cancel`, `/pause`, `/respond`, `/counterfactual`, `/artifacts`,
   `/v1/runs/{id}/stream` WebSocket).

Verify the app is up:

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq '.info.title'
# → "Harbor"
```

## Step 2 — Register the graph (POC)

The POC `harbor serve` boots with an empty in-memory graphs registry
(`app.state.deps["graphs"] = {}`); production wiring loads graphs
from the plugin manifest at lifespan start. For this tutorial we
cheat: enqueue a run and immediately drive it via the CLI's `harbor
run` against the same DB so the checkpoints are durable. Phase 2 task
2.30 swaps this for a Checkpointer-backed lookup.

In a second terminal:

```bash
uv run harbor run graph.yaml \
  --inputs message=hello \
  --checkpoint ./.harbor/serve.sqlite \
  --log-file ./.harbor/audit.jsonl
```

Capture the `run_id=…` from the last stdout line.

```bash
RUN_ID=$(uv run harbor run graph.yaml --inputs message=hello \
  --checkpoint ./.harbor/serve.sqlite --no-summary | tail -1 | awk '{print $1}' | cut -d= -f2)
echo "$RUN_ID"
```

## Step 3 — Poll over HTTP

```bash
curl -s "http://127.0.0.1:8000/v1/runs/$RUN_ID" | jq
```

Expected `RunSummary` shape:

```json
{
  "run_id": "run-…",
  "status": "done",
  "graph_hash": "sha256:…",
  "started_at": "…",
  "finished_at": "…"
}
```

The list endpoint is paginated:

```bash
curl -s "http://127.0.0.1:8000/v1/runs?limit=10" | jq '.items[].run_id'
```

## Step 4 — Try the enqueue surface

`POST /v1/runs` enqueues against the in-process Scheduler. In the POC
the Scheduler resolves the future quickly with a synthetic
`RunSummary` and returns `{run_id: "poc-<graph_id>", status: "pending"}`
— it does NOT execute your graph against the live DB yet (that wiring
is Phase 2 task 2.30). Useful for confirming the queueing path works
end-to-end:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"graph_id": "run:hello-harbor", "params": {"message": "hello"}}'
# → {"run_id": "poc-run:hello-harbor", "status": "pending"}
```

## Step 5 — Replay the real run

`harbor replay` forks a counterfactual run from a persisted parent at
a chosen `--from-step`. Without a `--mutation` JSON, the cf-run still
gets a fresh `cf-<uuid>` id and a derived `graph_hash` per design
§3.8.3.

```bash
uv run harbor replay "$RUN_ID" \
  --db ./.harbor/serve.sqlite \
  --from-step 0 \
  --diff
```

Expected stdout — the cf-run id followed by the parent vs cf
`RunDiff` rendered as canonical JSON via `harbor.ir.dumps`:

```
cf_run_id=cf-…
{
  "added_steps": [...],
  "removed_steps": [...],
  "state_deltas": {...},
  "fact_deltas": {...},
  "derived_hash": "sha256:..."
}
```

A no-op mutation produces an empty diff; the `derived_hash` still
captures the cf-side identity.

## Step 6 — Mutate state on replay

Save a `CounterfactualMutation` JSON file:

```bash
cat > mutation.json <<EOF
{
  "state_overrides": {"message": "mutated"},
  "facts_assert": [],
  "facts_retract": []
}
EOF
```

Then replay with the mutation overlay:

```bash
uv run harbor replay "$RUN_ID" \
  --db ./.harbor/serve.sqlite \
  --mutation mutation.json \
  --from-step 0 \
  --diff
```

The cf-run now has `state.message="mutated"` at step 0; the diff
shows the divergence. Pipe `cf_run_id` into `harbor inspect` to walk
the cf-side timeline:

```bash
CF_RUN_ID=$(uv run harbor replay "$RUN_ID" --db ./.harbor/serve.sqlite \
  --mutation mutation.json | head -1 | cut -d= -f2)

uv run harbor inspect "$CF_RUN_ID" --db ./.harbor/serve.sqlite
```

## Step 7 — Verify determinism

Replay the same run twice with no mutation. The cf-run ids differ
(fresh uuid each time) but the `derived_hash` is identical — this is
the bit-identity contract per FR-19 / FR-28 amendment 6 (no
`set`/`frozenset` state fields, no `race`/`any` parallel branches with
write side effects, compiled `state_schema` folded into the graph
hash).

```bash
uv run harbor replay "$RUN_ID" --db ./.harbor/serve.sqlite --diff | jq -r '.derived_hash'
uv run harbor replay "$RUN_ID" --db ./.harbor/serve.sqlite --diff | jq -r '.derived_hash'
# → identical hashes
```

## Cleaning up

The `Scheduler` is started inside `harbor serve`'s lifespan; Ctrl-C
on the serve process stops it cleanly (drain + close), then closes
the checkpointer. The SQLite WAL is single-writer, so you cannot run
`harbor serve` and `harbor run --checkpoint` against the same DB
simultaneously — pick one writer at a time.

## What to read next

- [Serve → API](../serve/api.md) — full route table, error envelopes,
  rate-limit headers.
- [Serve → Scheduler](../serve/scheduler.md) — cron loop, per-graph
  concurrency, idempotency keys.
- [Engine → Replay](../engine/replay.md) — cassette mechanics and
  determinism guards.
- [Engine → Counterfactual](../engine/counterfactual.md) — full
  `CounterfactualMutation` schema (`state_overrides`, `facts_assert`,
  `facts_retract`, `rule_pack_version`, `node_output_overrides`).
