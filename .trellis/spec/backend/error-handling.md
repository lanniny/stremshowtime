# Error Handling

> Fail safely, stay factual, and escalate to humans when risk is high.

---

## Core Rule

If the system lacks trusted data, it must **stop, mark the gap, or escalate**.

It must not "smooth over" missing facts with plausible-sounding copy.

---

## Required Behaviors

### Missing Product Data

- If a requested product is not in `products.json`, tell the operator it is missing.
- If a field required for output is missing, use `[To confirm]` or block the step.
- Never invent prices, gifts, stock counts, ingredients, or shipping promises.

### High-Risk User Questions

If a barrage or prompt touches:

- medical efficacy
- legal disputes
- serious complaints
- privacy
- unsupported refund or compensation promises

route to human handling instead of auto-answering.

### Complaint Flow

For D-class complaint handling, the standard behavior is:

1. immediate public calming response
2. explicit human notification via Feishu webhook or equivalent

Do not collapse that into one step.

---

## Operator-Facing Error Style

Surface errors in a way a non-technical operator can act on:

- what failed
- which input or dependency is missing
- what to do next

Prefer direct messages over stack-trace style output.

Example:

```text
Cannot generate the script yet: product "xxx" was not found in products.json.
Next step: add the product record or choose an existing product name.
```

---

## Common Failure Cases

- product exists in one skill catalog but not the other
- `FEISHU_WEBHOOK_URL` is not configured
- barrage log format is malformed or incomplete
- report template placeholders are not filled
- review is requested before data exists

Each of these should produce a clear next action.

---

## Forbidden Patterns

- Silent fallback to made-up content
- Swallowing an integration failure and pretending the alert was sent
- Returning a risky public answer for a complaint that should be escalated
