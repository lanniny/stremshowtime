# Component Guidelines

> Reusable presentation patterns in this repo are mostly markdown structures and templates, not UI components.

---

## Current State

There is still no shared React/Vue component system checked into this repository, but there is now one small local UI under `apps/live-studio/`.

The reusable "component" patterns that already exist are:

- five-section livestream script output
- structured review report sections
- setup guides written as short numbered steps
- tables for metrics, pricing, and comparisons
- live stage card, barrage feed cards, and integration status cards in `apps/live-studio/`

Before creating code components, first ask whether the need can be solved by reusing one of those existing content patterns.

---

## Preferred Reuse Patterns

### 1. Sectioned Outputs

When generating operator-facing deliverables, prefer explicit section headers over prose walls.

Examples:

- script sections: opening, pain points, selling points, CTA, closing
- report sections: summary, barrage analysis, suggestions, trend comparison

### 2. Small, Scannable Blocks

Prefer:

- short headings
- flat bullet lists
- compact tables
- explicit placeholders such as `[To confirm]`

### 3. Template-Driven Outputs

If an output format repeats, keep a reference template in `skills/<skill>/references/`.

Do not re-describe the same report or script structure differently in every task.

---

## Rules If UI Components Are Added Later

- Keep one component focused on one operator task.
- Presentation components must not be the source of truth for product data.
- External calls to LLMs, webhooks, or file IO must not live directly in rendering code.
- Prefer composition over building a large design system upfront.
- The existing `apps/live-studio/` page should stay a small operator console, not turn into a generic design system.

---

## Forbidden Patterns

- Creating a component library before there is an actual UI
- Hardcoding live prices or ingredients inside presentational assets
- Mixing operator instructions, business rules, and runtime logic into one giant file

---

## Examples In This Repo

- `skills/livestream-review/references/review-template.md`
- `docs/guides/P1-飞书Webhook配置指南.md`
- `apps/live-studio/index.html`
