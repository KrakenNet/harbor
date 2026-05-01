# Knowledge · `open-questions-kb`

A knowledge base of *questions without answers* — the things the team
knows it doesn't know, indexed by domain and kept queryable. The
inverse of every other KB: this one stores ignorance on purpose.

Most knowledge bases are optimized to surface answers. The
`open-questions-kb` is optimized to surface *the gaps*, so that an
agent that doesn't know the answer doesn't quietly hallucinate one —
it cites the open question, attributes it to the team that owns it, and
declines to make the gap up.

## Purpose

Two failure modes this KB addresses:

1. Agents that hallucinate confident answers to genuinely-unknown
   questions, because nothing in the system says "we don't know."
2. The same question being asked, half-answered, and forgotten weekly
   in three different Slack channels, because nothing keeps the question
   itself alive.

The load-bearing innovations:

1. **Questions are first-class artifacts** with owners, due-by dates,
   and downstream "what's blocked on this?" links.
2. **Retrieval prefers the open question over a stale answer** when an
   agent is asked something in the question's embedding region. Saying
   "we don't know yet" is treated as more honest than confabulating.
3. **A question can be partially answered** — answers attach as evidence
   *toward* the question, but the question stays open until an owner
   declares it closed. The unfinished state is the artifact.

## Type

Knowledge Base (markdown documents) with chunked embeddings; one
document per question, append-only evidence sub-records.

## Schema

Each question document carries frontmatter:

```yaml
---
question_id: <uuid>
title: <the question, phrased as a question>
domain: <area>
opened_at: <date>
opened_by: <person>
owner: <person|team>
priority: <low|medium|high|blocking>
blocking: [<decision-id|workflow-id|...>]   // what's stuck on this
status: <open|investigating|partially-answered|closed>
due_by: <date-or-null>
evidence: [<evidence-id>]
related_debates: [<debate-id>]              // → disagreement-archive
---
```

Each `evidence` sub-record:

```yaml
evidence_id: <uuid>
contributed_by: <person|agent>
contributed_at: <date>
summary: <prose>
weight: <weak|moderate|strong>
direction: <toward-yes|toward-no|context-dependent|tangential>
```

## Ingest source

- Manual authoring in the KB UI
- The `naive-newcomer` agent surfaces questions whose answers don't
  exist anywhere retrievable
- The `pre-mortem-first` workflow promotes "what we don't know" entries
  from its priors-retrieval phase into open questions
- The `meeting-notes` agent extracts unanswered questions from
  `meeting-transcript-memory`
- HITL: anyone can file an open question from any other surface

## Retrieval query example

> Agent is asked: "what's the worst-case latency on the new vector index?"

→ semantic search over `title + evidence.summary` for the question
→ retrieves: `question_id=q_312` titled "What's the p99 latency of the
  vector index under realistic write load?"
→ status=`investigating`, owner=`platform-team`, due_by=2026-05-15,
  blocking=[`decision-id=d_088`]
→ retrieval layer prefers this open question over any stale benchmark
  numbers an LLM might confabulate. The agent's response composes:
  "This is an open question on the platform team's docket — owner
  platform-team, due by 2026-05-15. Two pieces of partial evidence so
  far: (a) synthetic benchmark from 2026-03 showed p99 ≈ 80ms; (b)
  early load-test from this week showed degradation under bursty
  writes. No answer yet."

## ACLs

- **Read**: workspace-wide; sensitive questions (HR, exec, security)
  tagged for restricted readership
- **Write**: anyone can open a question; only the owner can close one;
  evidence is append-only
- **Public/customer access**: never

## Why it's a good demo

1. **It treats ignorance as a first-class data type.** No other catalog
   item does this. KBs store knowledge; KGs store relationships;
   memories store experience. This one stores the negative space, on
   purpose, with provenance — which is exactly the substrate that lets
   agents say "we don't know" without sounding evasive.

2. **It is the most natural anti-hallucination primitive.** The
   `conviction-tax` governor penalizes confident claims without
   citations. The `fact-half-life` governor penalizes claims with stale
   citations. The `open-questions-kb` does the third thing: it lets
   the agent cite the *absence* of an answer when one is expected. That
   completes the trio.

3. **It connects directly to `disagreement-archive` and
   `auto-hypothesis`.** A debate becomes an open question when both
   sides agree the answer needs evidence. The `auto-hypothesis`
   workflow turns open questions into queued experiments — closing them
   produces evidence which closes them. The flow from "we don't know"
   → "let's find out" → "we know" is structurally captured, not just
   aspirational.

## Sample read

> A workflow is about to recommend "auto-scale the vector tier 2x":

→ pre-flight check finds an open question, `q_312`, in the embedding
  region of vector-index latency under load. The question is
  *blocking*-priority and was opened specifically to inform decisions
  exactly like this one.
→ the workflow does not silently proceed. It surfaces: "this
  recommendation is in the blast radius of an open question owned by
  the platform team, due 2026-05-15. Recommend either: (a) wait for
  the answer, (b) proceed and tag the rollout for re-evaluation, or
  (c) propose evidence that closes the question."
→ the open question stayed alive long enough to influence the very
  decision it was opened to inform. That's the point of keeping it as
  a first-class artifact rather than a Slack message.
