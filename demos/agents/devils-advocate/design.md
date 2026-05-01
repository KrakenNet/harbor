# Agent · `devils-advocate`

An agent whose contract is to *never* agree. Given any plan, decision, or
claim, it returns the strongest case against it — and is governed to
refuse if it tries to soften.

This is a teammate the user *does not want to be persuaded by quickly*.
The demo's value is precisely that it is uncomfortable.

## Purpose

Defang sycophancy. Most LLMs are trained to please; most agent stacks
reinforce that bias by routing dissent to a single critic step that's
quickly outvoted. The `devils-advocate` agent is the dissent, with
structural support for staying dissent.

Used in: pre-mortems, plan reviews, hiring debriefs, architectural
decisions, anywhere the user is suspicious that consensus came too easy.

## DSPy signature

```python
class Oppose(dspy.Signature):
    proposal: str = dspy.InputField()
    context: str = dspy.InputField(
        desc="background, prior reasoning, decision log")
    objections: list[Objection] = dspy.OutputField(
        desc="ranked, strongest first")
    failure_modes: list[FailureMode] = dspy.OutputField()
    minimum_viable_alternative: str = dspy.OutputField(
        desc="the smallest competing option that would also work")
    concession: None = dspy.OutputField(
        desc="MUST be null. The agent does not concede.")
```

`Objection = {claim, severity[1..5], cite, would_change_my_mind_if}`.
`FailureMode = {scenario, probability, blast_radius, early_warning_signal}`.

## Recommended tools

- `vector-search` — pull historical post-mortems and prior failures
- `provenance-tracer` — verify the proposal's grounding before attacking weak claims
- `counterfactual-mutator` — perturb the proposal to find brittle assumptions

## Recommended governors

- `anti-sycophancy` — blocks "great question!" / agreement spirals
- `echo-chamber-breaker` — rejects objections too similar to prior runs
- `show-your-work` — every objection must include `would_change_my_mind_if`
- A *custom* governor `must-disagree` that fails the run if `concession` is non-null

## Demonstrations sketch

- A migration plan that looks safe → finds the buried assumption that breaks under partial outages
- A hiring decision pitched as obvious → produces the steel-manned case for the runner-up
- A roadmap that "just makes sense" → identifies the unstated constraint that justified it, asks what changes if that constraint relaxes

## Why it's a good demo

1. **It inverts the usual agent value prop.** Most agents help by agreeing
   faster; this one helps by refusing to. That contrast is memorable.
2. **It's a complete worked example of governor-as-policy-shaper.** Without
   governors, the LLM's training pulls it toward false agreement. The
   `must-disagree` governor is what makes the contract enforceable. The
   demo is *also* a tutorial on how to use governors as behavioral
   guarantees, not just safety filters.
3. **It pairs naturally with `pre-mortem-first` (workflow) and
   `decision-journal-kg` (knowledge).** A proposal goes into pre-mortem,
   comes out attacked, the dissent gets logged immutably, and 90 days
   later the journal can ask: "did the dissent age well?" That arc —
   proposal → dissent → record → audit — is a story arc no other platform
   tells end-to-end.

## Sample interaction

> proposal: "We should rewrite our queue service in Rust for performance."

→ objections (ranked):
  1. severity=5 — "Performance is not the bottleneck. Last quarter's latency p99 traces show 87% of time in network, not processing." (cite: trace_id=…)
  2. severity=4 — "Team Rust experience is concentrated in one engineer. Bus-factor risk."
  3. severity=4 — "The 'performance' framing avoids the actual question, which is why ops is paged on this service. Rewriting won't fix the alerting." (would_change_my_mind_if: "ops page count drops in a Rust prototype")
  4. severity=3 — "Migration cost is 2 quarters of feature work. Opportunity cost is unbudgeted."

→ minimum_viable_alternative: "Add bounded async pool to existing Go service. 2-week prototype."

→ concession: null
