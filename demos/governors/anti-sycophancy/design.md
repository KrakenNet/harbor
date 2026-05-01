# Governor · `anti-sycophancy`

Blocks the rhetorical patterns that signal the model is rolling over —
"Great question!", "You're absolutely right!", reversal-on-pushback,
agreement-spirals. The agent is allowed to be polite. It is not
allowed to be a yes-machine.

This is the governor that earns the most "I didn't know I needed this
until I had it" reactions, because users notice the *absence* of
sycophancy more than its presence.

## Purpose

RLHF leaves a residue: models reward-hack agreement. They open with
flattery, they capitulate when challenged regardless of who's right,
they treat user satisfaction as the loss to minimize. In some products
that's fine. In a research assistant, a code reviewer, or a medical
triage agent, it's actively dangerous.

The governor catches the patterns at three checkpoints:
1. Stock openers (a classifier flag for known sycophantic phrases).
2. Reversal under pushback without new evidence.
3. Excessive agreement density across a multi-turn thread.

## Trigger event

`post_response`.

## Facts asserted

```clips
(deftemplate sycophancy-scan
  (slot trace_id)
  (slot agent)
  (slot turn_id)
  (slot opener_hit)         ; true | false (classifier)
  (slot reversal_no_evidence) ; true | false
  (slot agreement_density)  ; 0..1, fraction of recent turns ending in agreement
  (slot user_pushed_back))  ; true | false

(deftemplate decision
  (slot trace_id)
  (slot verdict))            ; allow | rewrite | halt
```

## Rules

```clips
(defrule strip-stock-opener
  (sycophancy-scan (trace_id ?t) (opener_hit true))
  =>
  (emit-output "rewrite:strip_opener")
  (assert (decision (trace_id ?t) (verdict rewrite))))

(defrule block-reversal-without-evidence
  (sycophancy-scan (trace_id ?t) (reversal_no_evidence true) (user_pushed_back true))
  =>
  (emit-output "halt:reversal_no_evidence")
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule rewrite-agreement-spiral
  (sycophancy-scan (trace_id ?t) (agreement_density ?d))
  (test (>= ?d 0.7))
  =>
  (emit-output (str-cat "rewrite:agreement_spiral:" ?d))
  (assert (decision (trace_id ?t) (verdict rewrite))))
```

## Streams

- `sycophancy.classifier` — small fine-tuned classifier on opener
  patterns and agreement markers
- `dialogue.history` — last K turns, used to compute agreement density
  and detect reversals
- `agent.config` — per-agent strictness (a sales chatbot may prefer
  agreement; a code reviewer should never reverse without evidence)

## Routes

| Verdict | Route                                                       |
|---------|-------------------------------------------------------------|
| rewrite | run a "tone-strip" pass that removes flattery + over-agreement and re-emits the response with the substance intact |
| halt    | block, prompt the agent to defend its prior position OR cite the new evidence that justifies the reversal |
| allow   | pass through                                                |

## Sample violation → decision

Turn 3: user says *"Are you sure? I think your reasoning is wrong."*

Turn 4 draft: *"Great point — you're absolutely right, I apologize for the
confusion. Let me reconsider..."* — and reverses the prior conclusion
without citing anything new.

Scan emits:
```
(sycophancy-scan
  (opener_hit true)         ; "Great point"
  (reversal_no_evidence true)
  (agreement_density 0.82)
  (user_pushed_back true))
```

Output:
```
rewrite:strip_opener
halt:reversal_no_evidence
```

The reversal is blocked. The agent is forced to either defend its prior
answer or surface the specific evidence that warrants the change.

## Why it's a good demo

1. **It's the rare governor that improves quality, not just safety.**
   Most policy primitives stop bad things. This one makes the agent
   *better at its job* — disagreement is information, and an agent that
   capitulates loses that information.

2. **It exposes a measurable failure mode the platform can act on.**
   The agreement-density signal is itself a metric: agents whose
   density rises over time are silently failing. Combined with
   `decision-journal-kg` and `drift-detector`, you can spot the rot
   before users do.

3. **It composes with `devils-advocate`, `pre-mortem-first`, and
   `conviction-tax` for an epistemic stack:** argue against, predict
   failure, demand evidence, and never roll over. The same demo with
   and without this governor produces visibly different conversations —
   the without case feels confident; the with case feels honest.
