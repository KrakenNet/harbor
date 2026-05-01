=============================================================================
                          SUPPORT TICKET TRIAGE
=============================================================================

[Inbound Channels] (Email, Web Form, Slack /ticket, Zendesk webhook)
             │
             ▼
[1. classify_intent]  (agent: `classifier`)
  → intent: bug | how-to | feature-request | billing | escalation | spam
             │
             ├──► [IF spam] ──► [Discard + audit]
             │
             ▼
[2. extract_entities]  (agent: `extractor`)
  → fields: customer_id, product_area, severity_self_reported, env, attachments
             │
             ▼
[3. retrieve_context]  (tool: `vector-search` over support-kb + past tickets)
             │
             ▼
[4. score_priority]  (governor: `compliance-scan` + agent: heuristic scorer)
  → priority: P1 | P2 | P3 | P4
             │
             ├──► [IF P1] ──► [Page on-call + open Slack channel]
             │
             ▼
[5. assign_owner]  (rule: round-robin within product_area, skip OOO)
             │
             ▼
[6. draft_reply]  (agent: `support-agent`)
  → suggested_reply, with citations into KB
             │
             ▼
[7. governor: `pii-redactor`]
  (redact PII from the draft before storing or sending)
             │
             ▼
[8. governor: `tone-calibrator`]
  (reject draft if tone wrong for channel: formal for enterprise,
   casual for self-serve; loops back to step 6 with feedback)
             │
             ▼
[9. HITL Gate]  (P1/P2 require human approval before send; P3/P4 auto-send)
             │
             ▼
[10. send_reply]  (tool: `email-send` / `slack-post` / Zendesk API)
             │
             ▼
[11. write_outcome]  (memory: `past-decision-memory` — ticket → resolution → CSAT)
=============================================================================

## Inputs

- ticket payload (email body, sender, attachments, channel metadata)

## Step types

| #  | Step                | Type        | Notes |
|----|---------------------|-------------|-------|
| 1  | classify_intent     | agent       | small classifier model OK |
| 2  | extract_entities    | agent       | structured-output mode |
| 3  | retrieve_context    | tool        | RAG over `customer-faq-kb` + ticket history |
| 4  | score_priority      | governor + agent | priority arithmetic + compliance flags |
| 5  | assign_owner        | rule        | deterministic, no LLM |
| 6  | draft_reply         | agent       | `support-agent` with retrieved citations |
| 7  | redact              | governor    | `pii-redactor` |
| 8  | tone_check          | governor    | `tone-calibrator`, can loop to step 6 |
| 9  | hitl                | approval    | conditional on priority |
| 10 | send_reply          | tool        | channel-specific |
| 11 | write_outcome       | memory      | feeds back into retrieval for next time |

## Outputs

- assigned ticket with priority, owner, draft reply, sent reply (if auto), outcome record

## Why it's a good demo

The most common B2B workflow customers will recognize. Touches every
Railyard primitive once: agents (classifier, extractor, support), tools
(vector-search, email-send), governors (pii-redactor, tone-calibrator,
compliance-scan), HITL gating, memory writeback. A natural anchor demo for
sales conversations and a complete onboarding tutorial.
