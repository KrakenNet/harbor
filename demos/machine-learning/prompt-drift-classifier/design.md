# ML Model · `prompt-drift-classifier`

A model that watches an agent's *effective* behavior over time and
detects when it has silently drifted away from its system prompt,
without the prompt itself having changed. The agent didn't get
reconfigured; its *outputs* started reconfiguring themselves.

It is not a prompt-text classifier. It compares observed behavior —
which tools fired, which claims surfaced, which response styles
appeared — against the embedded intent of the system prompt.

## Purpose

Catch the slow, non-exception failure mode where an agent's outputs
drift class-by-class from "what its prompt says it's for" to
something different. Tools regressions, RAG-context changes,
upstream-model swaps, and prompt-injection residue all manifest this
way. Static prompt review never catches it; the prompt didn't change.

## Task type

Embedding-distance + classification hybrid. The system prompt is
embedded; recent agent outputs are embedded as a behavioral
distribution; KL/MMD between the two is the drift signal, with a
secondary classifier head that tags drift type (`tool_misuse`,
`tone_shift`, `policy_violation`, `topic_creep`).

## Inputs

| Field                | Type     | Notes                                |
|----------------------|----------|--------------------------------------|
| `agent_id`           | uuid     | which agent                          |
| `system_prompt`      | string   | current system prompt text           |
| `recent_outputs[]`   | list[Output] | last N final answers + tool selections |
| `window`             | duration | time window for "recent"             |

## Outputs

| Field              | Type         | Notes                              |
|--------------------|--------------|------------------------------------|
| `drift_score`      | float [0..1] | 0 = on-policy, 1 = wandered off    |
| `drift_type`       | enum         | tool_misuse / tone / policy / topic |
| `exemplar_outputs[]` | trace_id[] | which traces show the drift most   |
| `nearest_aligned[]` | trace_id[]  | older traces that *did* match prompt |

## Training-data shape

Drawn entirely from Railyard's own tables. The platform produces:

- `agents.agents` — system prompt history per agent
- `tracing.spans` — every agent invocation, its inputs and outputs
- `agents.tool_calls` — which tools were chosen per turn
- `governor.decisions` — which policies fired (a strong drift signal)

Training pairs are constructed as `(prompt_embedding, behavior_window)`
with positive examples from the agent's first stable month and
negative examples mined from periods where governors started firing
unexpectedly. The model is per-agent; cold-start uses a global
shrinkage prior.

## Eval metric

1. **AUROC** against operator-flagged drift incidents (the SRE marks
   "yes that was real drift" / "no that was intentional").
2. **Lead time** — how many hours before a human noticed did the model
   first cross threshold.

The second is the metric customers pay for; the first keeps training
honest.

## Serving target

gomlx (`internal/gomlx/`) — distributional comparisons and embedding
math sit on the hot path; the head is small but the streaming
windowing logic benefits from compiled graphs.

## Inference call sites

1. **Continuous**: every agent has a rolling drift score updated
   per-turn. UI surfaces it on the agent detail page.
2. **Governor integration**: the `drift-detector` governor can read
   the score and gate execution when drift exceeds threshold.
3. **Composes with `governor-rule-miner`**: when drift is detected,
   the rule miner is asked to propose a CLIPS rule that would have
   caught the specific drift pattern.

## Why it's a good demo

1. **It can only exist on a platform that owns the prompt history
   and the trace stream simultaneously.** Most observability tools
   see outputs but not configuration; most config tools see configs
   but not outputs. Railyard sees both, joined.

2. **It captures a failure mode that has no exception.** Drift is
   invisible to logs, metrics, and traces individually. It only
   becomes visible when you compare *intent* against *behavior* —
   which is what a platform like this is uniquely positioned to do.

3. **It composes with the creative trio.** `trace-shape-anomaly`
   catches *structural* surprise; this catches *semantic* surprise;
   `governor-rule-miner` turns both into reusable rules. Together
   they form a closed loop where the platform notices, explains,
   and codifies its own surprises.

## Sample interaction

Agent `support-agent` has been running for 90 days. Drift score over
the last week: 0.81 (typical: 0.05).

→ drift_type: `tool_misuse`
→ exemplar_outputs: [trace_a1, trace_b3, trace_c7]
  - `vector-search` calls dropped from 8/turn to 0.5/turn
  - `web-fetch` calls rose from 0/turn to 6/turn
→ nearest_aligned: [trace_x9, trace_y2] from week 1
→ likely cause: a recent KB ingest job failed silently, retrieval
  returns nothing, agent has learned to fall back to `web-fetch`.
  Prompt never changed; behavior did.

→ Surfaces in the agents UI; `governor-rule-miner` proposes a
"`web-fetch` count > N triggers `pre-mortem-required`" rule.
