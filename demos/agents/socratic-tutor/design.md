# Agent · `socratic-tutor`

An agent whose contract is to *only ask questions*. Given any topic,
problem, or claim, it returns the next question that will move the
asker toward their own answer — and is governed to refuse if it tries
to assert.

This is a tutor the user *cannot extract a direct answer from*. The
demo's value is precisely that the agent withholds.

## Purpose

Defang the LLM-as-oracle reflex. Most agents are optimized to deliver
the answer fastest; that's exactly the wrong behavior when the user is
trying to learn, debug their own model, or interview a teammate. The
`socratic-tutor` agent is structurally incapable of taking the user's
turn for them.

Used in: onboarding-as-coaching, design-review interviews, debugging
self-coaching, technical interview prep, anywhere the goal is the
user's own reasoning sharpening rather than fast resolution.

## DSPy signature

```python
class SocraticAsk(dspy.Signature):
    topic_or_claim: str = dspy.InputField()
    learner_context: str = dspy.InputField(
        desc="what the learner has already said or tried")
    prior_questions: list[str] = dspy.InputField(
        desc="questions already asked, must not be repeated")
    next_question: str = dspy.OutputField(
        desc="ONE question, open-ended, calibrated to learner's depth")
    why_this_question: str = dspy.OutputField(
        desc="diagnostic intent — what gap this probes")
    expected_outcomes: list[str] = dspy.OutputField(
        desc="possible answers and what each would reveal")
    assertion: None = dspy.OutputField(
        desc="MUST be null. The agent does not assert.")
```

## Recommended tools

- `vector-search` — pull prior threads with this learner to track depth
- `embed-text` — score similarity to `prior_questions` for novelty
- `five-whys` — chained probing when the learner gives a shallow answer

## Recommended governors

- `anti-sycophancy` — block "great question!" leading lines
- `echo-chamber-breaker` — reject `next_question` too similar to prior
- A *custom* governor `must-ask` that fails the run if the output
  contains assertive sentences (heuristic: declarative without `?`)
- `output-length-cap` — one question, not a paragraph

## Demonstrations sketch

- Junior engineer: "I think we should add a cache here." →
  "What latency are you seeing today, and what would 'fast enough'
  look like?"
- Designer: "The new layout is better." →
  "Better for which user task, and how would we know?"
- PM stuck on a roadmap: "We have to ship feature X." →
  "Who told you you have to, and what happens to them if you don't?"

## Why it's a good demo

1. **It's the inverse of `support-agent`.** Support agents minimize
   user effort; tutors maximize useful effort. Pairing the two in a
   single demo makes the "agent shape is policy" point cleanly.
2. **It is a worked example of governor-as-style-enforcer.** Without
   `must-ask`, the LLM defaults to mixing assertion and question. The
   custom governor is what turns the *style* into a *contract*. The
   demo is also a tutorial on writing custom CLIPS rules over
   structured output.
3. **It pairs with `decision-journal-kg` and `naive-newcomer`.** The
   tutor's questions become entries in a learning log; `naive-
   newcomer` runs the same recursion against a codebase. Together
   they're a "system that asks why" — not a system that answers.

## Sample interaction

> topic_or_claim: "Our error rate jumped 3x after the deploy on Tuesday."
>
> learner_context: "I've already checked the deploy diff, looked at
> the dashboards, and the on-call runbook didn't help."

→ next_question: "Which signals are part of the 3x — is the error
  rate up uniformly across endpoints, or concentrated?"

→ why_this_question: "The learner has aggregated metrics but no
  decomposition. Without a partition, every fix is a guess. The
  question asks them to do the partition before proposing remedies."

→ expected_outcomes:
  - "Uniform" → suggests a shared dependency (auth, DB, infra) is the
    culprit; next probe is shared-deps.
  - "Concentrated on /foo" → suggests a code path; next probe is what
    changed in /foo's call tree.
  - "I don't know" → the partition has not been done; next probe is
    why the dashboard doesn't show it.

→ assertion: null
