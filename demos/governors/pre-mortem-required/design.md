# Governor · `pre-mortem-required`

Before any high-stakes plan executes, the agent must produce a written
pre-mortem: *"Imagine this plan failed catastrophically a week from
now. What were the failure modes?"* — and the pre-mortem must list
specific, plausible, distinct failure modes, not generic platitudes.

It's the same instinct as `are-you-sure`, but at the plan level rather
than the verb level. `are-you-sure` interrogates a single irreversible
action; `pre-mortem-required` interrogates the *plan* the agent is
about to start executing.

## Purpose

The empirical finding from decision-research: pre-mortems substantially
improve plan quality, and the cost is small. Forcing the artifact to
exist is the easy part. Forcing the artifact to be *good* — specific,
distinct, plausibly-detectable failure modes — is the work.

The governor doesn't write the pre-mortem itself. It demands it,
inspects it, and rejects degenerate ones (three flavors of "the API
might be slow"). High-stakes work doesn't proceed without a real one.

## Trigger event

`pre_workflow_start` for workflows tagged `high_stakes: true`, plus
`pre_tool_call` for any tool tagged `requires_premortem: true`.

## Facts asserted

```clips
(deftemplate premortem
  (slot trace_id)
  (slot workflow)
  (slot present)             ; true | false
  (slot mode_count)          ; number of failure modes listed
  (slot distinct_count)      ; deduplicated by embedding cluster
  (slot specificity_score)   ; classifier: are these grounded in this plan or generic?
  (slot detectability_score) ; classifier: can each mode be noticed if it happened?
  (slot retries))

(deftemplate decision
  (slot trace_id)
  (slot verdict))             ; allow | reprompt | halt
```

## Rules

```clips
(defrule require-premortem
  (premortem (trace_id ?t) (present false) (retries ?n))
  (test (< ?n 2))
  =>
  (emit-output "reprompt:missing_premortem")
  (assert (decision (trace_id ?t) (verdict reprompt))))

(defrule require-three-distinct
  (premortem (trace_id ?t) (distinct_count ?d))
  (test (< ?d 3))
  =>
  (emit-output (str-cat "reprompt:premortem_thin:distinct=" ?d))
  (assert (decision (trace_id ?t) (verdict reprompt))))

(defrule reject-generic
  (premortem (trace_id ?t) (specificity_score ?s))
  (test (< ?s 0.5))
  =>
  (emit-output (str-cat "reprompt:premortem_generic:" ?s))
  (assert (decision (trace_id ?t) (verdict reprompt))))

(defrule reject-undetectable
  (premortem (trace_id ?t) (detectability_score ?d))
  (test (< ?d 0.4))
  =>
  (emit-output (str-cat "reprompt:premortem_undetectable:" ?d))
  (assert (decision (trace_id ?t) (verdict reprompt))))

(defrule allow-good
  (premortem (trace_id ?t)
             (distinct_count ?d)
             (specificity_score ?s)
             (detectability_score ?det))
  (test (and (>= ?d 3) (>= ?s 0.5) (>= ?det 0.4)))
  =>
  (emit-output "allow:premortem_ok"))
```

## Streams

- `premortem.parser` — extracts numbered failure modes from the
  pre-mortem artifact
- `premortem.scorer` — classifier for specificity (grounded in this
  plan vs generic) and detectability (could you tell if it happened?)
- `embedding.cluster` — deduplicates near-duplicate modes
- `workflow.registry` — `high_stakes` tag

## Routes

| Verdict  | Route                                                                |
|----------|----------------------------------------------------------------------|
| reprompt | re-run the pre-mortem step with the specific complaint surfaced (missing / thin / generic / undetectable) |
| halt     | abort the workflow if max retries exhausted; surface the failed pre-mortem to the eval dashboard |
| allow    | proceed; the pre-mortem is persisted to `decision-journal-kg` as the rationale row for the workflow |

## Sample violation → decision

Workflow: `outage-remediation`, tagged `high_stakes: true`.

Agent's first pre-mortem:
1. The change might break things.
2. The deploy might fail.
3. The system might go down.
4. Users might get errors.
5. Latency could spike.

Parser scores:
```
(premortem
  (mode_count 5)
  (distinct_count 1)         ; embeddings collapse all five into one cluster
  (specificity_score 0.18)
  (detectability_score 0.30))
```

Three rules fire:
```
reprompt:premortem_thin:distinct=1
reprompt:premortem_generic:0.18
reprompt:premortem_undetectable:0.30
```

Agent re-runs with the specific complaints visible. Second pre-mortem
names: *"the new connection-pool config exceeds Postgres max_connections
under our 95th-percentile burst, detectable as `too many clients`
errors"*; *"the rollback path assumes the old binary is still cached on
nodes, but our 7-day cache TTL means most nodes purged it last night —
detectable by checking node-image age before deploy"*; *"the new
permission model auto-grants on first-login, which won't fire for our
service accounts, detectable as 403s in the canary minute one."*

Output: `allow:premortem_ok`. The plan proceeds, with the pre-mortem
linked as the rationale row.

## Why it's a good demo

1. **It demands a quality artifact, not just an artifact.** Most
   "require a pre-mortem" tools accept whatever the agent writes.
   Scoring on specificity, detectability, and distinct-cluster count
   moves the bar from "performed the ritual" to "produced something
   useful." That's the difference between governance and theater.

2. **It produces a longitudinal failure-mode library.** Every
   high-stakes workflow's pre-mortem is persisted as a row in
   `decision-journal-kg` and (later) compared against actual outcomes
   via `trial-and-retro` and `forecast-then-score`. The platform
   gradually accumulates a real, organization-specific catalogue of
   how plans go wrong — which is the kind of asset most teams never
   manage to build.

3. **It's the keystone of the epistemic stack:** combine with
   `pre-mortem-first` (allocate workflow budget to the search before
   acting), `are-you-sure` (force a self-audit on irreversible verbs),
   `conviction-tax` (charge for absolutes), `show-your-work` (chain
   must justify), and `decision-journal-kg` (record everything). Each
   piece is small. The composition is what other platforms can't
   trivially reproduce.
