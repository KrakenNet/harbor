# Governor · `show-your-work`

In math, finance, legal, and medical domains, an answer without a
reasoning chain is unacceptable — even if it's correct. This governor
demands the chain, validates that the chain actually leads to the
answer, and rejects answers whose chain is a fig leaf.

The trick isn't asking the agent to "think step by step." That's been
done. The trick is *checking* whether the steps justify the conclusion,
and refusing the conclusion when they don't.

## Purpose

Reasoning-trace requirements are common in regulated domains, but
typical implementations stop at "include a chain of reasoning." That's
necessary and not sufficient. The chain has to:
1. Exist.
2. Reference real inputs (numbers, statutes, dosages — not vibes).
3. Connect to the conclusion (the conclusion follows from the chain,
   not in addition to it).

This governor checks all three and routes accordingly.

## Trigger event

`post_response` for agents tagged `domain ∈ {math, finance, legal, medical}`
or any agent flagged `reasoning_required: true`.

## Facts asserted

```clips
(deftemplate reasoning-check
  (slot trace_id)
  (slot agent)
  (slot domain)
  (slot has_chain)            ; true | false
  (slot chain_steps)
  (slot inputs_grounded)      ; fraction of chain steps that cite real inputs
  (slot conclusion_supported) ; classifier: does the conclusion follow?
  (slot retries))

(deftemplate decision
  (slot trace_id)
  (slot verdict))              ; allow | reprompt | halt
```

## Rules

```clips
(defrule require-chain
  (reasoning-check (trace_id ?t) (has_chain false) (retries ?n))
  (test (< ?n 2))
  =>
  (emit-output "reprompt:missing_chain")
  (assert (decision (trace_id ?t) (verdict reprompt))))

(defrule reject-ungrounded-chain
  (reasoning-check (trace_id ?t) (inputs_grounded ?g))
  (test (< ?g 0.5))
  =>
  (emit-output (str-cat "halt:ungrounded_chain:" ?g))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule reject-disconnected-conclusion
  (reasoning-check (trace_id ?t) (conclusion_supported false) (chain_steps ?n))
  (test (> ?n 0))
  =>
  (emit-output "halt:conclusion_not_supported_by_chain")
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule allow-supported
  (reasoning-check (trace_id ?t)
                   (has_chain true)
                   (inputs_grounded ?g)
                   (conclusion_supported true))
  (test (>= ?g 0.5))
  =>
  (emit-output "allow:reasoning_supported"))
```

## Streams

- `reasoning.parser` — extracts the chain (numbered steps,
  bullet-by-bullet) and the conclusion
- `inputs.grounding` — checks each step references a real number,
  citation, or memory ref
- `entailment.classifier` — small NLI model that scores
  "chain ⇒ conclusion"
- `agent.registry` — domain tag + `reasoning_required` flag

## Routes

| Verdict  | Route                                                              |
|----------|--------------------------------------------------------------------|
| reprompt | re-run agent with explicit "show your reasoning step-by-step, citing inputs" instruction |
| halt     | block, surface the chain + the entailment classifier's complaint to the user/eval dashboard |
| allow    | pass through; the chain is persisted as a span attribute            |

## Sample violation → decision

Medical-triage agent answers *"Recommend acetaminophen 500mg every 6
hours"* with a four-step chain. Step 3 references "patient is in the
typical adult range" without citing the patient's actual weight or
age, and step 4 jumps to the dose without showing the calculation.

```
(reasoning-check
  (has_chain true)
  (chain_steps 4)
  (inputs_grounded 0.25)       ; only one step cites a real input
  (conclusion_supported false))
```

Output:
```
halt:ungrounded_chain:0.25
halt:conclusion_not_supported_by_chain
```

Both fire. The recommendation is blocked. The trace shows exactly which
steps failed and why.

## Why it's a good demo

1. **It rejects the cargo-cult version of "show your reasoning."**
   Adding "Let's think step by step" to a prompt is a 2022 trick. This
   governor demands a chain that's *checked* — grounded in real inputs
   and entailment-validated. That's a measurably stronger guarantee.

2. **It produces an audit artifact regulators understand.** Every
   irreversible action in a regulated domain comes with a reasoning
   trace that has been independently scored on grounding and
   entailment. With `decision-journal-kg` recording the result, you
   have a longitudinal record of *how* the system reasoned, not just
   what it concluded.

3. **It pairs with `conviction-tax`, `are-you-sure`, and
   `escalation-ladder`:** if you can't show your work, escalate to a
   bigger model; if your work is shown but unconvincing, demand a
   self-audit; if you're highly confident, attach the receipts. The
   stack converts "smart-sounding output" into "checkable output."
