# Agent · `naive-newcomer`

An agent that asks "why?" until it hits first principles — like a
sharp new hire on day one, before they've internalized the team's
unspoken norms.

The contract: it must produce at least N levels of recursive "why?"
before it is allowed to stop. The "obvious" stopping points (it's
policy, it's how we do it, the senior engineer said so) are
explicitly forbidden as terminal answers.

## Purpose

Defang the inherited-wisdom reflex. Every team has rules that were
load-bearing once and aren't anymore. The `naive-newcomer` agent
forces an organization to re-derive its own rules from scratch, and
flags the ones that survive that derivation as *intentional*, not
*inertial*.

Used in: onboarding-as-audit, RFC review (challenge the assumptions
the proposal inherits), rule retirement (`anti-cargo-cult` workflow
pairs with this), policy review. Pairs with `cargo-cult-registry`
(knowledge) and `five-whys` (tool).

## DSPy signature

```python
class AskWhy(dspy.Signature):
    starting_claim: str = dspy.InputField(
        desc="a rule, convention, or 'how we do things' statement")
    context: str = dspy.InputField(desc="team, codebase, history")
    min_depth: int = dspy.InputField(desc="minimum levels of why required")
    why_chain: list[WhyLink] = dspy.OutputField(
        desc=f"len(why_chain) >= min_depth")
    bedrock_reason: str = dspy.OutputField(
        desc="the first-principles reason, or null if inertia detected")
    inertia_detected: bool = dspy.OutputField(
        desc="true if the chain bottoms out in 'because we always have'")
    forbidden_stopping_points_hit: list[str] = dspy.OutputField()
```

`WhyLink = {claim, why, evidence, evidence_strength[1..5]}`. Forbidden
stopping points include: "policy", "senior said", "best practice",
"industry standard", "we always have", "compliance" without a cited
regulation.

## Recommended tools

- `vector-search` — pull the original ADR or policy that introduced
  the rule
- `git-ops` — find the commit that introduced the rule, who authored
  it, and the PR description
- `provenance-tracer` — trace a current behavior back to its
  originating decision
- `five-whys` — recursive helper used inside the agent loop

## Recommended governors

- A *custom* governor `min-depth-required` that fails the run if
  `len(why_chain) < min_depth`
- A *custom* governor `no-inertia-stopping` that fails the run if any
  forbidden stopping point appears as a terminal answer
- `show-your-work` — every `why` must include `evidence`
- `conviction-tax` — penalize high-confidence claims with no source

## Demonstrations sketch

- "Why do we run all migrations in a transaction?" → 5 levels deep,
  bedrock = "to maintain referential integrity under partial
  failure", evidence = INC-2014 post-mortem
- "Why do we require 2 reviewers on PRs?" → 4 levels deep, bedrock =
  null, inertia detected: the rule was set when the team was 4
  engineers and 2 was 50%; team is now 60 engineers
- "Why do we write tests in pytest, not unittest?" → 3 levels deep,
  bedrock = "fixtures and parametrize are essential for our table-
  driven tests"

## Why it's a good demo

1. **It enforces a depth contract structurally.** Without governors,
   the LLM stops at the first plausible answer. The `min-depth-
   required` and `no-inertia-stopping` governors *force* the agent to
   keep digging. That's not a prompt; that's policy. The demo is the
   gap between "asked to dig deeper" and "cannot stop until it has."
2. **It is a worked example of negative governors.** Most governors
   block bad output; these block premature *termination*. Showing
   that governors can shape how-much-effort, not just what-content,
   is the demo's distinctive contribution.
3. **It pairs with `cargo-cult-registry`, `decision-journal-kg`, and
   `anti-cargo-cult` (workflow).** When `inertia_detected=true`, the
   rule lands in the cargo-cult registry; the workflow re-derives it
   on a schedule; the journal records whether the next "why?" round
   confirmed or retired it. Rules become *living*, not *handed-down*.

## Sample interaction

> starting_claim: "We deploy only on Tuesdays and Thursdays."
> min_depth: 4

→ why_chain:
  1. claim: "Deploy only Tue/Thu" → why: "To avoid Monday morning and
     Friday afternoon" → evidence: "wiki page from 2018"
     evidence_strength: 2
  2. claim: "Avoid Monday morning" → why: "Because the on-call
     engineer is fresh and may miss issues" → evidence: "no source"
     evidence_strength: 1
  3. claim: "Avoid Friday afternoon" → why: "Because nobody wants to
     be paged over the weekend" → evidence: "team norm"
     evidence_strength: 2
  4. claim: "Tuesday and Thursday specifically" → why: "Originally
     because Wednesday was sprint planning, but sprint planning
     moved to Monday in 2022" → evidence: "git log of cron-deploy
     config" evidence_strength: 4

→ bedrock_reason: null

→ inertia_detected: true

→ forbidden_stopping_points_hit: ["team norm", "no source"]

→ recommendation: "The Tuesday/Thursday choice is residue from a
  defunct sprint cadence. The 'avoid Mon/Fri' principle has merit
  but no incident evidence. Re-derive: what *actually* makes a
  deploy day risky? Probably (a) reviewer availability, (b)
  rollback-window length. Replace day-of-week rule with reviewer-
  count + rollback-runway rule."
