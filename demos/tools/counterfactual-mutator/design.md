# Tool · `counterfactual-mutator`

Take an input that produced verdict A. Find the smallest perturbation
that makes the agent (or classifier, or governor) produce verdict B.
Surface the diff: this is what the system was actually keying on.

Most explanations of model decisions come from inside the model. This
one comes from outside — by minimally torturing the input until the
output flips, you learn what the system *actually* cares about, which
is not always what you'd guess from reading the prompt.

## Purpose

Decision auditing, robustness probing, fairness checks, and "what did
the agent really pay attention to?" investigations. Cheaper than
mechanistic interpretability and more honest than asking the model to
explain itself.

## Inputs

| Field            | Type    | Required | Notes |
|------------------|---------|----------|-------|
| `target`         | ref     | yes      | agent / tool / governor / classifier to probe |
| `input`          | object  | yes      | the original input |
| `original_verdict`| any    | yes      | what the target produced for `input` |
| `flip_to`        | any     | no       | desired counter-verdict; default "anything else" |
| `mutation_kinds` | []enum  | no       | text-edit / numeric-nudge / field-swap / typo / synonym |
| `budget`         | int     | no, 50   | max attempts before giving up |
| `min_distance`   | bool    | no, true | search for the *smallest* mutation, not just any |

## Outputs

| Field            | Type            | Notes |
|------------------|-----------------|-------|
| `flipped`        | bool            | found a counterexample? |
| `mutated_input`  | object          | smallest perturbation that flipped the verdict |
| `diff`           | []ChangeOp      | structured edits from original → mutated |
| `distance`       | float           | normalized edit distance |
| `attempts`       | int             | tries used |
| `verdict_after`  | any             |       |

## Implementation kind

DSPy tool. The mutator uses a small LLM to propose minimal edits guided
by the verdict-flip objective and a deterministic loop to evaluate them.
Without DSPy's structured retry/refinement loop this devolves into "ask
GPT to rewrite the input and pray."

## Dependencies

- An LLM for proposing mutations
- The `target` execution path (agent executor, governor evaluator,
  classifier endpoint) — invoked many times
- `internal/tracing/` — every probe attempt becomes a span; the original
  run plus the search tree are visible together
- Sibling tools: `embed-text` for semantic-distance scoring, `regex-match`
  for field-edit operations

## Side effects

Many invocations of the target — this can be expensive. The tool emits
a parent span with all attempts as children so cost is auditable. No
state mutation outside its own span tree.

## Failure modes

- Budget exhausted without flip → `flipped=false`, returns the closest
  near-miss for inspection
- Target is non-deterministic → records verdict instability and stops,
  `error_kind="unstable_target"` (this is itself a useful signal)
- Mutation produces invalid input (schema fails) → that attempt is
  discarded, doesn't count against budget
- Target costs money → governor `cost-ceiling` may halt the search; the
  partial result is still returned

## Why it's a good demo

Three reasons:

1. **It's only practical because Railyard makes target invocation
   cheap and observable.** Re-invoking an agent 50 times with structured
   inputs and seeing every call as a span is a Railyard-shaped operation;
   on most platforms it's an afternoon of glue code per probe.
2. **It composes with the platform's interpretability story.** Pairs
   with `provenance-tracer` (now you have both "where did this come from"
   and "what would change it"), with `time-travel-replayer` (mutate the
   *intermediate* node, not just the input), and with the
   `prompt-drift-classifier` ML primitive (use mutator-found drift
   sensitivity as a training signal).
3. **It turns vague concerns into reproducible exhibits.** "I think the
   classifier is biased toward formal-sounding text" stops being a
   feeling once the mutator finds that swapping "y'all" for "everyone"
   flips the verdict in 4 of 5 sampled rows. That's a finding, not a
   vibe.

## Sample interaction

> target: governor `pii-redactor`
> input: `"Please email Jane at jane.doe@example.com about the meeting."`
> original_verdict: REDACT
> flip_to: ALLOW

→ flipped: true
→ diff:
  - replace "jane.doe@example.com" → "jane.doe at example dot com"
→ distance: 0.07
→ verdict_after: ALLOW
→ attempts: 3

The mutator just demonstrated that the redactor is keying on the literal
`@` character, not on the semantic content. That goes straight into a
gap-file for the `pii-redactor` governor and the `decision-journal-kg`
gets a row recording the discovery.
