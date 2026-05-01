# Agent · `test-case-writer`

Takes a function or feature description and emits test cases:
positive, negative, edge.

## Purpose

A developer-productivity agent and a building block for `pr-review`.
Pairs with `bug-reproducer` (which it can be primed by) and feeds
`test-run` (tool) for self-verification.

## DSPy signature

```python
class WriteTests(dspy.Signature):
    target: str = dspy.InputField(desc="function source or feature spec")
    framework: Literal["pytest", "jest", "go-test", "rspec"] = dspy.InputField()
    style_guide: str = dspy.InputField(desc="naming, fixtures, assertions")
    cases: list[TestCase] = dspy.OutputField()
    coverage_estimate: float = dspy.OutputField()
```

`TestCase = {name, kind[positive|negative|edge|property], code,
expected_outcome, justification}`.

## Recommended tools

- `code-format` — ensure produced code matches house style
- `lint-run` — catch obvious issues before returning
- `test-run` — actually execute the produced tests

## Recommended governors

- `schema-validator` — every test must have a `justification`
- `output-length-cap` — prefer 5 sharp tests over 50 dull ones
- `tool-allowlist` — restrict to read/format/lint, not arbitrary shell

## Demonstrations sketch

- A small pure function → 3 positive, 2 negative, 1 edge case
- An API handler → cases include auth-failure, rate-limit, malformed-body
- A data transform → property-based tests with invariant assertions

## Why it's a good demo

Forcing `justification` on every test surfaces the problem nobody
talks about: most LLM-written tests look fine but assert the wrong
invariant. Pairs naturally with `cargo-cult-detector` (tool) to find
existing tests with no justification.
