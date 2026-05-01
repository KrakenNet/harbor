# Knowledge · `intentional-non-features-kb`

A knowledge base of "why X isn't here" — features the org has
deliberately chosen *not* to build, capabilities a product
intentionally doesn't have, and behaviors that look like bugs but are
on-purpose absences. Kept on file specifically to prevent re-litigation.

Every product has a graveyard of "why don't we just...?" suggestions
that get raised, debated, and rejected, then re-raised six months later
by someone who wasn't around for the first round. The
`intentional-non-features-kb` is the citation that closes the loop:
"here's why we don't, here's when we last reviewed it, here's what
would change our minds."

## Purpose

Two specific costs this KB cuts:

1. The cycle of "great idea — we considered that — let me find the
   thread" that costs a team-week every quarter when a request resurfaces.
2. The agent or chatbot that, asked "why doesn't your product do X?",
   confabulates "we're working on it" or "I'm not sure" when the truthful
   answer is "we deliberately chose not to, here's our reasoning."

The load-bearing innovations:

1. **Non-features are *citable*.** Every entry has a stable URL; PMs
   linking to it in customer conversations is the explicit use case.
2. **Each entry has a `would_change_my_mind_if`** — the falsifiable
   condition under which the decision should be revisited. This is what
   keeps the KB honest: a non-feature without a flip-condition becomes a
   review item.
3. **Public-vs-internal split is structural.** Some non-features are
   safe to explain to customers ("we don't ship a mobile app because we
   focus on desktop power users"). Some aren't ("we don't auto-tune
   prompts because the legal review of unbounded model behavior would
   slow us down"). The KB stores both with explicit visibility flags.

## Type

Knowledge Base (markdown documents) with chunked embeddings;
append-only with revisit log.

## Schema

Each entry carries frontmatter:

```yaml
---
entry_id: <uuid>
title: <the question, phrased as customers ask it>
canonical_phrasing: <one-line non-feature description>
class: <product|api|policy|integration|monetization>
visibility: <public|customer-on-request|internal>
decided_at: <date>
decided_by: <person|squad>
linked_decision: <decision-id>          // → decision-journal-kg
linked_disagreements: [<debate-id>]     // → disagreement-archive
would_change_my_mind_if: <prose>
last_reviewed: <date>
review_cadence: <quarterly|annually|on-trigger>
trigger: <prose, optional — what observable would trigger early review>
status: <active|flipped|under-review>
---
```

Body sections: **What people ask** · **Why we don't** · **What we'd
need to see to reconsider** · **What we offer instead**.

## Ingest source

- The `decision-journal-kg`: any `Decision` with stakes=high tagged
  `non-feature` auto-creates a draft entry
- The `customer-faq-kb`: questions that recur and get explicit "we
  don't" answers get promoted here
- The `email-drafter` and `support-agent` flag candidates when they
  notice they've answered the same "why don't you?" question more than
  3 times in a month
- Manual authoring by PMs

## Retrieval query example

> Customer asks the support chatbot: "why don't you support real-time
  collaborative editing in your editor?"

→ semantic search over `title + canonical_phrasing` for the question
→ retrieves `entry_id=nf_018`, visibility=`public`
→ chatbot's response composes the *real* answer: "We've made a
  deliberate choice not to ship real-time co-editing. Last reviewed
  2026-01. Our reasoning is [body]. We'd reconsider if [the
  `would_change_my_mind_if`]. Here's what we offer instead: [body]."
→ the customer gets a direct, attributable answer instead of a
  hand-wave. The chatbot doesn't promise something the product team
  hasn't promised. The PM who wrote the entry is on file as the owner.

## ACLs

- **Read**: visibility flag is enforced server-side. `public` entries
  ship to customer-facing surfaces; `customer-on-request` entries are
  retrievable only by support agents in active conversations;
  `internal` entries are eng/PM-only
- **Write**: append-only — `flipped` and `under-review` are status
  transitions, not edits; the original reasoning is preserved
- **Audit**: every public retrieval produces a span — when the answer
  ships, the citation is logged

## Why it's a good demo

1. **It is the structural fix for "the agent makes promises the
   product hasn't made."** Most chatbots default to optimistic
   confabulation when asked about absent features. This KB makes the
   *deliberate-absence* answer authoritative and citable. Composes
   directly with `conviction-tax` (citations required) and the
   `redaction-on-egress` governor (internal entries can't leak to
   public surfaces by mistake).

2. **The `would_change_my_mind_if` field is the load-bearing
   epistemic constraint.** A non-feature decision that doesn't name
   its flip-condition is a permanent veto, which is rarely honest. By
   *requiring* the field at decision time, the KB turns "we don't"
   into "we don't, *yet, and here's what would change that*." That's
   the difference between strategic discipline and stubbornness, and
   it's what makes the entry trustworthy a year later.

3. **It is the only KB whose value increases with deliberate
   non-action.** Other knowledge bases grow by recording what was
   built. This one grows by recording what was rejected, on purpose,
   with reasoning. It's the most honest representation of a product's
   shape — *what isn't there is part of the design*.

## Sample read

> A new PM joins and asks Slack: "why don't we have a free tier?"

→ before three colleagues can dig up an old thread, the PM hits the
  KB. `entry_id=nf_004`, visibility=`internal`, last reviewed 6
  months ago, owner=Head of Growth.
→ body: "Free tier was rejected three times across 2023-2025.
  Reasoning: support cost per free user is high relative to conversion;
  prior tests showed paid trials convert at 4x free signups. Linked
  decision: `decision-journal-kg/d_211`."
→ would_change_my_mind_if: "either (a) self-serve support cost drops
  below $X via the new docs/agent stack, or (b) we identify a
  PLG-shaped product surface where free trials underperform free
  signup."
→ status: `under-review` (because the docs/agent stack is *literally
  what they are now shipping*, and condition (a) might be triggering).
→ the PM doesn't re-litigate the closed parts of the debate. They
  contribute to the under-review part of it. That's the whole point.
