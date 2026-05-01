# Governor · `output-length-cap`

Caps response length in tokens or characters. Truncates, summarizes, or
re-prompts depending on policy.

## Purpose

Some channels can't take a 4000-token response (SMS, push notifications,
voice IVR). Some humans don't want one (chat). This governor enforces
the channel limit, neutrally.

## Trigger event

`post_response`.

## Facts asserted

```clips
(deftemplate length-check
  (slot trace_id)
  (slot channel)
  (slot length_tokens)
  (slot limit_tokens)
  (slot policy))          ; truncate | summarize | reprompt
```

## Rules

```clips
(defrule truncate-when-over
  (length-check (trace_id ?t) (length_tokens ?l) (limit_tokens ?lim) (policy truncate))
  (test (> ?l ?lim))
  =>
  (emit-output (str-cat "truncate:" ?l "->" ?lim))
  (assert (decision (trace_id ?t) (verdict truncate))))

(defrule summarize-when-over
  (length-check (trace_id ?t) (length_tokens ?l) (limit_tokens ?lim) (policy summarize))
  (test (> ?l ?lim))
  =>
  (emit-output "summarize:over_limit")
  (assert (decision (trace_id ?t) (verdict summarize))))

(defrule reprompt-when-over
  (length-check (trace_id ?t) (length_tokens ?l) (limit_tokens ?lim) (policy reprompt))
  (test (> ?l ?lim))
  =>
  (emit-output "reprompt:shorter_response")
  (assert (decision (trace_id ?t) (verdict reprompt))))
```

## Streams

- `channel.config` — per-channel length limits and policy
- `tokens.usage` — response length

## Routes

| Verdict   | Route                                                |
|-----------|------------------------------------------------------|
| truncate  | hard cut at limit, append "[truncated]"              |
| summarize | run summarizer agent over response, return summary   |
| reprompt  | re-run agent with explicit "respond in N tokens"     |

## Sample violation → decision

SMS channel, response 412 tokens against 160 limit, policy=`summarize`.
Output: `summarize:over_limit`. The response is replaced with a summary
that fits.

## Why it's a good demo

A small, useful, and easy-to-explain governor. Shows three different
"repair" routes for the same condition — drives home the point that
governors are policy, not just safety.
