# Agent · `constraint-surfacer`

An agent that turns *implicit team assumptions* into *explicit specs*.
It reads a proposal, a doc, or a chat thread and asks: "What is this
text *assuming*?" Then it writes those assumptions down as
constraints, with a flag for which ones are actually verified.

## Purpose

Defang the unspoken-norm reflex. Most team disagreements turn out to
be disagreements about constraints nobody wrote down: "we have to
support Postgres", "we don't ship on Fridays", "our customers won't
tolerate breaking changes." These constraints shape decisions
invisibly until someone violates one and discovers it the hard way.
The `constraint-surfacer` agent makes them visible.

Used in: RFC review, new-hire onboarding ("here are the rules we
forgot we have"), cross-team coordination, post-mortem ("which
constraint did we violate?"). Pairs with `intentional-non-features-
kb` (knowledge), `naive-newcomer` (agent), and `decision-journal-kg`
(knowledge).

## DSPy signature

```python
class SurfaceConstraints(dspy.Signature):
    text: str = dspy.InputField(
        desc="proposal, doc, chat thread, or codebase region")
    org_context: str = dspy.InputField(
        desc="team, prior decisions, known guardrails")
    constraints: list[Constraint] = dspy.OutputField()
    constraints_with_no_source: list[str] = dspy.OutputField()
    contradictions: list[Contradiction] = dspy.OutputField()
    suggested_explicit_spec: str = dspy.OutputField(
        desc="a markdown spec listing the surfaced constraints")
```

`Constraint = {assumption, kind[hard|soft|aspiration], source,
verified[true|false|unknown], if_violated_what_breaks}`.
`Contradiction = {constraint_a, constraint_b, why}`.

## Recommended tools

- `vector-search` — pull prior ADRs, RFCs, and chat history
- `provenance-tracer` — trace a stated constraint to its origin
- `git-ops` — find code that *enforces* (or contradicts) a stated
  constraint
- `embed-text` — match informal phrases ("we don't really do X") to
  formal constraints

## Recommended governors

- `show-your-work` — every constraint must have a `source` or be
  flagged in `constraints_with_no_source`
- `conviction-tax` — penalize hard-flagged constraints with no source
- A *custom* governor `no-invented-constraints` that fails the run if
  the agent adds constraints absent from the input text *and* not
  present in `org_context`
- `schema-validator` — `if_violated_what_breaks` is required for hard
  constraints

## Demonstrations sketch

- An RFC saying "we'll add a Redis cache" → surfaces: "assumes ops
  is willing to take on a new stateful service" (no source), "assumes
  reliability budget allows a non-essential dependency" (no source)
- A code review comment "we don't accept PRs without tests" →
  surfaces: hard constraint, source = CONTRIBUTING.md, contradiction:
  the README example PR has no tests
- A roadmap doc "we'll launch in EU next quarter" → surfaces: assumes
  GDPR readiness, assumes data-residency stack exists, assumes
  pricing supports EUR

## Why it's a good demo

1. **It treats text as evidence of unspoken policy.** Most agents
   treat text as a task to complete. This one treats text as a
   *symptom* whose generative rules are what matters. That reframing
   — "what does this text assume the world is like?" — is a different
   axis of agent value, and it's hard to demonstrate without
   structured outputs and provenance retrieval.
2. **It is a worked example of negative evidence.** The
   `constraints_with_no_source` field is the agent's *uncertainty*
   surfaced as data — "I see this assumption, I cannot find its
   origin." Most LLMs hide that uncertainty inside hedging language;
   this agent makes it queryable.
3. **It pairs with `intentional-non-features-kb`, `decision-journal-
   kg`, and `panel-of-five` (agent).** Surfaced constraints become
   journal entries; non-features become explicit; the panel can
   review proposals against a *named* set of constraints rather than
   a vibe. Over time the org accumulates a constraint registry that
   anchors every decision review.

## Sample interaction

> text: "I propose we replace our SQL queries with an ORM for type
>   safety."

→ constraints:
  - assumption: "Type safety in queries is a current pain"
    kind: soft, source: null,
    verified: unknown,
    if_violated_what_breaks: "the proposal's premise"
  - assumption: "ORM performance is acceptable for our query mix"
    kind: hard, source: null,
    verified: false,
    if_violated_what_breaks: "p99 latency budget on /reports endpoint"
  - assumption: "Team is willing to learn the ORM's DSL"
    kind: soft, source: null,
    verified: unknown,
    if_violated_what_breaks: "adoption velocity"
  - assumption: "Migrations are simpler with the ORM than with raw SQL"
    kind: aspiration, source: null,
    verified: unknown,
    if_violated_what_breaks: "the proposal's payoff"

→ constraints_with_no_source:
  - "All four constraints — none are sourced from the proposal text
     or org_context."

→ contradictions:
  - constraint_a: "ORM performance is acceptable",
    constraint_b: "p99 latency budget is 50ms (org_context)",
    why: "Most ORMs over our query shape produce 2–3x more SQL
      round-trips. Without a benchmark, this proposal cannot honor
      the existing latency constraint."

→ suggested_explicit_spec:
  ```
  ## Constraints this proposal must address
  - HARD: p99 latency on /reports must remain ≤50ms (current org SLO).
  - HARD: migration tooling must support our existing partitioned
    tables.
  - SOFT: team training cost must fit in next quarter's budget.
  - SOFT: the type-safety pain point must be quantified (current
    bug rate from query typos) before the proposal is approved.
  ```
