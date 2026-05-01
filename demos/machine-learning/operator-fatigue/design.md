# ML Model · `operator-fatigue`

A model that watches HITL reviewer behavior and detects quality
decline — when an operator approves too fast, agrees too consistently,
or loses calibration against their historical baseline.

It is not a productivity tracker. It catches the predictable failure
mode of human-in-the-loop systems: that humans rubber-stamp under
load, and the platform is the only thing that can notice.

## Purpose

Protect the integrity of the approval gates. The `hitl-trigger`,
`approval-policy`, and `escalation-ladder` governors all hand off to
human operators. Those operators have their own degradation curve. A
fatigued reviewer who approves everything is *worse* than no reviewer
— it adds latency without adding signal. This model catches that.

## Task type

Sequence model over per-decision feature streams. Output is a
per-operator fatigue score with diagnostic breakdown
(`speed_drift`, `agreement_drift`, `calibration_drift`).

## Inputs

| Field             | Type             | Notes                              |
|-------------------|------------------|------------------------------------|
| `operator_id`     | uuid             | which reviewer                     |
| `recent_decisions[]` | list[Decision] | last N HITL approvals/rejections  |
| `window`          | duration         | rolling window for "recent"        |

Each decision carries:
- time-to-decide (ms)
- verdict (approve/reject/request-changes)
- task difficulty estimate (from `question-difficulty-router`)
- prior-distribution agreement (was this verdict the popular one?)
- post-hoc outcome where known (did the approved action turn out OK?)

## Outputs

| Field                | Type           | Notes                              |
|----------------------|----------------|------------------------------------|
| `fatigue_score`      | float [0..1]   | 0 = sharp, 1 = degraded            |
| `drift_kinds[]`      | enum[]         | speed / agreement / calibration    |
| `recommended_action` | enum: continue / rotate / pause | suggested response  |
| `peer_baseline`      | dict           | how this operator compares to peers + their own past |

## Training-data shape

Entirely from Railyard's tables:

- `compliance.review_queue` — every HITL task and its assignment
- `compliance.review_outcomes` — verdict + timestamp + reviewer id
- `tracing.spans` — the underlying agent execution being reviewed
- `workflow.executions` — what happened *after* an approval (the
  outcome ground truth)

Training labels: a decision is "high-quality" if the post-hoc outcome
agreed with the verdict (approved actions that succeeded; rejected
actions that turned out to have been correctly stopped). The model
learns the per-operator feature signature of high-quality decision
streaks vs. fatigued ones.

## Eval metric

1. **AUROC** against the post-hoc decision-quality label.
2. **Lead time** before a manager-flagged "this reviewer is burnt
   out" event — the model should fire hours-to-days before the
   human pattern is obvious.
3. **Per-operator calibration** — the model has to be calibrated
   *per person*, not at the population level. A reviewer with a
   genuinely fast baseline shouldn't read as fatigued.

## Serving target

gomlx (`internal/gomlx/`) — sequence model over per-operator
streams; calibration is per-operator and benefits from a graph that
includes the personalization layer.

## Inference call sites

1. **Per-decision**: every HITL verdict updates the operator's
   rolling score.
2. **Routing integration**: `approval-policy` uses the score to
   re-route high-stakes approvals away from fatigued operators.
3. **Workforce UI**: managers see a fatigue panel for their team,
   with rotation suggestions.
4. **Composes with `question-difficulty-router`**: hard tasks get
   routed to operators with low fatigue scores; easy tasks to anyone.

## Why it's a good demo

1. **It can only exist on a platform that owns both the queue and
   the outcome.** Standard HITL tools have the queue; standard
   audit tools have the outcomes; almost nothing joins them at the
   reviewer-id level. Railyard does, automatically, because the
   approval and the downstream execution share a request_id.

2. **It surfaces a failure mode operators rarely admit to themselves.**
   Reviewers don't notice their own fatigue — that's the definition
   of fatigue. The platform can.

3. **It composes with the human-loop trio.**
   `question-difficulty-router` decides who to route to;
   `governor-rule-miner` learns which patterns reviewers repeatedly
   approve so they can be auto-approved; this model decides whether
   the reviewer is currently sharp enough to be the deciding voice.
   Together they form a self-tuning HITL system.

## Sample interaction

Operator `alice` reviews approvals. Last 4 hours:

→ fatigue_score: 0.78 (typical for alice: 0.15)
→ drift_kinds: [speed, agreement]
  - median time-to-decide: 8s (her baseline: 45s)
  - approval rate: 96% (baseline: 72%)
  - calibration: 4 of last 12 approvals had post-hoc bad outcomes
    (her usual is 1 in 30)
→ recommended_action: rotate

→ `approval-policy` re-routes the next high-stakes approval to bob.
→ Manager dashboard surfaces: "alice may want a break — quality
   metrics dropped sharply over the last 4 hours."

The model isn't accusing the operator; it's giving the operator and
their manager a defensible signal that the review queue is degrading
in real time, before a bad approval ships.
