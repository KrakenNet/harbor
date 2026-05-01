# ML Model · `tool-choice-predictor`

Predicts which tool the agent *should have* called, from the agent's
own input, system prompt, and available tool catalog — and compares
it against what the agent actually did. The post-hoc tool-choice oracle.

It is not a re-implementation of the agent's tool router. It learns
from successful past traces what the *empirically right* tool was for
problems that look like the current one, regardless of what the LLM
chose.

## Purpose

Two uses, depending on whether you're looking forward or back:

1. **Live nudge** — a hint surfaced to the agent at decision time
   ("90% of past similar tasks used `sql-query`, you're about to use
   `web-fetch`").
2. **Retro debugging** — for a failed trace, surface the tool choice
   that historical evidence says would have worked, so operators can
   fix the agent's prompt or tool descriptions.

## Task type

Multi-class classification over the tool catalog, conditioned on
input + agent context. Trained from outcome-labeled traces — only
*successful* outcomes count as positive labels.

## Inputs

| Field             | Type         | Notes                              |
|-------------------|--------------|------------------------------------|
| `task_text`       | string       | user query / current sub-goal      |
| `agent_id`        | uuid         | which agent                        |
| `available_tools` | string[]     | tool ids in this agent's allowlist |
| `prior_steps`     | list[Step]   | tools already called in this trace |

## Outputs

| Field              | Type             | Notes                              |
|--------------------|------------------|------------------------------------|
| `recommended_tool` | string           | top-1 prediction                   |
| `scores`           | map[string]float | per-tool                           |
| `confidence`       | float [0..1]     | top score                          |
| `historical_support` | int            | how many similar past traces backed this |

## Training-data shape

Pulled entirely from Railyard's tables:

- `tracing.spans` — every tool call, with surrounding context
- `agents.executions` — final outcomes (success/failure, user-rated)
- `agents.tool_calls` — tool selection events
- `compliance.review_outcomes` — human verdicts where present
- `memories.*` — what context was in scope at the moment of choice

Each row: `(task_text, agent_id, available_tools, prior_steps,
chosen_tool, outcome_quality)`. Only rows with above-threshold outcome
quality count as positives. Per-tenant model with fallback to a
cross-tenant shrinkage prior.

## Eval metric

1. **Top-1 / top-3 accuracy** on held-out successful traces
   (does the model recover the tool that worked?).
2. **Lift on outcome quality** when an agent follows the recommendation
   vs. its native choice (measured via canary deployment).

The second is what matters; the first is a sanity check.

## Serving target

ONNX runtime (`internal/onnxrt/`) — small encoder + classification
head. Latency on the agent hot path needs to be < 30ms.

## Inference call sites

1. **Pre-call hint**: agents can opt into receiving the recommendation
   as a structured hint in their context window.
2. **Trace UI**: every tool-call span gets a "would have recommended:
   X" annotation when the live recommendation differs.
3. **Composes with `decision-journal-kg`**: when the agent ignores
   the recommendation, that's recorded as an explicit "we considered
   X but chose Y" rationale row.

## Why it's a good demo

1. **It can only be trained where tool calls and outcomes are
   joined.** Most LLM platforms log tool calls; few log outcome
   quality back to the call. Railyard does — and the join is the
   training signal.

2. **It turns historical traces into a feedback loop on agent
   configuration.** When the recommender systematically disagrees
   with a particular agent, the operator gets a "your tool
   descriptions might be misleading" signal — actionable
   prompt-engineering feedback, evidence-based.

3. **It composes with `governor-rule-miner` and `prompt-drift-
   classifier`.** Drift detector says "agent is choosing differently
   than it used to"; this model says "and here's what it should
   choose"; rule miner converts that into a CLIPS rule. The three
   form a "diagnose, recommend, codify" pipeline.

## Sample interaction

Agent `support-agent` is asked: "show me the last 5 invoices for
account 4192." It is about to call `vector-search`.

Tool-choice predictor:
→ recommended_tool: `sql-query`
→ scores: `sql-query` 0.91, `vector-search` 0.04, `web-fetch` 0.02
→ historical_support: 1,847 similar past tasks
→ confidence: 0.91

The agent receives this as context. It overrides to `sql-query`,
returns the right answer in one call instead of the 7-step retrieval
loop it would have entered.

The trace logs both the original choice signal and the override; the
journal records: "predictor recommended sql-query (n=1847), agent
adopted, outcome: success."
