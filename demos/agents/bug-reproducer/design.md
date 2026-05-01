# Agent · `bug-reproducer`

Takes a bug report (often vague), produces a minimal reproducer:
exact steps, environment, expected vs actual.

## Purpose

The "did you try turning it off and on again" agent. Used in
`incident-response` workflow and as a tool for `support-agent` when a
ticket needs engineering eyes. Pairs with `test-case-writer` to convert
the reproducer into a regression test.

## DSPy signature

```python
class ReproduceBug(dspy.Signature):
    report: str = dspy.InputField(desc="raw bug report or ticket text")
    product_context: str = dspy.InputField(
        desc="versions, supported configs")
    repro_steps: list[str] = dspy.OutputField()
    environment: dict = dspy.OutputField(
        desc="OS, version, browser, runtime")
    expected: str = dspy.OutputField()
    actual: str = dspy.OutputField()
    confidence: float = dspy.OutputField()
    needs_user_input: list[str] = dspy.OutputField(
        desc="missing facts to confirm reproduction")
```

## Recommended tools

- `vector-search` — find similar past bugs and their reproducers
- `shell-exec` — attempt to run the reproducer in a sandbox
- `git-ops` — bisect across commits if reproducer narrows the regression

## Recommended governors

- `tool-allowlist` — restrict shell to a sandbox image
- `confidence-threshold` — low confidence returns `needs_user_input`
- `loop-breaker` — same shell command 3x = stop and ask

## Demonstrations sketch

- "It crashes sometimes" → produces `needs_user_input`, asks for stack trace
- "API returns 500 on POST /foo" → minimal curl, asserted-vs-actual
- "Mobile-only layout bug" → device matrix, screenshots needed

## Why it's a good demo

The agent's most valuable behavior is asking for missing facts rather
than guessing. `needs_user_input` is the structured output that
prevents the typical "agent invents a reproducer" failure mode.
