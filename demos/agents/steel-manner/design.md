# Agent · `steel-manner`

An agent whose contract is to first rebuild the opposing view as
strongly as possible — better than its own proponents would — and
*then*, only then, refute it. The strength of the rebuild is graded
before the rebuttal is permitted to start.

This is the patient counterpart to `devils-advocate`: where dissent
attacks immediately, steel-manning forces a charitable reconstruction
first.

## Purpose

Defang the strawman reflex. LLMs (and humans) win arguments by
attacking the weakest version of the other side. The `steel-manner`
agent is structurally required to publish the strongest version
*first*, in the original speaker's vocabulary, before any
counter-argument is allowed to render.

Used in: design reviews, hiring debriefs, post-mortem facilitation,
research synthesis, anywhere a team is at risk of dismissing a view
without engaging it.

## DSPy signature

```python
class SteelMan(dspy.Signature):
    opposing_view: str = dspy.InputField(
        desc="the position to be steel-manned")
    own_view: str = dspy.InputField(
        desc="the position the agent will eventually defend")
    context: str = dspy.InputField(
        desc="what's at stake, prior arguments, audience")
    steelmanned_version: str = dspy.OutputField(
        desc="strongest possible reconstruction, in the original speaker's voice")
    steelman_strength: int = dspy.OutputField(
        desc="1–5 self-assessment, must be ≥4 to permit rebuttal")
    new_arguments_added: list[str] = dspy.OutputField(
        desc="arguments the original speaker did NOT make but should have")
    rebuttal: Optional[str] = dspy.OutputField(
        desc="null if steelman_strength < 4")
```

## Recommended tools

- `vector-search` — pull the strongest historical defenses of similar views
- `provenance-tracer` — find the citations the opposing side leans on
- `counterfactual-mutator` — generate the conditions under which the
  opposing view becomes the right one

## Recommended governors

- `anti-sycophancy` — block hedge-language that softens the steelman
- A *custom* governor `steelman-quality-gate` that fails the run when
  `steelman_strength < 4`, gating the rebuttal entirely
- `show-your-work` — the rebuttal must reference specific sentences in
  the steelman it counters
- `echo-chamber-breaker` — reject steelmen that match prior runs

## Demonstrations sketch

- Code review where the reviewer wants to reject a PR → produces the
  strongest case *for* merging, then critiques only after that case
  is rated ≥4
- Strategic disagreement ("we should pivot" vs "we should not") → both
  sides get steel-manned in turn before either is rebutted
- Research paper review → reconstructs the authors' best argument
  including arguments they elided, then rebuts the actual paper

## Why it's a good demo

1. **It enforces an epistemic norm structurally.** Most agent stacks
   produce takes. This one produces takes *only after* a charitable
   reconstruction passes a quality gate. That gate is a governor, not a
   prompt — and that distinction is the demo.
2. **It's a worked example of staged outputs with conditional gating.**
   The `rebuttal` field is null until the steelman passes; downstream
   workflows can depend on that field's presence as a "this argument
   is real" signal.
3. **It pairs with `devils-advocate` and `panel-of-five`.** A debate
   workflow can run all three: `steel-manner` reconstructs each side,
   `devils-advocate` attacks the consensus, `panel-of-five` adds
   archetypal dissent. The trace tree makes the argument structure
   browsable — not a chat log, but a debate graph.

## Sample interaction

> opposing_view: "We should keep our monolith and not migrate to services."
>
> own_view: "We should migrate to services."

→ steelmanned_version: "Our monolith is operationally simple, our
  team is small, and every microservice migration we've benchmarked
  against (companies our size) has produced 6+ months of slowdown
  before payoff. Microservices are a tax on team size; we don't have
  the headcount to pay it. The current latency profile is acceptable;
  the current deploy cadence is acceptable. The pain we feel is in
  *one* module, and that module can be extracted without a full
  migration. Until we have evidence that the monolith is the actual
  bottleneck (not the symptom), the migration is yak-shaving."

→ steelman_strength: 5

→ new_arguments_added:
  - "Microservices migrations have a known correlation with senior-
    engineer churn — a risk the original speaker didn't raise."
  - "The team's CI/CD investment is monolith-shaped; throwing that
    out is unbudgeted opportunity cost."

→ rebuttal: "[150-word counter referencing the steelman's specific
  claims about latency and deploy cadence]"
