# Centralize Product Catalog Source of Truth

## Goal

Reduce maintenance drift around product knowledge by introducing one canonical product catalog file for the repository, while preserving the current skill-local file layout expected by existing OpenClaw skill instructions.

## Problem

Today the same product catalog is duplicated in:

- `skills/livestream-script/references/products.json`
- `skills/barrage-responder/references/products.json`

They are currently identical, but future edits can easily update one file and forget the other. This repo is intentionally small and operator-friendly, so the fix should be simple, explicit, and low-risk.

## Requirements

- Introduce one canonical product catalog file in a repo-level shared location.
- Preserve skill-local `references/products.json` files so current skill instructions do not break.
- Add a simple sync mechanism that refreshes skill-local copies from the canonical source.
- Update skill documentation so future edits happen in the canonical file first.
- Keep the product schema unchanged.
- Avoid symlink-only solutions that may be brittle on Windows or in other environments.

## Acceptance Criteria

- [ ] A single canonical catalog file exists in a shared location.
- [ ] Both skill-local `references/products.json` files are regenerated from that canonical file.
- [ ] A sync command/script exists and runs successfully in this repo.
- [ ] `livestream-script` and `barrage-responder` docs point maintainers to the canonical file and sync flow.
- [ ] No product values or schema fields change during the refactor.

## Non-Goals

- Building a database or API service
- Changing OpenClaw runtime behavior
- Redesigning the product schema
- Refactoring all docs that merely mention `products.json` as an example

## Technical Notes

- Prefer a shared path under `data/` because this repo already uses `data/` for maintained runtime-facing artifacts.
- Use a small repo script for synchronization instead of relying on symlink permissions.
- Keep the change boring and reversible.
