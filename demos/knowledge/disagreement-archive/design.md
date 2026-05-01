# Knowledge · `disagreement-archive`

A knowledge base of unresolved internal debates — questions where smart
people on the same team came to different conclusions, and where the
team explicitly chose *not* to force a single answer. Kept open on
purpose, retrievable, and never silently closed.

Most orgs treat disagreement as a bug — escalate, decide, move on. The
`disagreement-archive` treats unresolved disagreement as a structured
artifact: a topic where the evidence is genuinely insufficient, where
context-dependence is real, and where flattening to one answer would
lose information the team needs.

## Purpose

The most expensive failure mode in alignment-heavy orgs is false
consensus: the team agrees on the surface, then quietly disagrees in
implementation, and ships incoherent product. The
`disagreement-archive` makes the disagreement legible. Anyone making a
related decision sees the debate, the named positions, and the
contexts under which each position dominates.

The two load-bearing innovations:

1. **Positions are *attributed*.** Disagreements are not "some say X,
   others say Y" — they're "Alice (architect, 8 yrs context on this
   service) says X under conditions C1; Bob (SRE, on-call lead) says Y
   under conditions C2." Anonymity collapses information.
2. **Resolution is opt-in.** A debate stays open until someone files
   evidence that flips a position, or until both sides agree the debate
   is now context-dependent and *should* stay open.

## Type

Knowledge Base (markdown documents) with chunked embeddings; one
document per debate, append-only sub-records for positions and evidence.

## Schema

Each debate document carries frontmatter:

```yaml
---
debate_id: <uuid>
title: <the question, phrased neutrally>
domain: <area of the question>
status: <open|context-dependent|resolved>
opened_at: <date>
opened_by: <person>
positions: [<position_id>]
evidence_count: <int>
last_activity: <date>
flag: <"do not flatten in summaries" | null>
---
```

Each `position` is a sub-record:

```yaml
position_id: <uuid>
held_by: <person>
held_by_role: <role + relevant context>
claim: <one-paragraph statement>
conditions_under_which_this_dominates: <prose>
evidence: [{ doc_id, summary, weight }]
last_updated: <date>
```

The `flag: "do not flatten in summaries"` is enforced by retrieval — any
agent summarizing a debate must surface both positions verbatim or
refuse to summarize.

## Ingest source

- Manual authoring in the KB UI when a thread escapes Slack
- Promotion from `meeting-transcript-memory` when the `extractor` agent detects a multi-turn unresolved disagreement
- The `steel-manner` agent contributes strengthened versions of opposing positions
- The `panel-of-five` agent decomposes its archetypes' divergences into debates

## Retrieval query example

> An agent is about to ship a PR that touches a known-debated area:

→ semantic search over `title + position.claim` for the PR's intent
→ filter: `status IN ["open","context-dependent"]`
→ returns: the debate, all positions verbatim, the conditions each
  position claims dominance under, and a hint to the PR author:
  "this area has an active debate; your PR's choice should either
  cite a position or note that it's making a stance"

## ACLs

- **Read**: workspace-wide; sensitive debates (HR, security, exec
  strategy) tagged for restricted readership
- **Write**: append-only — positions can be added, evidence can be
  added, but a position's original `claim` is immutable. A change of
  mind is a *new* position, attributed and dated, not a rewrite.
- **Audit**: every read produces a span; this matters because debates
  are exactly where after-the-fact "I knew that wouldn't work" claims
  are tempting

## Why it's a good demo

1. **It reframes a failure mode as an artifact.** Other catalog items
   capture decisions, mistakes, and forgotten knowledge. None of them
   capture *productive disagreement* — the kind that should not collapse
   into a single answer. This is the only primitive that lets a team
   keep a real debate open and queryable instead of letting it die in a
   Slack thread or a one-side-wins doc.

2. **It is the natural counterpart to `decision-journal-kg`.** The
   journal records what was decided. The disagreement archive records
   what *isn't* decided yet, and on purpose. Together they describe the
   org's full epistemic state: settled, unsettled-and-known, and the
   honest line between them.

3. **The "do not flatten" flag is structurally enforced.** A normal KB
   would let a `summarizer` agent produce "the team is divided on X" —
   a sentence that loses every important detail. This KB blocks that
   summary at the retrieval boundary. Either both positions surface, or
   nothing does. That's a real epistemic constraint, baked into the
   primitive.

## Sample read

> Engineer asks the platform: "should new services use Postgres or DynamoDB by default?"

→ debate retrieved: `debate_id=42`, status=`context-dependent`, open
  since 2023-Q4, 7 evidence entries
→ position 1: held by Yelena (Platform Lead, 12 yrs RDBMS experience).
  Claim: "Postgres by default unless the workload is genuinely
  write-skewed; complexity tax of running both is real."
  Conditions: "default tier services with < 10k writes/sec/instance."
→ position 2: held by Ravi (SRE, on-call rotation 3 yrs).
  Claim: "DynamoDB by default for new services we don't want to
  babysit; ops cost of Postgres at scale is the worst part of my
  on-call." Conditions: "any service the team can't commit to
  schema-migration discipline for."
→ flag set: do not flatten

→ engineer's PR will not get a one-line "the team prefers X" answer.
  They get both positions, both contexts, and the burden of saying
  which set of conditions their service is in. That's higher friction
  than a tidy default. It is also the *correct* friction.
