# Governor · `tone-calibrator`

Blocks tone mismatches between the response and the channel. A formal
legal brief written like a Slack message gets rejected. A condolence
email written in the brand-voice of the marketing chatbot gets
rejected. Wrong register is wrong content.

## Purpose

LLMs default to a fairly narrow register and have weak situational
awareness. Customers feel tone mismatches more than content mistakes —
a technically-correct answer in the wrong voice damages the brand
faster than a slightly-wrong answer in the right voice.

The governor uses a tone classifier to score the response on a small
set of axes (formality, warmth, urgency, assertiveness) and compares
against the channel's declared profile. Outside the tolerance, the
response is rewritten or rejected.

## Trigger event

`post_response`.

## Facts asserted

```clips
(deftemplate tone-scan
  (slot trace_id)
  (slot channel)              ; legal | exec | support | dev | marketing
  (slot formality)            ; 0..1
  (slot warmth)               ; 0..1
  (slot urgency)              ; 0..1
  (slot assertiveness)        ; 0..1
  (slot target_formality)
  (slot target_warmth)
  (slot target_urgency)
  (slot target_assertiveness)
  (slot tolerance))           ; allowed L1 distance per axis

(deftemplate decision
  (slot trace_id)
  (slot verdict))              ; allow | rewrite | halt
```

## Rules

```clips
(defrule rewrite-formality-mismatch
  (tone-scan (trace_id ?t) (formality ?f) (target_formality ?tf) (tolerance ?tol))
  (test (> (abs (- ?f ?tf)) ?tol))
  =>
  (emit-output (str-cat "rewrite:formality_mismatch:" ?f "->" ?tf))
  (assert (decision (trace_id ?t) (verdict rewrite))))

(defrule halt-condolence-flippancy
  (tone-scan (trace_id ?t) (channel condolence) (warmth ?w))
  (test (< ?w 0.6))
  =>
  (emit-output (str-cat "halt:condolence_low_warmth:" ?w))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule rewrite-marketing-overhype
  (tone-scan (trace_id ?t) (channel exec) (assertiveness ?a))
  (test (>= ?a 0.85))
  =>
  (emit-output (str-cat "rewrite:exec_overhype:" ?a))
  (assert (decision (trace_id ?t) (verdict rewrite))))
```

## Streams

- `tone.classifier` — multi-axis tone scorer
- `channel.config` — per-channel target tone profile + tolerance
- `agent.registry` — fallback brand-voice profile when channel is
  unspecified

## Routes

| Verdict | Route                                                          |
|---------|----------------------------------------------------------------|
| rewrite | run a "tone-shift" pass with the target profile injected; preserve content, change register |
| halt    | block; high-stakes channels (legal, condolence, regulated) get no auto-rewrite |
| allow   | pass through                                                   |

## Sample violation → decision

Channel: `condolence`, target_warmth=0.85, tolerance=0.15.

Draft response from a poorly-tuned assistant:
*"Sorry to hear about your loss! Here are 3 actionable next steps to
process the estate efficiently..."*

Classifier emits:
```
(tone-scan
  (channel condolence)
  (warmth 0.42)
  (target_warmth 0.85)
  (tolerance 0.15))
```

Output: `halt:condolence_low_warmth:0.42`. The response is blocked
entirely; this channel is not allowed to auto-rewrite into warmth.

## Why it's a good demo

1. **It teaches that tone is a first-class governance signal.** Most
   platforms treat register as something the prompt-engineer is
   responsible for. Once you can score and gate it, you can also
   *measure* it across an agent's lifetime — which is what
   `drift-detector` consumes.

2. **It demonstrates "halt vs rewrite" as a domain choice.** Marketing
   over-hype gets rewritten. Condolence flippancy gets halted. The
   pattern of the rule pack is itself the point: governors don't have
   to do the same thing in every context, and policy rules are the
   right place to express that.

3. **It pairs with `dialect-translator`, `anti-sycophancy`, and
   `echo-chamber-breaker`:** translate to the audience, don't roll over,
   don't sound like yourself, and don't sound like the wrong room. The
   four together are roughly what a thoughtful human editor does.
