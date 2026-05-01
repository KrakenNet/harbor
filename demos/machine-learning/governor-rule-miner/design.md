# ML Model · `governor-rule-miner`

A model that mines Railyard's own governor-decision history and
proposes new CLIPS rules — concretely synthesized rule text — that
would have caught past escalations earlier or generalized them
across agents.

It is not a black-box "gate everything" classifier. The output is
literally a CLIPS `defrule` block, complete with conditions and
`(emit-output ...)` action, ready for an operator to review and
deploy into the governor runtime.

## Purpose

Turn the long tail of human-flagged escalations and post-hoc bad
outcomes into reusable, transparent policy. Today an operator
notices a pattern, manually writes a CLIPS rule, and deploys it.
This model does the noticing and the drafting; the human keeps the
deploy.

## Task type

Two-stage. (1) Pattern mining over the trace + decision graph
(frequent-subgraph mining + outcome correlation). (2) Sequence-to-
structured-output generation that emits valid CLIPS rule text from
the mined patterns.

## Inputs

| Field             | Type         | Notes                              |
|-------------------|--------------|------------------------------------|
| `tenant_id`       | uuid         | per-tenant rule set                |
| `time_window`     | duration     | how far back to mine               |
| `outcome_filter`  | enum         | "bad outcomes only" / all          |
| `min_support`     | int          | minimum trace count per pattern    |
| `existing_rules`  | string[]     | current CLIPS rules, to avoid duplicates |

## Outputs

| Field            | Type           | Notes                              |
|------------------|----------------|------------------------------------|
| `proposals[]`    | list[RuleProposal] | each = rule + evidence + impact estimate |

Each proposal carries:
- `clips_text` — runnable `defrule` with `(emit-output ...)` action
- `pattern_summary` — human-readable description
- `support_traces[]` — examples that match the antecedent
- `historical_impact` — how many past bad outcomes the rule would
  have caught
- `false_positive_estimate` — how many *good* outcomes it would
  have blocked
- `existing_rule_overlap` — flagged if it duplicates a current rule

## Training-data shape

Drawn entirely from Railyard's tables:

- `governor.decisions` — every fact stream entry, every rule firing
- `governor.rules` — the existing rule corpus (avoid duplicate proposals)
- `tracing.spans` — full execution context around each decision
- `agents.executions` — outcomes (success/failure/bad-outcome label)
- `compliance.review_outcomes` — human verdicts that fixed escalations

The model is trained on `(antecedent_pattern → outcome)` pairs,
where antecedents are subgraphs over span features (agent_id,
tool_id, prior_step, latency_bucket, retrieval_count, ...) and
outcomes are the trace's eventual quality label.

The CLIPS-generation head is fine-tuned on the platform's *own*
existing rules — the corpus of human-written CLIPS rules and the
patterns that motivated them — so the proposals are syntactically
and stylistically consistent with what operators write.

## Eval metric

1. **Operator acceptance rate** — what fraction of proposed rules
   does a human reviewer deploy without editing?
2. **Edit distance to deployed form** — for accepted rules, how much
   did the operator change before shipping?
3. **Realized impact** — for deployed rules, did the post-deploy
   bad-outcome rate actually drop?

The third matters most; the first two are leading indicators.

## Serving target

gomlx (`internal/gomlx/`) for the subgraph-mining pipeline (graph
ops + correlation matrices) and the CLIPS-text generation head
(small encoder-decoder). Latency is not a concern — this runs
nightly per tenant.

## Inference call sites

1. **Nightly batch**: per-tenant mining run, results queued to the
   governors UI as "proposed rules."
2. **Reactive**: triggered by `prompt-drift-classifier` or
   `trace-shape-anomaly` firing — "we just saw a new failure mode,
   propose a rule for it."
3. **Composes with `decision-journal-kg`**: every accepted/rejected
   proposal is logged to the journal with rationale, so future
   miner runs learn from operator preferences.

## Why it's a good demo

1. **It can only exist where the policy language and the trace
   stream are both first-class.** CLIPS rules are interpretable
   text; trace spans are structured graphs. Mining the second to
   write the first requires both substrates to be inspectable —
   which is exactly the Railyard pitch.

2. **It closes the platform's self-improvement loop.** The platform
   produces decisions, the platform's own ML watches those
   decisions, the platform proposes new policies, an operator
   approves, the platform enforces them. Every step happens on the
   same substrate.

3. **It composes with the creative trio.** `trace-shape-anomaly`,
   `prompt-drift-classifier`, and `cost-spike-forecaster` *detect*
   surprises; this model is the *response* surface — surprises get
   converted into reusable policy. The platform gets less surprising
   over time, by construction.

## Sample interaction

Tenant `acme`, nightly mining run. 3 proposals returned.

**Proposal 1:**
```
(defrule retrieval-loop-guard
  (agent (id ?a))
  (tool-call-count (agent ?a) (tool "vector-search") (count ?n&:(> ?n 30)))
  =>
  (emit-output (action "halt") (reason "vector-search loop suspected: ?n calls in single trace")))
```
- pattern_summary: "agent calls `vector-search` >30 times in one trace → 87% chance of bad outcome"
- support_traces: 14 examples (see trace UI)
- historical_impact: would have caught 11 of 14 (78%) of last quarter's retrieval-loop incidents
- false_positive_estimate: 0.4% (would have falsely halted 3 of ~700 legitimate runs)
- existing_rule_overlap: none

Operator reviews; deploys with the threshold loosened to 40. The
proposal, the operator's edit, and the post-deploy outcome get
logged to the decision journal so the next mining run treats the
operator's threshold preference as prior evidence.
