# Tool · `five-whys`

The classical root-cause discipline as a tool. Take a claim, an
incident, a decision, or a code pattern. Ask "why?" Take the answer.
Ask "why?" again. Recur until the chain hits something that doesn't
have a "because" — a value, a constraint, a physical limit, a market
fact, a person's stated preference. That terminal node is bedrock.

The tool refuses to stop early. If a "why?" answer is hand-wavey
("because that's how it's done," "for performance"), the next "why?"
is harder, not easier. The chain ends at first principles, not at the
first plausible-sounding answer.

## Purpose

Distinguish "we do it this way because we always have" from "we do it
this way because [load-bearing reason]." Useful for incident reviews,
ADR backfills, governor-rule justification audits, and architectural
debates that go in circles.

## Inputs

| Field           | Type    | Required | Notes |
|-----------------|---------|----------|-------|
| `claim`         | string  | yes      | the assertion or observation to interrogate |
| `context_refs`  | []ref   | no       | docs / traces / KB articles the chain may consult |
| `max_depth`     | int     | no, 7    | "five" is folkloric; truncate after N |
| `terminal_kinds`| []enum  | no       | what counts as bedrock (default: physical / market / value / external / proven) |
| `style`         | enum    | no       | terse / discursive (default terse) |

## Outputs

| Field          | Type            | Notes |
|----------------|-----------------|-------|
| `chain`        | []WhyNode       | ordered claim → … → bedrock |
| `terminal_kind`| enum            | what kind of bedrock was hit |
| `cycles_detected`| []CycleNote   | when the chain loops |
| `confidence`   | float [0..1]    | how sure the tool is the chain bottoms out |
| `evidence`     | map[depth][]ref | citations supporting each level |

`WhyNode` carries: `level`, `assertion`, `because`, `kind`
(observation / inferred / cited / assumed), `evidence_refs`.

## Implementation kind

DSPy tool. The "is this answer actually a reason or is it just
restating the previous level?" check is what makes this DSPy: a
generic prompt produces five fluent answers that together explain
nothing, while the tuned signature pushes back when level N is
synonymous with level N-1.

## Dependencies

- LLM judge — primary recursive reasoner
- Sibling tools: `vector-search` and `provenance-tracer` — to ground
  intermediate "becauses" against real evidence rather than letting the
  chain become fiction
- `decision-journal-kg`, `adr-archive`, `cargo-cult-registry` — natural
  context sources
- `internal/tracing/` — the chain becomes a span tree (each "why?" is a
  child span), so reviewers can audit the reasoning step by step

## Side effects

LLM calls (one or more per level). May read across knowledge bases
declared in `context_refs`. No state mutation outside its own trace
spans.

## Failure modes

- Chain loops (level 3 says the same thing as level 1 in different
  words) → halted, `cycles_detected` populated; this is a useful
  finding, not an error
- Bedrock not reached within `max_depth` → returns the partial chain
  with `terminal_kind="truncated"` and a recommendation for what to
  investigate next
- Evidence retrieval finds nothing relevant → that level is marked
  `kind="assumed"` and confidence is dropped accordingly
- Multiple competing causes at one level → the tool fans out into a
  small DAG instead of refusing to answer; the output is then a graph
  not a chain, and the consumer is told

## Why it's a good demo

Three reasons:

1. **Recursion with grounding only works because Railyard has both.**
   The recursive structure comes from DSPy. The grounding at each level
   comes from `provenance-tracer`, `vector-search`, and the
   `decision-journal-kg`. Most platforms have one or the other; the
   combination is what lets a "why?" chain stay honest.
2. **It composes with every "where did this come from?" primitive.**
   Pairs with `cargo-cult-detector` (its findings are perfect
   `five-whys` inputs), the `naive-newcomer` agent (which uses this
   tool to interrogate its own assumptions), the
   `pattern-archaeologist` agent (which surfaces dead idioms; this
   tool checks whether they were ever justified), and the
   `decision-journal-kg` (where chains become permanent rationale
   rows).
3. **It changes the cost of asking "why?"** When the disciplined
   version of the question is one tool call away with traceable
   evidence, teams ask it more often, earlier, and on smaller
   decisions. That's a culture shift the platform enables, not a
   feature it ships.

## Sample interaction

> claim: "All outbound emails go through `email-send` with `delay=2s`."
> context_refs: [governors/email-rate.clp, runbooks/2024-q3-incident-71.md]

→ chain:
  1. why? → because the email rate-limit governor enforces a 2s spacing.
     evidence: governors/email-rate.clp
  2. why? → because in 2024-Q3 we hit Mailgun's burst limit and got
     soft-suspended for 4 hours. evidence: runbooks/2024-q3-incident-71.md
  3. why? → because Mailgun applies a per-account QPS cap that the
     starter plan doesn't disclose in advance. evidence:
     adr-archive/adr-0142-email-vendor-choice.md
  4. why? → because email reputation is rate-limited at the receiver
     level and Mailgun amortizes that across customers. (kind: external,
     terminal_kind=market)
→ terminal_kind: market
→ confidence: 0.92

The chain just demonstrated that the 2s delay is justified all the
way to a market-level fact. That's filed into `decision-journal-kg`
and protects the rule from a future `cargo-cult-detector` sweep.
