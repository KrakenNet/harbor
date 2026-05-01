# Knowledge · `anti-pattern-kb`

A knowledge base of mistakes the org has made — what the mistake was,
how it manifested, and the *tell* that should have caught it earlier
next time. Built primarily by filtering the `decision-journal-kg` for
decisions whose outcomes contradicted their rationales.

A best-practices KB tells you what to do. An anti-pattern KB tells you
what you keep doing wrong, *with the early-warning signal you missed*.
That second part is the distinguishing one — and the part most
"lessons learned" docs leave out.

## Purpose

Most teams write a postmortem, learn one lesson, and forget. The
`anti-pattern-kb` makes the lesson retrievable in the moment when it
would help — not when the next postmortem is being written, but when
the *next decision is being made*. Each entry includes a "what would
have made us notice sooner?" field, which is the whole point.

The load-bearing innovations:

1. **Each entry has a `tell` — the early signal.** Not the postmortem
   smell. The thing observable while the bad decision was still
   reversible.
2. **Entries link back to the contradicted rationale**, so the agent
   making a similar decision sees not just "this went wrong" but "this
   went wrong *because* the team believed X, and X is a recurring belief
   here."
3. **Entries decay** — an anti-pattern that hasn't recurred in 18 months
   is archived, with the option to revive on next sighting. The KB
   tracks what the team is currently susceptible to, not what it
   theoretically could be.

## Type

Knowledge Base (markdown documents) with chunked embeddings; written
mostly by automation, curated by humans, append-only.

## Schema

Each anti-pattern document carries frontmatter:

```yaml
---
pattern_id: <uuid>
title: <the anti-pattern, phrased as a verb>
class: <architecture|process|comms|estimation|vendor|security|...>
first_observed: <date>
last_observed: <date>
recurrence_count: <int>
contradicted_rationale: <prose, the belief that turned out wrong>
tell: <the early signal that would have caught it>
detection_query: <optional CLIPS rule or trace query that would fire on the tell>
linked_decisions: [<decision-id>]      # → decision-journal-kg
linked_objections: [<objection-id>]    # objections that turned out to be right
status: <active|archived>
---
```

Body sections: **What we did** · **What happened** · **The tell we
missed** · **What we'd watch for next time** · **Examples in the wild**.

## Ingest source

- The `decision-journal-kg`: a query for decisions whose outcomes
  `CONTRADICTED` their rationales generates draft entries
- The `pattern-archaeologist` agent excavates anti-patterns from commit
  history (e.g., the same kind of revert recurring across services)
- The `auto-hypothesis` workflow promotes surprising postmortems into
  candidate entries
- HITL curation by tech leads / ops leads to confirm and write the `tell`

## Retrieval query example

> Pre-flight check on a draft change titled "consolidate three retry libraries into one":

→ semantic search hits `pattern_id=ap_071` titled "centralized retry
  abstraction adopted before its consumers stabilize"
→ returns: the rationale that was wrong last time ("centralization
  reduces drift"), the actual outcome (drift moved up the stack and
  became uglier), and the `tell`: **"if more than one of the consumers
  is currently mid-rewrite, you're early."**
→ agent attaches the warning to the PR description: not blocking, but
  visible. The author gets to address it, accept it, or note that this
  time differs.

## ACLs

- **Read**: workspace-wide for engineering and product anti-patterns;
  HR/security tagged for restricted readership
- **Write**: append-only — entries can be archived but not edited; a
  refined `tell` is a *new* entry that supersedes
- **Public/customer access**: never (these are internal blameless
  records, not marketing)

## Why it's a good demo

1. **It is the most direct application of the platform compounding.**
   The `decision-journal-kg` records every decision and its outcome.
   This KB is *built from* it — automatically — by mining the patterns
   where the team's beliefs were wrong. Pull out the journal and this KB
   has no input. Pull out this KB and the journal has no leveraged
   output. They are halves of the same idea.

2. **The `tell` field is the distinctive feature.** Every postmortem
   tool captures "what went wrong." Almost none capture "what was
   observable that we ignored." The `tell` is what makes the entry
   actionable in real time, and it's the field the `pre-mortem-first`
   workflow keys on: phase one of every plan checks whether any active
   anti-pattern's `tell` is currently true.

3. **Decay keeps the KB honest.** A list of every mistake the org has
   ever made would be both demoralizing and useless — too long to scan,
   too noisy to retrieve over. Archiving anti-patterns that haven't
   recurred in 18 months forces the KB to track the team's *current*
   susceptibilities. That's a different — and more useful — artifact than
   a comprehensive failure log.

## Sample read

> Engineer drafts a tech spec: "introduce a generalized event-bus to
  unify our 3 internal pub/sub flows."

→ `anti-pattern-kb` retrieves `pattern_id=ap_071` (premature
  centralization)
→ tell evaluation: are >1 of the consumer flows currently mid-rewrite?
  Cross-checking the `code-dependency-kg` says: yes, two of the three
  are.
→ surfaced: "The current state matches the early signal of a known
  anti-pattern. Last 3 attempts at this kind of consolidation in this
  org reverted within a quarter. The tell is currently true. You may
  still proceed; please document why this time is different in the
  spec's *Risks* section."

→ the spec author either changes course, or accepts the risk *in
  writing*, where it can be checked against later. The KB didn't
  prevent the decision. It made the recurrence cost the team something
  visible.
