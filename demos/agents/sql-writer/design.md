# Agent · `sql-writer`

Takes a natural-language question and a schema, returns a SQL query
plus an explanation. Read-only by default.

## Purpose

The "ask your database" agent. Used in `support-agent`, internal data
exploration, and most analyst-facing demos. Pairs with `sql-query`
(tool) for the read-execute-summarize loop.

## DSPy signature

```python
class WriteSQL(dspy.Signature):
    question: str = dspy.InputField()
    schema: str = dspy.InputField(desc="DDL or table summaries")
    dialect: Literal["postgres", "mysql", "sqlite", "bigquery"] = dspy.InputField()
    sql: str = dspy.OutputField(desc="single statement, read-only")
    explanation: str = dspy.OutputField(desc="why this query answers the question")
    estimated_cost: Literal["low", "medium", "high"] = dspy.OutputField()
```

## Recommended tools

- `sql-query` — execute the produced query (read-only)
- `vector-search` — retrieve example queries against this schema

## Recommended governors

- `tool-allowlist` — block write verbs (INSERT/UPDATE/DELETE/DDL)
- `cost-ceiling` — reject queries whose `estimated_cost` is high
- `schema-validator` — produced SQL must parse against the dialect

## Demonstrations sketch

- "How many tickets did we close last week?" → simple aggregate
- "Top 5 accounts by churn risk" → join across CRM and product schemas
- "Which features did our largest customer not adopt?" → multi-CTE query

## Why it's a good demo

The combination of `tool-allowlist` (read-only) + `cost-ceiling` (no
runaway scans) is a tight, comprehensible governor story. New users
immediately see why governors are not just safety theater.
