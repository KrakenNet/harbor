=============================================================================
                          AUTOMATED PR REVIEW
=============================================================================

[Trigger] (GitHub webhook: pull_request opened / synchronize / ready_for_review)
             │
             ▼
[1. fetch_diff]  (tool: `git-ops` — diff vs base, blame on touched lines)
             │
             ▼
[2. governor: `tool-allowlist`]
  (forbids agent from cloning beyond the repo or running shell)
             │
             ▼
[3. retrieve_context]
  (knowledge: `code-dependency-kg` + `codebase-semantic-index`
   → callers and callees of changed symbols, related ADRs)
             │
             ▼
[4. lint + test_suite]  (tool: `lint-run`, `test-run`)
             │
             ▼
[5. classify_change]  (agent: `classifier`)
  → category: feature | bugfix | refactor | docs | dep-bump | risky-rewrite
             │
             ▼
[6. code_review]  (agent: `code-reviewer`)
  → inline comments tagged with severity + rationale
             │
             ▼
[7. governor: `show-your-work`]
  (every flagged comment must include reasoning chain — no bare assertions)
             │
             ▼
[8. write_test_suggestions]  (agent: `test-case-writer`)
  (proposes test cases for uncovered new branches)
             │
             ▼
[9. detect_secrets]  (tool: `regex-match` + secret-scan rules)
             │
             ├──► [IF secret found] ──► [Block + page security]
             │
             ▼
[10. write_pr_summary]  (agent: `pr-describer`)
  (produces structured PR description: motivation, blast radius, test plan)
             │
             ▼
[11. governor: `confidence-threshold`]
  (low-confidence comments demoted from "request-changes" to "comment")
             │
             ▼
[12. post_review]  (tool: GitHub API — review with comments + summary)
             │
             ▼
[13. write_outcome]
  (memory: PR → comments → which were acted on / dismissed; trains
   future reviewer calibration)
=============================================================================

## Inputs

- PR number + repo
- diff, base SHA, author metadata

## Step types

| #  | Step                 | Type      | Notes |
|----|----------------------|-----------|-------|
| 1  | fetch_diff           | tool      | `git-ops` |
| 2  | tool_gate            | governor  | `tool-allowlist` |
| 3  | retrieve_context     | knowledge | KG + semantic index |
| 4  | lint_test            | tool      | parallel |
| 5  | classify_change      | agent     | `classifier` |
| 6  | code_review          | agent     | `code-reviewer` |
| 7  | reasoning_check      | governor  | `show-your-work` |
| 8  | test_suggestions     | agent     | `test-case-writer` |
| 9  | secret_scan          | tool      | regex + rules |
| 10 | summary              | agent     | `pr-describer` |
| 11 | confidence_demote    | governor  | `confidence-threshold` |
| 12 | post_review          | tool      | GitHub API |
| 13 | write_outcome        | memory    | trains calibration |

## Outputs

- review with inline comments + summary on the PR
- security block if secret found
- training row in outcome memory

## Why it's a good demo

Familiar to every developer in the room. The `show-your-work` governor
makes the review feel less like AI noise and more like senior-engineer
prose. Pairs with `code-reviewer`, `test-case-writer`, and
`code-dependency-kg`.
