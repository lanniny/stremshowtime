# Thinking Guides

> Use these guides to reason about this repository's real failure modes before changing prompts, data, or integrations.

---

## Why These Guides Matter Here

This repo is small, but it crosses many boundaries quickly:

- operator prompt
- skill contract
- JSON reference data
- LLM-generated output
- external livestream tooling
- human escalation and review

Most failures here are not syntax bugs. They are contract, consistency, and workflow bugs.

---

## Available Guides

| Guide | Use It When |
|-------|-------------|
| `code-reuse-thinking-guide.md` | Changing product facts, reply templates, or repeated structures across skills |
| `cross-layer-thinking-guide.md` | Touching any end-to-end flow across prompts, reference files, logs, reports, or webhooks |

---

## Project-Specific Triggers

Read the cross-layer guide when a task involves any of:

- `products.json` changes
- barrage classification changes
- webhook notifications
- report generation
- introducing scripts under `skills/*/scripts/`

Read the code reuse guide when a task involves any of:

- updating product info in more than one place
- repeating the same answer or template logic across skills
- proposing a new shared helper or shared data file

---

## Search First Rule

Before changing a field, category, or repeated phrase, search the repo first.

Preferred command:

```bash
rg "value_or_field_name" .
```

This is especially important for:

- product prices
- FAQ keys
- barrage category names
- report headings
