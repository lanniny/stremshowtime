# Frontend Development Guidelines

> Use this layer for operator-facing assets, visual references, and any future UI work.

---

## Current Reality

This repository now contains a small checked-in local UI runtime for operator demo and integration testing.

What currently acts as the "frontend" layer is:

- `docs/guides/` for operator-facing setup instructions
- `apps/live-studio/` for the local livestream-room style console
- `scripts/live_bridge.py` for serving the local UI and bridge API
- root-level `*.png` / `*.mp4` files for visual references and captured states
- `skills/*/references/*.md` for user-facing output templates
- external platforms such as Douyin Live, OBS, AIGCPanel, and digital-human tooling

That means the default frontend move in this repo is still usually **operator-facing documentation or template work**, but there is now one approved local UI surface under `apps/live-studio/`.

---

## When This Layer Applies

Read this layer before work that changes any of the following:

- operator instructions
- output formatting shown to non-technical users
- screenshots, mockups, and visual references
- report templates and structured markdown deliverables
- any proposal to add a real UI to this repo

---

## Pre-Development Checklist

Before editing operator-facing assets or proposing UI work, read:

1. `directory-structure.md`
2. `quality-guidelines.md`
3. `type-safety.md`
4. `../guides/cross-layer-thinking-guide.md` when product data, notifications, or generated outputs are involved

If you are about to introduce a second UI runtime beyond `apps/live-studio/`, pause and confirm the target platform first.

---

## Project-Specific Principles

1. Prefer markdown, templates, and workflow docs before building code UI.
2. Keep outputs usable by non-technical operators.
3. Do not hardcode product facts into presentation assets when they already exist in `products.json`.
4. Treat screenshots as references, not as the system of record.
5. If information is missing, mark `[To confirm]` instead of inventing values.

---

## Good Examples In This Repo

- `docs/guides/P0-数字人制作指南.md`
- `docs/guides/P1-飞书Webhook配置指南.md`
- `skills/livestream-review/references/review-template.md`
- `apps/live-studio/index.html`

---

## What To Avoid

- Creating a second `src/` or framework boilerplate without an explicit request
- Moving operator knowledge out of `docs/` into opaque prompt blobs
- Duplicating prices, ingredients, or FAQ answers across multiple presentation files without noting the source
