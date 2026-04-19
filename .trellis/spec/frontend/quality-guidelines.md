# Quality Guidelines

> Quality in this repo means operator clarity, factual accuracy, and stable structured outputs.

---

## What Good Looks Like

- Non-technical operators can follow the result without extra interpretation.
- Generated copy is energetic but traceable to source data.
- Markdown outputs are easy to scan.
- Every price, ingredient, stock statement, and FAQ answer can be traced to a source file.
- Missing information is surfaced explicitly.

---

## Writing Rules

1. Use clear headings and short sections.
2. Prefer tables for metrics, pricing, and comparisons.
3. Prefer numbered steps for setup guides.
4. Keep operator-facing language aligned with current repo style:
   - Chinese is fine for operator deliverables
   - English keys and filenames remain stable for machine-readable structures
5. When a claim is not backed by source data, output `[To confirm]`.

---

## Accuracy Rules

- Do not invent promotions, gifts, stock numbers, or shipping promises.
- Do not change factual values from `products.json` just to make copy sound better.
- Do not introduce medical, legal, or efficacy claims for food or drink products.
- Do not silently broaden a human-handled complaint into an auto-answer.

---

## Review Checklist

Before finishing a user-facing deliverable, verify:

- [ ] The output matches the expected structure for that skill
- [ ] Product facts match the reference data
- [ ] CTA language is present only when appropriate
- [ ] High-risk questions route to human support
- [ ] Any unknown field is marked `[To confirm]`

---

## Common Failure Modes

- Strong copy built on made-up numbers
- Rewriting a structured template into a wall of text
- Forgetting that this repo serves operators, not developers
- Spreading the same product fact into several markdown files with inconsistent wording
