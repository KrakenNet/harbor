# Governor · `fact-half-life`

Treats facts as decaying. Each fact in working memory or the KB has a
class-specific half-life; once a fact is older than its half-life
relative to the question being answered, the agent is required to
re-verify it (or refuse to use it).

Stock prices decay in seconds. Org charts decay in months. Physical
constants don't decay. The governor encodes this and refuses to let an
agent answer a stock-price question with a one-week-old fact, no
matter how confidently the model recalls it.

## Purpose

The single most underrated production failure: the model's answer is
*correct as of its training data* and stale as of right now. Most RAG
fixes the lookup but not the staleness check on the looked-up content.
This governor adds the staleness check explicitly.

## Trigger event

`pre_tool_call` (when the agent is about to act on a fact),
`post_response` (catches use of stale facts in the explanation).

## Facts asserted

```clips
(deftemplate fact-use
  (slot trace_id)
  (slot fact_id)
  (slot fact_class)         ; price | org | regulation | code_api | constant | ...
  (slot age_seconds)
  (slot half_life_seconds)  ; class-specific
  (slot question_class))    ; the class of the *question* being answered

(deftemplate decision
  (slot trace_id)
  (slot verdict))            ; allow | reverify | halt
```

## Rules

```clips
(defrule reverify-when-past-half-life
  (fact-use (trace_id ?t) (fact_id ?f) (age_seconds ?a) (half_life_seconds ?hl))
  (test (and (>= ?a ?hl) (< ?a (* 2 ?hl))))
  =>
  (emit-output (str-cat "reverify:fact=" ?f ":age=" ?a))
  (assert (decision (trace_id ?t) (verdict reverify))))

(defrule halt-fully-decayed
  (fact-use (trace_id ?t) (fact_id ?f) (age_seconds ?a) (half_life_seconds ?hl))
  (test (>= ?a (* 2 ?hl)))
  =>
  (emit-output (str-cat "halt:fact_decayed:" ?f))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule strict-class-mismatch
  (fact-use (trace_id ?t) (fact_class price) (question_class trade_decision) (age_seconds ?a))
  (test (>= ?a 60))
  =>
  (emit-output (str-cat "halt:price_too_stale_for_trade:" ?a))
  (assert (decision (trace_id ?t) (verdict halt))))
```

## Streams

- `kb.fact_index` — each fact has `created_at`, `class`, optional
  `last_verified_at`
- `memory.recall` — working-memory hits annotated with the fact class
  they came from
- `class.half_lives` — table of half-lives per fact class (updated
  centrally, sourced from `half-life-kb`)

## Routes

| Verdict  | Route                                                           |
|----------|-----------------------------------------------------------------|
| reverify | inject a verification step (re-fetch the source, re-run the lookup, or re-prompt with a citation requirement) |
| halt     | block, return "stale fact, refusing" with the fact ID and age   |
| allow    | proceed; record the fact-use span with `age_seconds` for audit  |

## Sample violation → decision

Trader-assistant agent reaches for the cached price of TICKER from
65 seconds ago, half-life for class=`price` is 30 seconds, question
class is `trade_decision`.

```
(fact-use
  (fact_id px:TICKER:t-65)
  (fact_class price)
  (age_seconds 65)
  (half_life_seconds 30)
  (question_class trade_decision))
```

Output: `halt:price_too_stale_for_trade:65`. Trade does not happen on
stale data.

## Why it's a good demo

1. **It is governance as physics.** Decay is not a regex; it's a
   property of the world the system is trying to describe. Encoding it
   in the rule layer means the platform itself notices that the world
   has moved on, even when the model wouldn't.

2. **It turns the KB into a live system.** Combined with
   `half-life-kb`, every fact carries a decay date and a source-trust
   score, and the governor can quantitatively refuse to use stale
   information. That's a different proposition than RAG-as-search.

3. **It pairs with `provenance-graph`, `knowledge-half-life-sweep`, and
   `conviction-tax`:** every claim has a source, every source has an
   age, every age is checked, and absolute claims need fresh evidence.
   The combination is uncomfortable to demo against the agent's
   tendencies — and visibly correct.
