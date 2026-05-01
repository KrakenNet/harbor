=============================================================================
                       KB SYNC: CODE/DOCS ↔ KB ARTICLES
=============================================================================

[Trigger] (post-merge to main, or weekly cron, or manual /sync)
             │
             ▼
[1. fetch_diff]  (tool: `git-ops` — files changed since last sync run)
             │
             ▼
[2. classify_change_scope]  (agent: `classifier`)
  → scope: schema | api | feature | refactor | docs-only | unrelated
             │
             ├──► [IF unrelated / docs-only without code change] ──► [Skip]
             │
             ▼
[3. resolve_kb_targets]
  (knowledge: route via `_index.md` mapping changed files → KB articles)
             │
             ▼
[4. retrieve_current_articles]
  (knowledge: load each affected article + its companion gap file)
             │
             ▼
[5. detect_drift]  (agent: `extractor` over both sides)
  → drift type: enum-added | field-renamed | endpoint-changed | behavior-shift
             │
             ▼
[6. governor: `fact-half-life`]
  (any article older than X days touching changed code is force-reviewed
   even if no obvious drift detected)
             │
             ▼
[7. propose_edits]  (agent: doc-rewriter — minimal-diff style)
             │
             ▼
[8. governor: `show-your-work`]
  (each edit must reference the source-code line that motivated it —
   no orphan rewrites)
             │
             ▼
[9. open_pr]  (tool: `git-ops` branch + GitHub API PR open)
             │
             ▼
[10. governor: `hitl-trigger`]
  (KB owner is requested as reviewer for any article in their domain)
             │
             ▼
[11. write_provenance]
  (knowledge: edge from KB article → commit SHA that motivated the update)
             │
             ▼
[12. write_outcome]
  (memory: which proposed edits got merged / rejected; trains future
   drift detection sensitivity)
=============================================================================

## Inputs

- repo + base ref (default: last successful sync commit)
- KB root path

## Step types

| #  | Step                     | Type      | Notes |
|----|--------------------------|-----------|-------|
| 1  | fetch_diff               | tool      | `git-ops` |
| 2  | classify_change_scope    | agent     | `classifier` |
| 3  | resolve_kb_targets       | knowledge | `_index.md` routing |
| 4  | retrieve_current         | knowledge | article + gap file |
| 5  | detect_drift             | agent     | `extractor` |
| 6  | half_life_gate           | governor  | `fact-half-life` |
| 7  | propose_edits            | agent     | doc-rewriter |
| 8  | show_your_work           | governor  | requires source citation |
| 9  | open_pr                  | tool      | GitHub API |
| 10 | hitl_request             | governor  | KB owner as reviewer |
| 11 | write_provenance         | knowledge | article ↔ commit |
| 12 | write_outcome            | memory    | trains drift sensitivity |

## Outputs

- PR per KB article with motivated edits
- updated provenance edges
- outcome row per edit

## Why it's a good demo

Railyard's own KB conventions (the `docs/` tree with gap files, see project
CLAUDE.md) make this an "eats its own dogfood" workflow. Pairs naturally
with `knowledge-half-life-sweep`, `provenance-graph`, and the
`code-dependency-kg`.
