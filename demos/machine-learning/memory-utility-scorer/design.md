# ML Model · `memory-utility-scorer`

Predicts which agent memories are worth keeping past their natural
decay window — based on how often they get retrieved, how often
retrieving them improved the outcome, and how irreplaceable they are
relative to the rest of the memory store.

It is not a recency-decay function. It learns from Railyard's own
retrieval logs which memories actually pulled their weight in
producing good outcomes, and lets useful memories outlive the
default decay schedule.

## Purpose

Solve the central problem of agent memory: most memories are useless,
a few are crucial, and recency is a poor proxy for which is which.
A 6-month-old memory of "user prefers terse responses" is worth more
than yesterday's "user said hi." This model decides what survives.

## Task type

Regression on memory-level utility, with a classification head for
the keep/decay/promote decision. Inputs are memory features +
retrieval/outcome history; output is a calibrated utility score.

## Inputs

| Field             | Type         | Notes                              |
|-------------------|--------------|------------------------------------|
| `memory_id`       | uuid         | which memory                       |
| `memory_text`     | string       | content                            |
| `created_at`      | timestamp    | original write                     |
| `retrieval_history[]` | list[Hit] | every time the memory was surfaced |
| `outcome_history[]`   | list[Outcome] | what happened in those traces  |

## Outputs

| Field            | Type             | Notes                              |
|------------------|------------------|------------------------------------|
| `utility_score`  | float [0..1]     | calibrated                         |
| `decision`       | enum: decay / keep / promote | what to do                |
| `lift_estimate`  | float            | estimated outcome improvement attributable to this memory |
| `redundancy`     | float [0..1]     | how much overlap with other memories |
| `reason_summary` | string           | human-readable explanation         |

## Training-data shape

Drawn entirely from Railyard's tables:

- `memories.memory_items` — content + creation metadata
- `memories.retrieval_log` — every retrieval event with the trace it
  participated in
- `tracing.spans` — full execution + outcome of those traces
- `agents.executions` — outcome quality scores
- `compliance.review_outcomes` — human-judged answer quality

For each memory, training builds a feature vector from
`(retrieval_count, retrieval_recency_curve, outcome_lift_when_retrieved,
embedding_neighborhood_density)` and a label from a counterfactual
estimate: how much worse would matching traces have done if this
memory had been absent? (The platform can run that counterfactual
because it persists what was retrieved per trace.)

## Eval metric

1. **Counterfactual outcome lift** — for memories the model says to
   keep, do their absence-experiments confirm they were helpful?
2. **Storage savings** — fraction of memories pruned at fixed
   outcome quality.
3. **Calibration** — the score gates an irreversible delete; threshold
   calibration is a hard SLO.

## Serving target

gomlx (`internal/gomlx/`) — embedding-distance computations against
the rest of the memory store and per-memory feature aggregation
benefit from compiled graphs. Runs nightly per tenant, not on the
hot path.

## Inference call sites

1. **Nightly memory-decay sweep**: every memory past its default
   decay window is scored. `keep` extends the window, `decay`
   proceeds, `promote` migrates to long-term.
2. **Knowledge UI**: operators see per-memory utility scores in the
   memory browser, with the option to manually pin or prune.
3. **Composes with `decision-journal-kg`**: a memory's utility
   trajectory over time is itself a journaled artifact — "we
   thought this was useful, here's the data on whether it was."

## Why it's a good demo

1. **It can only exist where the platform owns memory write,
   memory read, and outcome attribution simultaneously.** Most
   memory systems track writes and reads but can't say "did
   retrieving this memory actually help the trace it appeared in?"
   Railyard can, because the trace owns the join.

2. **It demonstrates the platform learning what it should
   remember.** The classic agent-memory bug is hoarding (cheap
   storage, expensive context window) or amnesia (too aggressive
   decay). This model gives a defensible per-memory verdict.

3. **It composes with the memory trio.** `decision-journal-kg`
   stores the rationale for retention decisions; `half-life-kb`
   provides a complementary fact-decay mechanism for non-memory
   knowledge; this model decides per-memory survival. Together
   they give the platform a coherent "what to keep, why we kept
   it, when to let it go" story.

## Sample interaction

Memory `mem_42a1`: "user 9173 prefers responses under 100 words."
Created 8 months ago. Default decay would expire it next week.

→ utility_score: 0.91
→ decision: keep
→ lift_estimate: 0.18 — when retrieved, traces produced answers
  that the user accepted 18% more often than when it wasn't
→ redundancy: 0.04 — no other memory expresses this preference
→ reason_summary: "Retrieved 142 times in the last 60 days, present
  in 38 user-marked-helpful traces, no near-duplicate exists. Decay
  would lose a high-utility, irreplaceable preference."

Memory `mem_99cd`: "user 9173 said 'hi'." Created 3 days ago.

→ utility_score: 0.04
→ decision: decay
→ lift_estimate: ~0
→ redundancy: 0.99 — there are 41 near-duplicate hellos
→ reason_summary: "Never retrieved, no outcome lift, near-perfect
  overlap with 41 other memories. Safe to drop on schedule."

The memory store stays small without losing the memories that
mattered, and every retention decision is auditable.
