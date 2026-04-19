# Backend Development Guidelines

> In this repo, "backend" means skill orchestration, reference data, generated artifacts, and integration logic.

---

## Current Reality

This repository still does **not** contain a traditional multi-service backend or database service, but it now includes a local HTTP bridge for demo and integration testing.

The backend-like layer currently lives in:

- `skills/*/SKILL.md` for behavior contracts
- `scripts/showman_runtime/` for shared runtime and integration helpers
- `scripts/live_bridge.py` for the local bridge server
- `skills/*/references/` for structured knowledge and templates
- `data/` for runtime outputs
- `docs/requirements/` and `docs/plans/` for frozen decisions
- `skills/*/scripts/` for runnable skill entry points

---

## When This Layer Applies

Read this layer before work that changes:

- product knowledge files
- barrage classification logic
- webhook notification flows
- generated report outputs
- future automation scripts or adapters
- local bridge API flows and integration adapters

---

## Pre-Development Checklist

Before making backend-like changes, read:

1. `directory-structure.md`
2. `database-guidelines.md`
3. `error-handling.md`
4. `logging-guidelines.md`
5. `quality-guidelines.md`
6. `../guides/cross-layer-thinking-guide.md` for any flow that spans prompts, files, LLM output, or external tools

---

## Project-Specific Principles

1. One skill should own one clear responsibility.
2. Reference files are the source of truth for factual content.
3. Generated artifacts belong in `data/`, not `docs/`.
4. Missing or risky information must fail safely.
5. Human escalation is a core feature, not an edge case.

---

## Good Examples In This Repo

- `skills/livestream-script/SKILL.md`
- `skills/barrage-responder/SKILL.md`
- `skills/livestream-review/SKILL.md`
- `docs/requirements/2026-04-15-ai-livestream-system.md`
