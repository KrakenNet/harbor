# Governor · `tool-allowlist`

Restricts an agent to a declared set of tools. Any attempt to invoke a
tool outside the allowlist is halted before the call reaches the
executor.

## Purpose

Defense-in-depth against prompt injection that tells the agent to call a
tool it shouldn't. Even if the LLM is convinced, the governor isn't.

## Trigger event

`pre_tool_call`.

## Facts asserted

```clips
(deftemplate tool-call
  (slot trace_id)
  (slot agent)
  (slot tool)
  (slot allowed))         ; true | false, derived from agent.config
```

## Rules

```clips
(defrule block-disallowed-tool
  (tool-call (trace_id ?t) (agent ?a) (tool ?tool) (allowed false))
  =>
  (emit-output (str-cat "halt:tool_not_allowed:agent=" ?a ":tool=" ?tool))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule allow-listed
  (tool-call (trace_id ?t) (allowed true))
  =>
  (emit-output "allow:tool_ok")
  (assert (decision (trace_id ?t) (verdict allow))))
```

## Streams

- `agent.registry` — sources each agent's allowlist
- `tool.registry` — canonical tool list

## Routes

| Verdict | Route                                                |
|---------|------------------------------------------------------|
| halt    | abort, log security event, increment per-agent counter |
| allow   | pass through                                         |

## Sample violation → decision

Agent `summarizer` (allowlist: `[search, fetch_url]`) attempts to call
`shell-exec`. Output:
`halt:tool_not_allowed:agent=summarizer:tool=shell-exec`.

## Why it's a good demo

The "you didn't think you needed this until you did" governor. The first
prompt-injection incident every customer experiences is what sells them
on the rest of the catalog.
