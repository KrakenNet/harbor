# Agent · `changelog-writer`

Takes a range of commits or merged PRs and produces a categorized
changelog entry: features, fixes, breaking changes.

## Purpose

The release-notes companion. Used in `weekly-roll-up` workflow and at
release tag time. Pairs with `pr-describer` (whose summaries are its
input) and `email-drafter` (which sends the changelog).

## DSPy signature

```python
class WriteChangelog(dspy.Signature):
    commits: list[Commit] = dspy.InputField()
    audience: Literal["customer", "internal", "developer"] = dspy.InputField()
    version: str = dspy.InputField()
    features: list[str] = dspy.OutputField()
    fixes: list[str] = dspy.OutputField()
    breaking: list[BreakingChange] = dspy.OutputField()
    upgrade_notes: str = dspy.OutputField()
```

`Commit = {sha, title, body, author, pr_number}`.
`BreakingChange = {summary, migration_path, affected_apis}`.

## Recommended tools

- `git-ops` — pull commits and tags
- `vector-search` — retrieve prior changelog entries for style

## Recommended governors

- `output-length-cap` — release notes balloon without limits
- `schema-validator` — every breaking change must have a migration path
- `tone-calibrator` — customer audience needs different voice than developer

## Demonstrations sketch

- Patch release → all fixes, no features, no breaking
- Minor release → features + fixes, customer-flavored
- Major release → breaking changes section dominates, with migration paths

## Why it's a good demo

Forcing every breaking change to carry a migration path (via
`schema-validator`) is the kind of "policy lives in the governor, not
the prompt" pattern Railyard makes natural.
