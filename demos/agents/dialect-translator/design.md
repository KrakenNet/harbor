# Agent · `dialect-translator`

An agent that rewrites a piece of text in a *different team's idiom* —
engineering ↔ sales ↔ legal ↔ support ↔ exec — preserving the
content while changing the vocabulary, density, and frame.

This is not translation between languages; it's translation between
*sub-cultures of the same company*. The contract is fidelity-of-fact
plus fluency-of-tribe.

## Purpose

Defang the "we shipped it but nobody understood why" reflex. Cross-
functional miscommunication isn't usually a logic problem; it's a
dialect problem. The same fact ("we deferred the launch") means
different things to engineering ("good, we needed the time"), sales
("bad, my Q is on fire"), and legal ("fine, but document the
decision"). The `dialect-translator` agent rewrites once-per-audience
so each team gets the version they can act on.

Used in: cross-functional comms, exec briefings, sales enablement
notes, legal-review drafts, support-team release notes. Pairs with
`email-drafter`, `meeting-notes`, and `tone-calibrator` (governor).

## DSPy signature

```python
class TranslateDialect(dspy.Signature):
    source_text: str = dspy.InputField()
    source_dialect: Literal["eng", "sales", "legal", "support", "exec",
                            "neutral"] = dspy.InputField()
    target_dialects: list[Literal["eng", "sales", "legal", "support",
                                  "exec"]] = dspy.InputField()
    fact_set: list[str] = dspy.InputField(
        desc="explicit list of facts that must survive translation")
    translations: dict[str, Translation] = dspy.OutputField(
        desc="keyed by target dialect")
    facts_dropped: dict[str, list[str]] = dspy.OutputField(
        desc="per dialect: facts intentionally omitted (e.g. legal
              jargon stripped from sales version)")
    facts_added: dict[str, list[str]] = dspy.OutputField(
        desc="per dialect: facts added to make the translation actionable
              (e.g. quota impact for sales)")
```

`Translation = {body, vocab_changes, density_change[shorter|longer|same],
frame_change}`.

## Recommended tools

- `vector-search` — pull prior comms in each target dialect to learn
  vocab and density
- `embed-text` — score whether the translation reads as in-dialect
- `tone-calibrator` (or its inputs) — match channel norms

## Recommended governors

- `tone-calibrator` — block tone mismatches per channel
- `schema-validator` — every fact in `fact_set` must appear in every
  translation (or be in `facts_dropped` with a reason)
- A *custom* governor `dialect-fidelity` that runs an embedding
  similarity check against the target dialect's prior corpus and
  fails translations that don't read as in-tribe
- `pii-redactor` — different audiences may not all see the same PII

## Demonstrations sketch

- Engineering RFC ("we'll deprecate the v1 API in 6 months") →
  sales: "Customers on v1 need a migration plan; here's the support
    timeline they'll see."
  legal: "Notice obligations under our Master Agreement § 4.3 require
    written notification 90 days prior to deprecation."
  exec: "12-week migration window, ~5% of customer base affected,
    revenue at risk: $X."
- Sales talking-track ("AI-powered platform with full guardrails") →
  eng: "Agentic system with policy enforcement via CLIPS rule engine
    and structured-output validation. Concrete claims: see governors
    list."
  legal: "Marketing language has implied warranties — confirm scope
    of 'full guardrails' against contract obligations."
- Legal redline ("data subject rights extend to derived inferences") →
  eng: "Need to be able to delete model outputs derived from a
    user's data, not just raw inputs. Implies output retention
    policy."
  support: "If a user invokes GDPR deletion, also delete agent
    memories and trace summaries derived from their data."

## Why it's a good demo

1. **It treats audience as a structural input, not a tone preset.**
   Every other "rephrase this" agent treats audience as a slider on
   formality. This one treats each dialect as a *fact-set transform*
   — what survives, what gets added, what gets dropped. That's a
   different agent shape, and the structured-output diff is the demo.
2. **It is a worked example of multi-target structured outputs.** One
   prompt, N translations, each with its own fidelity report. The
   governor stack guarantees fact-preservation across all N — a
   property no single LLM call can give you reliably without
   structural enforcement.
3. **It pairs with `meeting-notes` (agent), `email-drafter` (agent),
   `disagreement-archive` (knowledge), and `decision-journal-kg`
   (knowledge).** A meeting produces notes in neutral dialect;
   `dialect-translator` fans out to per-team comms; the journal
   records which translation each team acted on. When teams later
   disagree about what was "decided," the trace shows what each side
   read.

## Sample interaction

> source_text: "We're sunsetting the legacy reporting endpoint on
>   2026-12-01 to free up capacity for the new analytics pipeline."
> source_dialect: "eng"
> target_dialects: ["sales", "legal", "exec"]
> fact_set: [
>   "endpoint /v1/reports is deprecated",
>   "deprecation date: 2026-12-01",
>   "replacement is /v2/analytics",
>   "reason: capacity reallocation"
> ]

→ translations:
  sales:
    body: "Heads up — customers calling /v1/reports will need to
      migrate to /v2/analytics by Dec 1, 2026. We have ~7 months. The
      new endpoint has richer data; this is an upsell conversation,
      not a damage-control conversation. Customer success will draft
      a migration kit by end of next month. Affected accounts: ~120
      (we'll send a list)."
    vocab_changes: "deprecated → 'migrate', sunsetting → 'transition'"
    density_change: longer
    frame_change: "from 'we are removing X' to 'customer journey
      from old to new'"
  legal:
    body: "Effective 2026-12-01, the /v1/reports API endpoint will be
      withdrawn. Customer agreements containing API SLAs (see § 4.3
      and § 7.1) require written notification ≥90 days prior. Draft
      notice attached. Reason for withdrawal: internal capacity
      reallocation; not for cause. Replacement endpoint /v2/analytics
      provided at parity or better functionality."
    vocab_changes: "sunsetting → 'withdrawn', free up → 'reallocation'"
    density_change: longer
    frame_change: "from operational decision to contractual obligation"
  exec:
    body: "Sunsetting /v1/reports on Dec 1. Affects ~120 accounts
      (~3% MRR exposure). Mitigated by /v2/analytics, which is
      already at parity. Capacity freed: ~15% of current data-tier
      load, redirected to the analytics roadmap. Net: a planned
      transition, not a risk."
    vocab_changes: "free up capacity → 'capacity reallocation, X% of
      data-tier load'"
    density_change: shorter
    frame_change: "from operational milestone to risk/value summary"

→ facts_dropped:
  sales: []
  legal: []
  exec: ["specific replacement path /v2/analytics — exec doesn't
    need the URL"]

→ facts_added:
  sales: ["~120 affected accounts (sales needs the count)",
    "migration-kit timeline (sales needs the artifact date)"]
  legal: ["§ 4.3 and § 7.1 obligations cite (legal needs the
    contract anchor)"]
  exec: ["~3% MRR exposure (exec needs the dollar number)",
    "15% capacity reclaimed (exec needs the upside)"]
