# State Management

> In this repository, state is currently file-based and workflow-based rather than frontend-store-based.

---

## Source of Truth

Use the following sources as canonical:

| Data Type | Current Source |
|-----------|----------------|
| Canonical product knowledge | `data/product-catalog/products.json` |
| Skill-local product mirrors | `skills/*/references/products.json` |
| Ephemeral live session state | `scripts/live_bridge.py` in-memory session exposed via `/api/state` |
| Review output format | `skills/livestream-review/references/review-template.md` |
| Runtime barrage logs | `data/barrage-logs/` |
| Generated review reports | `data/review-reports/` |
| Requirements and rollout decisions | `docs/requirements/`, `docs/plans/` |

---

## Rules

1. Do not create a second source of truth for product facts in docs or future UI code.
2. Generated artifacts belong in `data/`, not inside the docs tree.
3. Product fact changes start from the canonical catalog, then propagate via `python scripts/sync-product-catalog.py`.
4. The local live-studio UI may hold temporary form state, but persisted facts still come from the canonical catalog or generated `data/` outputs.
5. Treat screenshots and guide text as explanatory views, not persistent state.

---

## Mirror Note

The repo keeps mirrored product files for skill compatibility:

- `data/product-catalog/products.json`
- `skills/livestream-script/references/products.json`
- `skills/barrage-responder/references/products.json`

The shared file is authoritative. The skill-local files are generated mirrors.

When editing product facts:

- edit the canonical file
- run the sync script
- verify mirrors before finishing

---

## If a UI Is Added Later

- Ephemeral form state can live locally in the UI.
- Persisted product data should still come from one canonical file or service.
- Derived views should be recomputed from source data, not hand-maintained.

---

## Forbidden Patterns

- Hardcoding product info into forms, cards, or screenshots
- Saving generated reports back into `docs/`
- Adding a global store before there is an actual multi-screen UI
