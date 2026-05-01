# Agent · `panel-of-five`

One prompt in, five archetypal critiques out: the PM, the SRE, the
Security engineer, the Individual Contributor, and the Executive. Each
critic has its own persona, its own concerns, and its own veto power.

This is the "have you talked to ___ yet?" agent. It surfaces the five
voices a proposal will face whether or not the author wants them to.

## Purpose

Defang the lonely-genius failure mode. Most plans die in cross-
functional review because the author optimized for one stakeholder.
The `panel-of-five` agent simulates the review *before* the meeting,
so the surprises happen on a draft instead of in front of leadership.

Used in: pre-meeting prep, RFC review, roadmap drafting, security
design review, SRE readiness reviews. Pairs with `pre-mortem-first`
(workflow) for proposals; pairs with `panel-of-five` becomes a fixture
of "before you send it" hygiene.

## DSPy signature

```python
class PanelReview(dspy.Signature):
    proposal: str = dspy.InputField()
    context: str = dspy.InputField(
        desc="org constraints, prior decisions, current pressures")
    panel: list[Critique] = dspy.OutputField(
        desc="exactly 5 entries: PM, SRE, Security, IC, Exec")
    consensus_concerns: list[str] = dspy.OutputField(
        desc="issues raised by ≥3 archetypes")
    blocking_vetoes: list[Veto] = dspy.OutputField()
    minimum_viable_revision: str = dspy.OutputField(
        desc="smallest change that addresses every blocking veto")
```

`Critique = {role[PM|SRE|Security|IC|Exec], primary_concern,
specific_objections, would_approve_if, severity[1..5]}`.
`Veto = {role, reason, what_would_lift_it}`.

## Recommended tools

- `vector-search` — pull each archetype's historical objections from
  prior reviews (e.g. all SRE comments on past RFCs)
- `provenance-tracer` — verify the proposal's load-bearing claims
  before the panel critiques them
- `embed-text` — diversify across critics so they don't converge on
  one shared concern

## Recommended governors

- `anti-sycophancy` — block "this is great, but..." sandwich language
- `echo-chamber-breaker` — reject critiques where 4+ critics raise the
  same objection (forces archetype divergence)
- A *custom* governor `roles-must-disagree` that fails the run if
  fewer than 3 of the 5 critics produce a blocking objection
- `show-your-work` — every objection must include `would_approve_if`

## Demonstrations sketch

- "We should adopt Kubernetes for our 30-engineer startup" →
  PM worries about velocity, SRE worries about on-call expansion,
  Security flags the RBAC surface, IC asks who maintains the
  manifests, Exec asks for the dollar number
- "Let's add a 'login with Google' option" →
  Security blocking, others mostly approve; demonstrates a *minority
  veto* pattern
- "Quarterly OKR: ship feature X" →
  Exec mostly approves, IC has implementation objections, PM notes
  market timing

## Why it's a good demo

1. **It manufactures cross-functional review on demand.** Most platforms
   give you one critic; Railyard's structured outputs + parallel-
   execution + governor enforcement turn one prompt into a five-row
   table that mimics the actual meeting. This is hard to replicate
   with a single LLM call and trivial with the right primitives.
2. **It demonstrates persona-as-policy.** Each critic isn't a system
   prompt; it's a sub-agent with its own demonstrations and
   `vector-search` slice (pull the SRE's actual past comments). The
   demo shows that personas become measurable when you wire them to
   real history.
3. **It pairs with `decision-journal-kg`, `pre-mortem-first`, and
   `disagreement-archive`.** A proposal goes through the panel,
   produces a `disagreement-archive` row for any unresolved veto, and
   the journal records which critics aged well. Over time the panel
   becomes self-tuning: archetypes whose objections kept being right
   gain weight.

## Sample interaction

> proposal: "We should ship a public API in 4 weeks."

→ panel:
  - PM: severity=3, primary_concern: "Rate-limit semantics aren't
    spec'd. Customers will design against undefined behavior."
    would_approve_if: "Public docs include explicit rate-limit policy
    and a sandbox tier."
  - SRE: severity=5, primary_concern: "We have no public-API on-call.
    Page volume from 'why is X 503' will land on the wrong team."
    would_approve_if: "Dedicated public-API alerting + runbook +
    on-call rotation in place 1 week before launch."
  - Security: severity=4, primary_concern: "Authentication path is
    untested under public load. CSRF and abuse vectors are
    unenumerated." would_approve_if: "Pen-test passed, abuse-pattern
    runbook published."
  - IC: severity=3, primary_concern: "Internal API consumers will
    silently degrade if we accidentally couple public/internal
    contracts." would_approve_if: "Versioned public contract,
    contract test in CI."
  - Exec: severity=2, primary_concern: "Strategic — does this open us
    to the partner channel we wanted, or to support volume we can't
    handle?" would_approve_if: "Forecast on support-ticket volume."

→ consensus_concerns:
  - "No production-readiness review has happened (PM, SRE, Security)."
  - "Contract semantics are unspec'd (PM, IC)."

→ blocking_vetoes:
  - SRE: "On-call coverage missing. Reason this lifts: rotation +
    runbook + alerting confirmed before launch."

→ minimum_viable_revision: "Push launch by 2 weeks; spend that time
  on (1) a published rate-limit policy, (2) an on-call rotation with
  tested alerting and runbook, (3) a pen-test pass, (4) a versioned
  contract with CI tests."
