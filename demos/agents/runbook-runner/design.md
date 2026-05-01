# Agent · `runbook-runner`

Takes a runbook and a triggering condition, executes the runbook step
by step, with HITL checkpoints on irreversible verbs.

## Purpose

The on-call companion. Used in `incident-response` workflow and as the
"please follow this checklist" agent for routine ops tasks. Pairs with
`runbooks-kb` (knowledge) and any HITL governor.

## DSPy signature

```python
class RunRunbook(dspy.Signature):
    runbook: str = dspy.InputField(desc="markdown runbook with steps")
    trigger: str = dspy.InputField(desc="what fired this run")
    current_state: dict = dspy.InputField(desc="snapshot from monitors")
    next_action: Action = dspy.OutputField()
    completed_steps: list[str] = dspy.OutputField()
    blockers: list[str] = dspy.OutputField()
    needs_human: bool = dspy.OutputField()
```

`Action = {step_name, kind[read|write|notify|wait], command,
expected_outcome}`.

## Recommended tools

- `shell-exec` — execute commands listed in the runbook
- `http-fetch` — call APIs the runbook references
- `slack-post` — notify channels per runbook
- `vector-search` — pull prior runs of this runbook for context

## Recommended governors

- `hitl-trigger` — every `write` action requires human approval
- `tool-allowlist` — runbook can only use tools it explicitly names
- `loop-breaker` — same step 3x without progress = halt
- `business-hours-only` — non-paging runbooks defer to morning

## Demonstrations sketch

- "Disk full on host X" runbook → reads, prunes, notifies, with HITL
  before deletion
- "Failed deploy rollback" runbook → reads state, proposes rollback,
  waits for human, then executes
- "Customer-data export request" runbook → multi-step with two human
  approvals

## Why it's a good demo

Runbook execution is the cleanest place to show the full governor
stack: HITL on writes, allowlist on tools, loop-breaker on retries.
Each guardrail maps to a real pager-duty horror story; the agent's
boring, predictable execution is the entire point.
