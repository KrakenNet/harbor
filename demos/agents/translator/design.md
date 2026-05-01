# Agent · `translator`

Translates text between languages with optional glossary and tone
controls. Locale-aware, terminology-aware.

## Purpose

Standard demo for multilingual support: localize KB articles, translate
inbound support tickets, render outbound notifications. Pairs with
`support-agent` and `faq-answerer` for non-English deployments.

## DSPy signature

```python
class Translate(dspy.Signature):
    text: str = dspy.InputField()
    source_lang: str = dspy.InputField(desc="ISO 639-1, or 'auto'")
    target_lang: str = dspy.InputField()
    glossary: dict[str, str] = dspy.InputField(
        desc="terms that MUST translate this way")
    tone: Literal["formal", "casual", "neutral"] = dspy.InputField()
    translation: str = dspy.OutputField()
    detected_source_lang: str = dspy.OutputField()
    glossary_hits: list[str] = dspy.OutputField(
        desc="glossary terms encountered")
```

## Recommended tools

- `vector-search` — retrieve company-specific terminology
- `language-id` (ml model) — verify `source_lang`
- `regex-match` — preserve untranslatable tokens (codes, IDs, URLs)

## Recommended governors

- `pii-redactor` — translation often crosses jurisdictions
- `compliance-scan` — geo-fenced data must not cross to certain locales
- `geo-fence` — block target languages for restricted tenants

## Demonstrations sketch

- Inbound German support ticket → English with product glossary applied
- English release notes → Spanish, casual tone, brand names preserved
- Korean legal notice → English, formal tone, glossary required

## Why it's a good demo

Glossary enforcement is a great showcase for governors: a `glossary-
adherence` policy can fail any output that mistranslates a required
term, turning what's usually a manual QA step into a compile-time
check.
