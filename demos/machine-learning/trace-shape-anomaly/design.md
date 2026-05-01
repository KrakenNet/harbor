# ML Model · `trace-shape-anomaly`

A model that learns the *shape* of a normal Railyard trace — which agents
call which tools in which order, with what fan-out, at what depth — and
flags traces whose shape is unusual.

It is not a sentiment model on log text. It treats span trees as
structured graphs and learns their distribution. Its training data is
something only Railyard has: every span tree the platform has ever run.

## Purpose

Catch silent failures and behavioral drift that *don't* throw exceptions.
An agent that has started looping. A tool whose error rate is unchanged
but whose call count just doubled. A governor that's silently no-op'd
because its facts stream went stale. None of these trip a traditional
alert; all of them produce an unusual trace shape.

## Task type

Unsupervised anomaly detection over labeled directed graphs. Variational
graph autoencoder; reconstruction error is the anomaly signal.

## Inputs

A trace tree, encoded as a node-labeled graph:

| Field            | Type                   | Notes |
|------------------|------------------------|-------|
| `nodes[]`        | list[SpanNode]         | each node = `{span_kind, agent_id, tool_id, model_id, latency_bucket, error_kind}` |
| `edges[]`        | list[(parent, child)]  | parent-child span relationships |
| `root_workflow`  | uuid                   | for per-workflow normalization |

## Outputs

| Field                     | Type            | Notes |
|---------------------------|-----------------|-------|
| `anomaly_score`           | float [0..1]    | higher = more unusual |
| `most_anomalous_subtree`  | span_id         | where the surprise concentrates |
| `nearest_normal_shape`    | trace_id        | which past trace this *almost* looked like |
| `divergence_features`     | list[Feature]   | which structural attributes differ |

## Training-data shape

Stored span trees from Railyard's tracing tables. **Per-tenant model:**
each tenant's "normal" is its own distribution. Cold-start: until a
tenant has 1k traces, fallback to global model with shrinkage.

Negative examples are not curated — the model is trained on everything,
since "normal" is whatever the system mostly does. Drift is captured by
retraining nightly.

## Eval metric

Two-tier:

1. **Reconstruction loss** — proxy, computed every batch
2. **Operator-labeled retro accuracy** — sample weekly anomalies, ask SRE if they were real, log AUROC against those labels

The second metric is the one that matters; the first is just for training
stability.

## Serving target

gomlx (`internal/gomlx/`) — graph operations are the hot path, custom
layers needed.

## Inference call sites

1. **Live**: every completed trace gets a score. Top-1% per tenant per day surfaces in the traces UI.
2. **Workflow integration**: `pre-mortem-first` workflow uses `nearest_normal_shape` to retrieve relevant priors.
3. **Governor integration**: a high anomaly score on a still-running trace can fire `loop-breaker` or `drift-detector`.

## Why it's a good demo

1. **It can only exist on a platform like Railyard.** A model that learns
   from span trees presupposes a system that produces span trees
   consistently. The demo is the platform proving its data is good
   enough to be the substrate for its own ML.

2. **It demonstrates the platform consuming its own output.** Most
   platforms ship telemetry to external observability tools. Here, the
   telemetry is training data for a first-class model that improves the
   platform. That self-consumption is rare and worth showing.

3. **It composes with two other creative entries** — `governor-rule-miner`
   (which learns from *governor decisions*) and `prompt-drift-classifier`
   (which learns from *prompt evolutions*). Together they form a "the
   platform learns about itself" trio. Each one alone is interesting; in
   concert they tell a story about a platform that gets less surprising
   over time.

## Sample interaction

Trace `xyz789` finishes. Score: 0.94.

→ most_anomalous_subtree: span_4 — agent `support-agent` called `vector-search` 47 times (typical: 3–5)
→ nearest_normal_shape: trace_7e2a (similar agent, similar input class, fanout 4)
→ divergence_features:
  - `tool_call_count(vector-search)`: observed=47, p99_normal=8
  - `depth`: observed=12, p99_normal=5
  - `elapsed_ms`: observed=58_400, p99_normal=4_200

→ Surfaced in traces UI; on-call sees a likely retrieval-loop bug in the agent.
