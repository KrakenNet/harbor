# Governor · `approval-policy`

Decides *which* humans must approve a paused action, and how many. Sister
to `hitl-trigger` — that one decides whether to pause; this one routes
the approval card.

## Purpose

Different actions need different approvers. A $500 refund: any support
lead. A $50,000 refund: support lead AND finance VP. Production deploy:
on-call SRE AND eng manager. The matrix lives here.

## Trigger event

`on_pause` — fires after `hitl-trigger` (or any other governor) has
paused the run.

## Facts asserted

```clips
(deftemplate approval-needed
  (slot trace_id)
  (slot action)
  (slot dollar_amount)
  (slot risk_class)
  (slot tenant_policy))   ; named matrix

(deftemplate approver-set
  (slot trace_id)
  (multislot roles)
  (slot quorum))
```

## Rules

```clips
(defrule single-approver-low
  (approval-needed (trace_id ?t) (risk_class low))
  =>
  (emit-output "approver:any_lead:quorum=1")
  (assert (approver-set (trace_id ?t) (roles support_lead) (quorum 1))))

(defrule dual-approver-financial
  (approval-needed (trace_id ?t) (action ?a) (dollar_amount ?d))
  (test (and (>= ?d 10000) (member ?a (create$ refund transfer payout))))
  =>
  (emit-output (str-cat "approver:dual:finance_vp+support_lead:amount=" ?d))
  (assert (approver-set (trace_id ?t) (roles finance_vp support_lead) (quorum 2))))

(defrule sre-deploy
  (approval-needed (trace_id ?t) (action prod_deploy))
  =>
  (emit-output "approver:sre+eng_mgr:quorum=2")
  (assert (approver-set (trace_id ?t) (roles oncall_sre eng_mgr) (quorum 2))))
```

## Streams

- `tenant.config` — named approval matrices
- `directory` — current role assignments
- `approval.inbox` — destination

## Routes

| Verdict (effective)         | Route                                                   |
|-----------------------------|---------------------------------------------------------|
| approver-set asserted       | post card to all listed roles, require `quorum` votes   |

## Sample violation → decision

Paused action: `refund`, amount=$15,000. Output:
`approver:dual:finance_vp+support_lead:amount=15000`. Two cards posted;
both must approve before resume.

## Why it's a good demo

Shows that governors don't always halt or allow — they can *enrich*. The
output here is data the platform consumes (an approver set), not a
yes/no. Pairs with `hitl-trigger` and `role-gate`.
