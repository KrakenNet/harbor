# Governor · `role-gate`

RBAC over verbs. Maps the calling principal's role to the set of tools
and workflows they're permitted to trigger.

## Purpose

Without this governor, an agent invoked by a low-privilege user can
inherit dangerous tools because the agent itself owns them. This rule
checks the *principal*, not just the agent.

## Trigger event

`pre_tool_call`, `pre_workflow_start`.

## Facts asserted

```clips
(deftemplate verb-attempt
  (slot trace_id)
  (slot principal)
  (slot role)             ; viewer | editor | admin | service
  (slot verb)             ; tool slug or workflow slug
  (slot required_role))   ; sourced from registry
```

## Rules

```clips
(defrule deny-insufficient-role
  (verb-attempt (trace_id ?t) (role ?r) (verb ?v) (required_role ?req))
  (test (not (role-meets ?r ?req)))
  =>
  (emit-output (str-cat "halt:rbac:role=" ?r ":needs=" ?req ":verb=" ?v))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule allow-sufficient-role
  (verb-attempt (trace_id ?t) (role ?r) (required_role ?req))
  (test (role-meets ?r ?req))
  =>
  (emit-output "allow:rbac_ok"))
```

## Streams

- `auth.principal` — role lookup from JWT claims
- `tool.registry` / `workflow.registry` — required-role per verb

## Routes

| Verdict | Route                                            |
|---------|--------------------------------------------------|
| halt    | 403 forbidden, audit event with principal + verb |
| allow   | proceed                                          |

## Sample violation → decision

Principal `bob@acme.com` (role=`viewer`) triggers an agent that calls
`apply_change` (required=`admin`). Output:
`halt:rbac:role=viewer:needs=admin:verb=apply_change`.

## Why it's a good demo

Auditors love to see RBAC enforced at the rule layer rather than scattered
across handler code. Composes with `hitl-trigger` for the case where
even an admin needs a second human.
