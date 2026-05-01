# ML Model · `hallucination-scorer`

Per-claim grounding-confidence scoring. Decomposes an agent's answer
into atomic claims and scores each one against the provenance graph
the platform already maintains: which retrieved chunks, which tool
outputs, which prior memories actually support the claim.

It is not a self-consistency check. It uses Railyard's
trace-and-retrieval substrate to verify that each claim has a real
upstream source span, not just plausible-sounding text.

## Purpose

Tell the operator, per output, *which claims are grounded and which
ones aren't* — at claim granularity, not response granularity. Drives
the `conviction-tax` governor, the citation requirement on
`show-your-work`, and the human-review queue prioritization.

## Task type

Multi-stage: claim extraction (sequence labeling) → evidence retrieval
(over the trace's own retrieval cache) → entailment classification per
(claim, evidence) pair. Output is a per-claim probability the claim is
grounded.

## Inputs

| Field             | Type         | Notes                              |
|-------------------|--------------|------------------------------------|
| `output_text`     | string       | the agent's final answer           |
| `trace_id`        | uuid         | provides retrieval cache + tool outputs |
| `agent_id`        | uuid         | for per-agent calibration          |

## Outputs

| Field              | Type         | Notes                              |
|--------------------|--------------|------------------------------------|
| `claims[]`         | list[Claim]  | each = `{text, span, grounded_prob, supporting_spans}` |
| `overall_score`    | float [0..1] | aggregated confidence              |
| `unsupported[]`    | list[Claim]  | grounded_prob < threshold          |
| `weak_evidence[]`  | list[Claim]  | grounded but only by low-trust source |

## Training-data shape

Pulled from Railyard's own tables:

- `tracing.spans` — agent output text + the retrieval calls it made
- `rag.retrieval_results` — which chunks were returned, with scores
- `knowledge.documents` — source document text
- `memories.*` — prior memories surfaced into context
- `compliance.review_outcomes` — human verdicts on outputs

Each labeled example is `(claim_text, supporting_spans[],
human_verdict_grounded)`. The platform synthesizes weak supervision
by treating retrieval-hit answers as positives and answers-with-no-
retrieval as negatives, then refines on the human-verdict subset.

## Eval metric

1. **Per-claim AUROC** against human-verdict labels.
2. **Calibration error** — the score is consumed by governors that
   gate on absolute thresholds, so calibration is a hard SLO.
3. **Coverage** — fraction of claims where the model returns a
   confident verdict (vs. abstain).

## Serving target

gomlx (`internal/gomlx/`) — entailment head batched over (claim,
evidence) pairs; claim extraction is a small sequence-labeling head.
Both compose into one compiled graph.

## Inference call sites

1. **Post-execution**: every agent answer gets scored before it leaves
   the platform. Latency budget: 200ms for typical N=5 claims.
2. **Governor integration**: `conviction-tax` reads `weak_evidence[]`
   to penalize confident-but-unsupported claims; `show-your-work`
   reads `unsupported[]` to require explicit citations.
3. **Workflow integration**: the `pre-mortem-first` and
   `decision-journal-loop` flows log per-claim grounding scores into
   the immutable rationale row.

## Why it's a good demo

1. **It only works because the platform persists the retrieval
   cache, the tool outputs, and the memory hits per trace.** A
   bare-LLM hallucination check has nothing to ground against. A
   platform-aware scorer has the actual upstream spans the answer
   was supposed to be derived from.

2. **It's the cleanest example of "platform exhaust becomes platform
   ML."** Retrieval results were already being cached for traces;
   this model just reads them and asks "did the answer actually use
   the evidence?"

3. **It composes with `decision-journal-kg` and `provenance-graph`.**
   The journal stores per-decision rationale; the provenance graph
   stores fact-source paths; this scorer is the runtime that turns
   both into a per-claim verdict at output time.

## Sample interaction

Agent `support-agent` answers a billing question. Output:

> "Your plan includes 50,000 API calls per month and resets on the
> 1st. Overages are billed at $0.002 per call. We sent you an email
> about the upcoming price change on March 3rd."

Scoring:
- claim 1 (50,000 calls, resets 1st): grounded_prob 0.97 — supported
  by `rag.retrieval_results[span_a]` (plan-tier KB doc)
- claim 2 ($0.002 overage): grounded_prob 0.94 — supported by
  `rag.retrieval_results[span_b]` (pricing KB)
- claim 3 (email on March 3rd): grounded_prob 0.08 — NO supporting
  span found. Likely hallucinated.

→ unsupported: [claim 3]
→ `conviction-tax` governor flags the claim, response is rewritten
  to drop it before sending. Operator sees the flag in the trace UI.
