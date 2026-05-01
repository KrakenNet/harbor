=============================================================================
                       THE KNOWLEDGE HALF-LIFE SWEEP
=============================================================================

A workflow that finds KB articles whose source code has drifted, scores
each by trust-decay, and either auto-proposes a refresh PR or marks the
article expired. Documentation in this model has a *physical half-life*:
unrefreshed knowledge loses confidence over time the way unrefreshed
backups lose recoverability.

The premise: stale docs aren't just wrong, they're *worse than absent*
because they confidently mislead. Most teams handle this by giving up.
Railyard handles it by treating every fact as decaying material and
giving the system the job of refreshing or burying it.

[Trigger] (weekly cron, or post-merge on changed-docs path, or on-demand
 via /sweep-stale)
             │
             ▼
=============================================================================
            PHASE 1: ENUMERATE + AGE (DECAY LAYER)
=============================================================================
[1. enumerate_articles]
  (knowledge: traverse `_index.md` routing — every article has a stated
   half-life class; default 90d, code-bound 30d, policy-bound 365d)
             │
             ▼
[2. compute_age_signals]  (parallel rule + tool)
  ├──► last_updated → calendar age
  ├──► last_verified_against_source → verification age
  ├──► source_files (from frontmatter) → git log age of each
  └──► linked enums / endpoints → existence check
             │
             ▼
[3. ml: `fact-half-life` scorer]
  (gomlx_inference: per-article trust-decay curve; produces a
   half-life-adjusted confidence score 0..1)
             │
             ▼
[4. governor: `fact-half-life`]
  (articles below threshold flagged for refresh OR expiration; trust
   decay is applied uniformly — exemptions require a documented reason)
             │
             ▼
=============================================================================
            PHASE 2: DETECT DRIFT (DIFF LAYER)
=============================================================================
[5. parallel_diff]
  ├──► structural diff: source enums / fields / endpoints vs article claims
  ├──► semantic diff: agent: `extractor` over both sides → drift card
  └──► gap-file diff: companion `*-gaps.md` already lists known
       inaccuracies — those are *acknowledged* drift, weighted differently
             │
             ▼
[6. classify_drift]  (agent: `classifier`)
  → drift type: enum-added | field-renamed | endpoint-changed |
    behavior-shift | example-rotted | none | unknown
             │
             ▼
[7. governor: `show-your-work`]
  (each drift call must link to the source-code line and the article
   line that disagree — no orphan "feels stale" verdicts)
             │
             ▼
[8. governor: `conviction-tax`]
  (high-confidence "no drift" verdicts on articles older than half-life
   are penalized — old + clean is suspicious)
             │
             ▼
=============================================================================
            PHASE 3: ROUTE PER ARTICLE (DECISION LAYER)
=============================================================================
[9. classify_disposition]  (agent: `classifier`)
  → action: refresh | expire | mark_provisional | escalate_to_owner |
    keep
             │
             ▼
[10. governor: `approval-policy`]
  (auto-refresh PRs allowed for low-blast-radius articles; high-traffic
   articles or policy-bound articles require KB owner sign-off)
             │
             ▼
[11. branch_action]  (conditional)
  ├──► refresh           → step 12 (auto-PR path)
  ├──► expire            → step 15 (deprecation path)
  ├──► mark_provisional  → step 17 (warning banner path)
  ├──► escalate_to_owner → step 18 (HITL path)
  └──► keep              → step 19 (record + advance)
             │
             ▼
=============================================================================
            PHASE 4: REFRESH OR BURY (ACTION LAYER)
=============================================================================
[12. agent: doc-rewriter — minimal-diff style]
  (rewrites only the lines disagreeing with source; preserves voice,
   examples, and structure of the original article)
             │
             ▼
[13. governor: `show-your-work`]
  (each line edit must cite source — auto-PRs are evidence-bound or
   they aren't filed)
             │
             ▼
[14. open_pr]  (tool: `git-ops` + GitHub API; KB owner requested as reviewer)
             │
             ▼
[15. expire_article]  (knowledge: move to `intentional-non-features-kb`
   with reason "X was here, now removed because Y" — the article doesn't
   just vanish, it leaves a tombstone)
             │
             ▼
[16. backfill_open_questions]
  (knowledge: any unresolved drift becomes an `open-questions-kb` row
   so the question survives the article's death)
             │
             ▼
[17. mark_provisional]
  (knowledge: prepend trust-decay banner to article; readers know
   confidence is below threshold)
             │
             ▼
[18. escalate_to_owner]  (tool: Slack / GitHub mention with the drift
   card and proposed disposition)
             │
             ▼
[19. record_no_action]
  (knowledge: row in scan history saying "evaluated, no drift, next
   re-check in N days")
             │
             ▼
=============================================================================
            PHASE 5: ARCHIVE + LEARN (FEEDBACK LAYER)
=============================================================================
[20. write_provenance]
  (knowledge: edge from each article → the source-code commits that
   either motivated this run or were judged irrelevant; future runs
   can compare without re-walking history)
             │
             ▼
[21. ml_signal: half-life calibrator]
  (gomlx_inference: which article classes drift fastest? rebalances
   the per-class half-life used at step 1; the system learns its own
   decay rates)
             │
             ▼
[22. notify_kb_owners]
  (tool: Slack — weekly digest of refreshed / expired / escalated
   articles with metric trends)
=============================================================================

## Inputs

- KB scope (default: full `_index.md` traversal)
- half-life class overrides (per article tag)
- dry-run flag (skips PR creation, useful for first runs)

## Step types

| #     | Step                       | Type                |
|-------|----------------------------|---------------------|
| 1     | enumerate_articles         | knowledge           |
| 2     | compute_age_signals        | rule + tool         |
| 3     | half_life_scorer           | gomlx_inference     |
| 4     | fact_half_life             | governor            |
| 5     | parallel_diff              | tool + agent        |
| 6     | classify_drift             | agent               |
| 7     | show_your_work             | governor            |
| 8     | conviction_tax             | governor            |
| 9     | classify_disposition       | agent               |
| 10    | approval_policy            | governor            |
| 11    | branch_action              | conditional         |
| 12    | doc_rewriter               | agent               |
| 13    | show_your_work             | governor            |
| 14    | open_pr                    | tool                |
| 15    | expire_article             | knowledge           |
| 16    | backfill_open_questions    | knowledge           |
| 17    | mark_provisional           | knowledge           |
| 18    | escalate_to_owner          | tool                |
| 19    | record_no_action           | knowledge           |
| 20    | write_provenance           | knowledge           |
| 21    | half_life_calibrator       | gomlx_inference     |
| 22    | notify_kb_owners           | tool                |

## Outputs

- per-article disposition: refreshed / expired / provisional / escalated
- auto-PRs with evidence chains
- tombstoned-article rows in `intentional-non-features-kb`
- self-tuning half-life rates per article class

## Pairs naturally with

- `half-life-kb` (knowledge) — receives the trust-decay metadata
- `fact-half-life` (governor) — Phase 1 enforcement
- `provenance-graph` (knowledge) — Phase 5 archive
- `intentional-non-features-kb` (knowledge) — Phase 4 tombstone target
- `open-questions-kb` (knowledge) — Phase 4 unresolved-drift target
- `kb-sync` (workflow) — sister workflow; this is the periodic sweep
  while `kb-sync` is the post-merge push
- `anti-cargo-cult` (workflow) — same shape applied to rules instead of docs

## Why it's a good demo

Three reasons:

1. **It treats documentation as a decaying physical asset.** Most KB
   tools are read-mostly storage. Railyard treats each fact as having
   a half-life, applies a `fact-half-life` governor uniformly, and
   *acts* on the decay — refresh, tombstone, or warn. The demo is
   that documentation in this system *cannot* silently rot.

2. **It eats Railyard's own dogfood.** Railyard's own KB has 138
   articles and 78 gap files (per project CLAUDE.md). This workflow
   is the thing that runs against it. Showing the workflow refreshing
   Railyard's own docs in front of customers is a credibility move
   no slide can match.

3. **It writes value even when it deletes.** The
   `intentional-non-features-kb` write at step 15 makes deletion
   informative — "we used to claim X, here's why we don't anymore" —
   which prevents the next person from re-litigating it. Tombstones
   are knowledge too.
