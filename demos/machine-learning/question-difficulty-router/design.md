# ML Model · `question-difficulty-router`

Predicts the difficulty of an inbound question and routes it
accordingly: easy → small/cheap model, hard → big/expensive model,
genuinely-hard → human. Trained on the platform's own outcome
history at every model tier.

It is not a token-length heuristic. It learns from Railyard traces
which problem types each tier of model actually solves well, and uses
that to make a calibrated cost/quality decision per request.

## Purpose

Cut LLM cost without quality regression. The naive policy ("always
use the big model") is expensive; the naive cheap policy ("always
small") regresses on hard cases. This model picks per request, with
a calibrated escalation path.

## Task type

Multi-class classification over `(model_tier, route)` choices, with
a regression head for expected quality at each tier. The output is
a tier recommendation plus a confidence interval that drives the
fallback ladder.

## Inputs

| Field             | Type         | Notes                              |
|-------------------|--------------|------------------------------------|
| `query`           | string       | the user question                  |
| `agent_id`        | uuid         | which agent will handle it         |
| `available_tiers` | string[]     | configured model tiers             |
| `cost_envelope`   | float        | per-request budget cap             |
| `context_meta`    | dict         | retrieval-set size, language, etc. |

## Outputs

| Field             | Type             | Notes                              |
|-------------------|------------------|------------------------------------|
| `recommended_tier`| string           | small / medium / large / human     |
| `quality_pred`    | map[tier]float   | predicted answer quality per tier  |
| `cost_pred`       | map[tier]float   | predicted $$ per tier              |
| `confidence`      | float [0..1]     | top-tier prediction confidence     |
| `fallback_tier`   | string           | escalate-to if first tier fails    |

## Training-data shape

Drawn from Railyard's own tables:

- `agents.executions` — every request, model tier used, outcome
- `tracing.spans` — token counts and intermediate quality signals
- `compliance.review_outcomes` — human-judged answer quality
- `platform.cost_ledger` — actual cost per request
- `memories.*` — query similarity to past queries

For each historical request, training records exist at *every tier*
that has been tried (via the `escalation-ladder` governor's natural
ABA pattern) — so the model learns from real per-tier outcomes, not
just imputations. Per-agent models with cross-agent shrinkage.

## Eval metric

1. **Realized cost savings** — total spend at the model's policy vs.
   "always large" baseline.
2. **Quality regression** — answer quality at the model's policy vs.
   "always large" baseline. Must be ≤ 2% degradation for the policy
   to be acceptable.
3. **Escalation rate** — fraction of times the fallback tier had to
   fire (a high rate means the predictor is over-routing to small).

The product (cost saved × quality preserved) is the headline.

## Serving target

ONNX runtime (`internal/onnxrt/`) — small encoder + classification
head. Latency budget: 20ms p99 (it sits before every LLM call).

## Inference call sites

1. **Pre-call routing**: every agent invocation passes the query
   through this model first. The chosen tier becomes the actual
   model selection.
2. **Governor integration**: `escalation-ladder` reads the
   `fallback_tier` to know what to escalate to on retry.
3. **Composes with `operator-fatigue`**: when the recommended tier
   is `human`, this model also names *which* humans are sharp
   enough right now to handle the difficulty class.

## Why it's a good demo

1. **It only works because the platform has tried multiple tiers
   on similar questions and recorded outcomes.** Cold-start LLM
   routers have to guess; this one has hundreds of thousands of
   per-tier outcome rows, naturally accumulated by every workflow
   that uses `escalation-ladder`.

2. **It demonstrates Railyard learning to spend less on itself.**
   Cost optimization is normally an external concern (FinOps tools,
   bill analysis); here it's a first-class platform behavior driven
   by the platform's own data.

3. **It composes with the cost trio.** `cost-spike-forecaster`
   predicts incoming spend; this model controls per-request spend
   at the source; `governor-rule-miner` codifies the policies that
   emerge. Together they give the platform a "predict, control,
   codify" loop on cost.

## Sample interaction

User asks: "what's the capital of France?"

→ recommended_tier: `small`
→ quality_pred: small=0.97, medium=0.97, large=0.98, human=0.99
→ cost_pred: small=$0.0003, medium=$0.003, large=$0.04
→ confidence: 0.94
→ fallback_tier: medium

Routes to small. Saves ~13× cost vs. always-large policy with
indistinguishable quality.

User asks: "given these 12 contradictory contract clauses, which
governs the indemnification cap?"

→ recommended_tier: `large`
→ quality_pred: small=0.41, medium=0.62, large=0.86, human=0.94
→ cost_pred: small=$0.001, medium=$0.01, large=$0.12, human=$8.00
→ confidence: 0.71 — borderline; might need human escalation
→ fallback_tier: human

Routes to large with a pre-armed human fallback. If `large`'s
self-confidence (per `hallucination-scorer`) comes back low, the
trace auto-escalates to a human reviewer rather than retrying.
