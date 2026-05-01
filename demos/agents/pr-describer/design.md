# Agent · `pr-describer`

Takes a diff and produces a PR title, summary, and test plan in the
team's house style.

## Purpose

The other half of `code-reviewer`. Used in `pr-review` workflow and as
a pre-commit helper. Pairs with `changelog-writer` to keep the
release-notes pipeline in sync.

## DSPy signature

```python
class DescribePR(dspy.Signature):
    diff: str = dspy.InputField()
    commits: list[str] = dspy.InputField(desc="commit messages on the branch")
    style_guide: str = dspy.InputField(desc="house conventions")
    title: str = dspy.OutputField(desc="≤72 chars, conventional-commit style")
    summary: list[str] = dspy.OutputField(desc="1–3 bullets")
    test_plan: list[str] = dspy.OutputField()
    risk: Literal["low", "medium", "high"] = dspy.OutputField()
```

## Recommended tools

- `git-ops` — pull blame and prior PR descriptions for style matching
- `vector-search` — retrieve similar past PRs for tone reference

## Recommended governors

- `output-length-cap` — keep titles ≤72, summaries terse
- `schema-validator` — required fields present, bullets non-empty
- `tone-calibrator` — match team's PR-description voice

## Demonstrations sketch

- Small fix → one-line title, one-bullet summary, one-line test plan
- Multi-commit feature branch → multi-bullet summary, test plan with
  manual + automated entries
- Refactor with no behavior change → risk=low, explicit "no test plan
  needed" justification

## Why it's a good demo

It's a useful local-developer agent and a great surface for showing
optimized demonstrations: feed it the team's last 50 PRs and the tone
matches, no prompt engineering required.
