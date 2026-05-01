# Governor · `schema-validator`

Asserts that structured outputs (JSON, typed records) conform to a
declared schema before they leave the agent. Re-prompts the agent if not.

## Purpose

LLMs lie about their JSON. This governor closes the loop: structured
output gets validated, and a non-conforming response is rejected with the
specific error fed back into the next attempt.

## Trigger event

`post_response` for any agent declared with an `output_schema`.

## Facts asserted

```clips
(deftemplate schema-check
  (slot trace_id)
  (slot agent)
  (slot ok)               ; true | false
  (slot error_kind)       ; missing_field | wrong_type | extra_field | parse_error
  (slot field)
  (slot retries))
```

## Rules

```clips
(defrule allow-when-valid
  (schema-check (trace_id ?t) (ok true))
  =>
  (emit-output "allow:schema_ok")
  (assert (decision (trace_id ?t) (verdict allow))))

(defrule reprompt-on-failure
  (schema-check (trace_id ?t) (ok false) (error_kind ?e) (field ?f) (retries ?n))
  (test (< ?n 3))
  =>
  (emit-output (str-cat "reprompt:schema:" ?e ":" ?f))
  (assert (decision (trace_id ?t) (verdict reprompt))))

(defrule halt-after-max-retries
  (schema-check (trace_id ?t) (ok false) (retries ?n))
  (test (>= ?n 3))
  =>
  (emit-output "halt:schema_max_retries")
  (assert (decision (trace_id ?t) (verdict halt))))
```

## Streams

- `agent.registry` — sources `output_schema` per agent
- `validator.results` — JSON Schema / pydantic / DSPy signature check results

## Routes

| Verdict   | Route                                                        |
|-----------|--------------------------------------------------------------|
| allow     | pass response downstream                                     |
| reprompt  | inject error back into agent for retry                       |
| halt      | abort, return schema-failure envelope to caller              |

## Sample violation → decision

Agent `extractor` returns `{"name": "Alice"}` against a schema requiring
`name` and `age`. Output: `reprompt:schema:missing_field:age`. Agent
re-runs with the missing-field hint and succeeds on the second attempt.

## Why it's a good demo

Shows a governor that *steers* the agent rather than just gate-keeping.
A clean entry point for the broader story that governors can be
generative — they can reshape the next step instead of only saying
yes/no.
