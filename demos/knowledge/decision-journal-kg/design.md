# Knowledge · `decision-journal-kg`

A knowledge graph that stores decisions and their epistemic context. Every
non-trivial decision the platform makes — and every decision a human
approves through HITL — gets a node, with edges to its rationale, its
objections, the priors it cited, and (eventually) its outcome.

This is not a log. Logs are linear and ephemeral. This is a graph that
compounds: future decisions can query the graph for "what did we decide
last time we faced this?" and surface not only the decision but its
disagreement, its expected outcome, and its actual outcome.

## Purpose

Most teams lose institutional memory in two places: decisions whose
rationale dies with a Slack thread, and outcomes whose link to the
original decision is never made explicit. The `decision-journal-kg`
makes the rationale and the outcome co-locatable, queryable, and never
silently rewritten.

## Type

Knowledge Graph (Neo4j-backed via `internal/knowledge/`), with embedded
vector index on rationale and objection bodies for semantic retrieval.

## Node and edge types

```
Nodes:
  Decision        { id, title, made_at, made_by, plan_hash, stakes }
  Rationale       { body, conviction, source }
  Objection       { body, severity, would_change_my_mind_if, source }
  Prior           { trace_id_or_doc_id, relevance_excerpt }
  Outcome         { observed_at, success_score, surprises[] }
  Counterfactual  { body, why_not_chosen }
  Person          { id, role }

Edges:
  (Decision)-[:JUSTIFIED_BY]->(Rationale)
  (Decision)-[:ATTACKED_BY]->(Objection)
  (Decision)-[:CITES]->(Prior)
  (Decision)-[:HAS_OUTCOME]->(Outcome)
  (Decision)-[:CONSIDERED_BUT_REJECTED]->(Counterfactual)
  (Decision)-[:APPROVED_BY]->(Person)
  (Objection)-[:RAISED_BY]->(Person | Agent)
  (Outcome)-[:CONFIRMED]->(Objection | Rationale)
  (Outcome)-[:CONTRADICTED]->(Objection | Rationale)
```

The two outcome edges (`CONFIRMED` / `CONTRADICTED`) are the load-bearing
innovation: the graph remembers which voices were *right*, not just which
ones spoke.

## Ingest source

- HITL approval gates write `Decision` nodes automatically
- `are-you-sure` governor's audit step writes `Rationale` nodes
- `devils-advocate` agent writes `Objection` nodes
- `pre-mortem-first` workflow writes `Counterfactual` nodes
- `decision-journal-loop` workflow closes outcomes 7d / 30d / 90d post-decision

## Retrieval query example

A workflow about to make decision X queries:

```cypher
MATCH (d:Decision)
WHERE d.embedding ~ $candidate_decision_embedding
WITH d ORDER BY similarity DESC LIMIT 5
MATCH (d)-[:HAS_OUTCOME]->(o:Outcome)
MATCH (d)-[:ATTACKED_BY]->(obj:Objection)
OPTIONAL MATCH (o)-[r:CONFIRMED|CONTRADICTED]->(obj)
RETURN d.title, o.success_score, obj.body, type(r)
```

→ "Last 5 times we made a decision like this: 2 succeeded, 3 didn't.
   Here are the objections that turned out to be right."

## ACLs

- **Read**: workspace-wide for non-sensitive decisions; per-decision tag for sensitive (HR, security)
- **Write**: append-only — outcomes can be added but rationales and objections cannot be edited after a decision is finalized
- **Audit**: every read/write produces a span

## Why it's a good demo

1. **It's the showcase artifact for "the platform compounds."** A vanilla
   agent stack runs decisions and forgets them. This graph means the
   *next* decision is informed by the *last* decision and its outcome.
   That's the difference between an interesting toy and a system that
   gets better over time.

2. **It is the data substrate for three creative demos.**
   - `governor-rule-miner` (ML) trains on outcome-confirmed objections —
     patterns of objections that turned out to be right become rules.
   - `pre-mortem-first` (workflow) queries the graph in Phase 1
     (`retrieve_priors`).
   - `anti-pattern-kb` (knowledge) is *built from* this graph by filtering
     decisions whose outcomes contradicted their rationales.

   This isn't decoration; the graph is the load-bearing substrate.
   Pulling it out collapses three other demos.

3. **The append-only constraint is the whole point.** Rationales and
   objections are immutable once finalized. The graph is a record of
   what people *believed at the time*, not what they wish they had
   believed in retrospect. That's epistemically rigorous, structurally
   enforced, and rare. It is also the thing that makes outcomes
   meaningful — you can't tell whether a prediction was good if you let
   people quietly edit the prediction.

## Sample read

> "Should we migrate auth to OIDC?"

→ similar past decision: "Migrate auth to SAML" (made 2024-09)
→ outcome: `success_score=0.4`, `surprises=["downstream service B couldn't ingest SAML attrs"]`
→ objection that turned out to be right (`CONFIRMED`): "Service B's claims-handling code is hard-coded to OAuth shape" — raised by `devils-advocate`, not addressed in plan
→ counterfactual: "stay on OAuth, add IdP brokering" — rejected at the time for "added complexity"

→ surfaced into the OIDC decision before it's made. Same objection now
  must either be addressed or explicitly noted as accepted-risk.
