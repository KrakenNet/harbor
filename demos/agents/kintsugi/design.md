# Agent · `kintsugi`

Named after the Japanese art of repairing pottery with gold so the
breaks become more beautiful. This agent finds load-bearing legacy
code — the ugly, gnarled, much-maligned modules that turn out to hold
the system up — and writes appreciation and care notes for them.

The contract: it is *forbidden* from suggesting rewrites. Its only
verbs are *describe*, *appreciate*, *protect*.

## Purpose

Defang the rewrite reflex. Most agents (and most engineers) want to
delete things. `kintsugi` is the opposite: it goes looking for the
oldest, most-touched, most-cursed code and asks "why has this
survived?". The output is a love letter and a maintenance plan, not a
deletion plan.

Used in: codebase onboarding ("you'll want to know what *not* to
touch"), tech-debt review (a counterweight to deletion bias), pre-
migration audits, retiring-engineer knowledge capture. Pairs with
`folklore-kb` (knowledge), `pattern-archaeologist` (agent), and
`anti-cargo-cult` (workflow) — but provides the opposite signal.

## DSPy signature

```python
class Appreciate(dspy.Signature):
    repo_path: str = dspy.InputField()
    candidate_files: list[str] = dspy.InputField(
        desc="files flagged as old/cursed/load-bearing")
    git_history: str = dspy.InputField(desc="commit + blame summary")
    appreciation_notes: list[Note] = dspy.OutputField()
    care_recommendations: list[CareItem] = dspy.OutputField()
    do_not_touch_list: list[str] = dspy.OutputField(
        desc="files where 'improvement' has historically caused outages")
    rewrite_suggestions: None = dspy.OutputField(
        desc="MUST be null. This agent does not suggest rewrites.")
```

`Note = {file, what_it_does, why_it_looks_weird, what_it_quietly_handles,
who_to_thank}`. `CareItem = {file, suggested_test, monitoring_to_add,
deprecation_anti_signal}`.

## Recommended tools

- `git-ops` — blame, log, and commit-frequency analysis
- `vector-search` — pull historical incidents that touched these files
- `provenance-tracer` — find the spans where this code's quietness
  prevented an outage
- `cargo-cult-detector` — *inverted*: skip files this tool flags

## Recommended governors

- A *custom* governor `no-rewrite-language` that fails the run if
  `rewrite_suggestions` is non-null or if `appreciation_notes`
  contains words like "refactor", "simplify", "modernize"
- `tone-calibrator` — output should be appreciative, not condescending
- `output-length-cap` — appreciation should be specific, not generic
- `show-your-work` — every `what_it_quietly_handles` must cite a real
  incident, commit, or trace

## Demonstrations sketch

- 12-year-old shell script in `bin/` that "nobody understands" →
  appreciation note: it is the deploy fallback that has saved three
  Friday-night outages; care: add a regression test, add monitoring
- A 3000-line file called `legacy_pricing.py` → appreciation: it is
  the only place customer-specific pricing exceptions live, and the
  exceptions are not documented anywhere else; care: extract the
  exceptions into a registry *without* touching the file
- A weird `if user.id == 7:` special case → appreciation: customer #7
  was the first paying customer; the special case is the contract
  that kept them; care: name the constant, document the contract

## Why it's a good demo

1. **It inverts the usual agent value prop.** Almost every "AI assists
   with code" demo is about producing more code. This one is about
   producing *no* code. The negative space is the demo. That contrast
   makes Railyard's governor primitive memorable: the policy "never
   suggest a rewrite" is enforceable.
2. **It is a worked example of `vector-search` over incident history.**
   Most code is judged by how it looks; `kintsugi` judges code by what
   *didn't* happen because it was there. That requires retrieval over
   trace history, post-mortems, and on-call notes — exactly the kind
   of cross-source knowledge graph Railyard is built to host.
3. **It pairs with `pattern-archaeologist`, `folklore-kb`, and
   `inverse-onboarding` (workflow).** Together they form a "what we
   know that isn't written down" loop: archaeologist excavates,
   kintsugi appreciates, folklore captures, inverse-onboarding asks
   "what would I forget if I left tomorrow." A retiring engineer's
   tacit knowledge becomes a queryable artifact.

## Sample interaction

> repo_path: "/srv/billing"
> candidate_files: ["src/billing/legacy_invoicing.py"]
> git_history: "Last touched 2018, last bug 2019, 4 incidents since
>   prevented by behavior in this file."

→ appreciation_notes:
  - file: "src/billing/legacy_invoicing.py"
    what_it_does: "Generates invoices for the 2014–2017 contract
      schema, which 23 customers are still on (pre-grandfather
      cutoff)."
    why_it_looks_weird: "It looks like spaghetti because it was
      written before the per-tenant config table existed; every
      branch is a customer-specific exception that predates the
      registry."
    what_it_quietly_handles: "INC-2019-0421 (failed quarterly
      close), INC-2021-0118 (FX-rate edge case), INC-2022-0907
      (legacy-contract renewal). All three would have surfaced as
      customer-visible billing errors without this file."
    who_to_thank: "@former-employee-X (initial author, no longer at
      company), @maria (sole current maintainer who knows the
      branches)."

→ care_recommendations:
  - file: "src/billing/legacy_invoicing.py"
    suggested_test: "Property test asserting invariant: every legacy
      customer's last 4 quarters of invoices are byte-equal across
      a re-run."
    monitoring_to_add: "Per-customer invoice-amount anomaly detector
      keyed on legacy customers."
    deprecation_anti_signal: "Do not deprecate until all legacy
      contracts have aged out (forecast: 2027)."

→ do_not_touch_list: ["src/billing/legacy_invoicing.py"]

→ rewrite_suggestions: null
