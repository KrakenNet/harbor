# Agent · `code-reviewer`

Reviews a diff and returns categorized comments — bugs, style, design,
security — with file/line anchors and severity.

## Purpose

The PR-companion agent. Used in `pr-review` workflows, pre-commit hooks,
and ad-hoc developer requests ("review my branch"). Pairs with
`pr-describer` so the same diff produces both a description and a
review.

## DSPy signature

```python
class ReviewCode(dspy.Signature):
    diff: str = dspy.InputField(desc="unified diff")
    repo_context: str = dspy.InputField(
        desc="conventions, languages, prior style notes")
    comments: list[Comment] = dspy.OutputField()
    summary: str = dspy.OutputField(desc="overall verdict, 1–3 sentences")
    blocking: bool = dspy.OutputField()
```

`Comment = {file, line, category[bug|style|design|security|perf],
severity[1..5], message, suggested_fix}`.

## Recommended tools

- `git-ops` — fetch surrounding context (blame, prior commits)
- `lint-run` — surface lint findings before the LLM reads the diff
- `test-run` — confirm the diff doesn't break existing tests
- `vector-search` — retrieve project conventions from the codebase KB

## Recommended governors

- `tool-allowlist` — restrict to read-only git/lint
- `output-length-cap` — reviewers that comment on every line are noise
- `confidence-threshold` — abstain on bug claims with low confidence

## Demonstrations sketch

- A small refactor PR → mostly style + one design suggestion
- A security-sensitive diff (auth path) → blocking, with severity-5 finding
- A test-only PR → mostly praise, optional nits

## Why it's a good demo

Pairs naturally with the trace UI: every comment links back to the
exact tool calls that produced it, so a developer can ask "where did
that lint finding come from" and get a span answer.
