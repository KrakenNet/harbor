# Tool · `embedding-cartographer`

Take a corpus of embedded items — documents, memories, traces, support
tickets, anything with a vector. Cluster them, project to 2D, and
auto-name the regions. Returns a navigable map you can click through to
see what your data actually contains.

Most "we have a vector store" demos stop at retrieval. This tool steps
back: instead of asking "find things like this query," it asks "what
*shape* is the corpus?" Topics, clusters, gaps, outliers — surfaced as a
map, not a list.

## Purpose

Help operators, data owners, and curious agents understand a corpus at
a glance. Find content gaps. Spot drift over time (re-run the
cartographer monthly and diff the maps). Identify clusters that warrant
their own knowledge-base or their own specialized agent.

## Inputs

| Field          | Type    | Required | Notes |
|----------------|---------|----------|-------|
| `source`       | enum    | yes      | knowledge-base / memory-store / trace-corpus / arbitrary table |
| `selector`     | string  | yes      | KB id / memory-store id / SQL filter |
| `vector_column`| string  | no       | inferred when source is a known one |
| `cluster_count`| int \| "auto" | no, "auto" | HDBSCAN if auto, k-means with k otherwise |
| `naming`       | enum    | no       | llm / tfidf / hybrid (default hybrid) |
| `time_window`  | string  | no       | restrict to a date range for drift studies |

## Outputs

| Field        | Type            | Notes |
|--------------|-----------------|-------|
| `regions`    | []Region        | id, name, centroid, member count, top examples |
| `points`     | []Point         | id, x, y, region_id |
| `outliers`   | []string        | item ids that fit no region |
| `coverage`   | float [0..1]    | fraction of items assigned to a region |
| `map_url`    | string          | rendered HTML map artifact |

## Implementation kind

DSPy tool. The clustering and projection are deterministic (HDBSCAN +
UMAP). The *naming* — looking at top-K members of a region and writing
a 2-3 word label that fits the cluster — is what makes this DSPy:
generic LLM prompts produce names like "Various topics" and the DSPy
signature is what gets you to "Q4 churn complaints (post-sale)."

## Dependencies

- `umap-learn` — 2D projection
- `hdbscan` — density-based clustering
- Sibling tools: `vector-search` (member sampling), `embed-text` (for
  ad-hoc query points overlaid on the map)
- LLM judge for region naming
- `internal/tracing/` and `internal/rag/` — corpus sources

## Side effects

Read-only against the source corpus. Writes a map artifact (HTML +
JSON) to a configured artifact store and emits a span. Idempotent on
the same corpus + same parameters.

## Failure modes

- Source too small (<50 points) → returns the points without clustering
  and a `degenerate=true` flag
- All points collapse to one region → naming returns the single region;
  this is itself a useful signal ("the corpus is homogeneous")
- LLM naming returns a duplicate name across regions → suffixed with a
  disambiguator; recorded in warnings
- UMAP non-determinism → same `seed` produces same map; reported in
  output for reproducibility

## Why it's a good demo

Three reasons:

1. **Railyard already stores the embeddings.** Every doc, memory, and
   trace is already vectorized for retrieval — the cartographer just
   surfaces what was already there. On platforms that treat the vector
   store as a black box behind a search API, this is a separate
   pipeline; here it's a tool call.
2. **It composes with the platform's data-quality story.** Pairs with
   `half-life-kb` (decay overlaid as color), `provenance-graph` (color
   regions by source-trust score), the `trace-shape-anomaly` ML
   primitive (region-level shape anomalies), and `decision-journal-kg`
   (overlay decision density per topic). One map, many lenses.
3. **It changes how operators think about a knowledge base.** Today
   the question is "is the right answer in there?" After the
   cartographer, the question becomes "what topics are *missing*?" —
   measured by gaps and sparsely-populated regions on the map.

## Sample interaction

> source: knowledge-base
> selector: kb_id=customer-faq
> cluster_count: auto
> time_window: last 90 days

→ regions:
  - "Onboarding & SSO setup" — 312 items
  - "Billing disputes (annual)" — 188 items
  - "API rate-limit confusion" — 144 items
  - "Mobile app crash on iOS 18" — 73 items (new this window vs. prior)
  - "Refund policy clarifications" — 41 items
→ outliers: 27 items
→ coverage: 0.97
→ map_url: artifacts/cartographer/2026-04-30-cust-faq.html

The "Mobile app crash on iOS 18" cluster is brand new compared to last
month's run — that signal goes to the `triage` agent's routing table
and to a fresh row in the `open-questions-kb`.
