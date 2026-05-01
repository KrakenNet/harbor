# Tool · `time-travel-replayer`

Pick a past run. Pick one node in its trace tree. Swap something — the
model, the prompt, the tool implementation, an input value — and replay
from that node forward, leaving the upstream context exactly as it was.
See what *would have* happened.

This is the demo that, if you've ever debugged an agent, makes you
realize the platform you've been using has been hiding a power tool
from you. Most platforms only let you replay an entire run, which means
the cheapest re-run is the entire run.

## Purpose

Counterfactual debugging, prompt-iteration with realistic context,
model-comparison experiments, and "would the new governor have caught
this?" backtests. All of them collapse to "rerun this trace with one
node swapped."

## Inputs

| Field           | Type    | Required | Notes |
|-----------------|---------|----------|-------|
| `trace_id`      | uuid    | yes      | the run to replay from |
| `node_id`       | string  | yes      | span id to start divergence at |
| `swap`          | object  | yes      | what to substitute |
| `swap.kind`     | enum    | yes      | model / prompt / tool_impl / input / governor |
| `swap.value`    | any     | yes      | replacement payload |
| `replay_depth`  | int     | no, full | stop after N spans of replay |
| `seed`          | int     | no       | for sampling determinism |

## Outputs

| Field            | Type            | Notes |
|------------------|-----------------|-------|
| `new_trace_id`   | uuid            | the replay's own trace |
| `divergence_node`| string          | echo of `node_id` |
| `final_state`    | any             | terminal output of the replayed branch |
| `cost`           | CostSummary     | tokens, dollars, latency |
| `delta`          | Diff            | structured diff vs. original final state |

## Implementation kind

DSPy tool. The trace-walker and node-substitutor are Go-side, but the
*delta computation* (semantically diffing two final states that may be
free-text answers) uses a DSPy signature.

## Dependencies

- `internal/tracing/` — trace tree reader, span hydration with full
  inputs/outputs of every node
- `internal/agent/executor.go` — re-execute downstream from any span
  using its captured upstream context
- DSPy module registry — to swap a step's prompt/signature
- LLM-model registry — to swap the resolved model
- Sibling tool `provenance-tracer` — for surfacing where the new
  branch's final claims come from

## Side effects

Spawns a new run with full normal cost — model calls, tool calls, etc.
The original trace is untouched. Both traces become siblings under a
"counterfactual replay" parent span so reviewers see the comparison as
one artifact.

## Failure modes

- `node_id` not in trace → `error_kind="node_not_found"`
- Swap incompatible with the node (e.g. prompt swap on a tool node) →
  rejected pre-replay, `error_kind="swap_incompatible"`
- Downstream span depends on non-replayable side effects (a deleted
  external row, a notification already sent) → marked as `unreplayable`
  in the replay's gap notes; the replay continues and skips them
- Cost cap hit during replay → halted, partial trace returned

## Why it's a good demo

Three reasons:

1. **It only exists because every Railyard step captures full
   inputs/outputs as spans.** A platform that doesn't record the inputs
   to step 4 cannot replay step 4. This tool is the most direct
   demonstration of why the trace store is a first-class architectural
   choice and not an observability afterthought.
2. **It composes with the entire experimentation surface.** Pairs with
   `counterfactual-mutator` (mutate the input *to* the swap node),
   `confidence-bettor` (have the new branch bet on its answer for
   side-by-side calibration), `decision-journal-kg` (record the swap as
   an experiment), and the `counterfactual-replay` workflow (which is
   this tool driven on a schedule).
3. **It changes the cost of "what if?"** A team that can re-run last
   week's flaky decision with a different model in 30 seconds asks
   different questions than a team that has to reconstruct the
   conditions from logs. This tool is what makes that habit affordable.

## Sample interaction

> trace_id: 7fd1...
> node_id: span:agent.route_decision
> swap: { kind: "model", value: "gpt-5-thinking" }

→ new_trace_id: a91c...
→ divergence_node: span:agent.route_decision
→ final_state: "{ owner: 'security-eng', priority: 'P1' }"
→ delta: original chose `priority='P3'`; replay chose `P1`
→ cost: $0.42 (vs. original $0.07)

The replay just demonstrated that the bigger model would have escalated
this incident on day one. That row goes to `decision-journal-kg`, the
delta becomes a training signal for the `tool-choice-predictor` ML
primitive, and the replayed trace is now a permanent exhibit.
