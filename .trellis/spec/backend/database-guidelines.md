# Database Guidelines

> There is no database service in this repo today. The persistent layer is file-based.

---

## Current Persistence Model

| Purpose | Storage |
|---------|---------|
| Canonical product catalog | `data/product-catalog/products.json` |
| Skill-local product mirrors | `skills/*/references/products.json` |
| Review template | `skills/livestream-review/references/review-template.md` |
| Barrage logs | `data/barrage-logs/` |
| Generated reports | `data/review-reports/` |

Treat these files as the backend data layer.

---

## Product Catalog Rules

The current MVP now keeps one canonical product catalog plus skill-local mirrored copies for compatibility.

Current layout:

- canonical source: `data/product-catalog/products.json`
- mirrored copies:
  - `skills/livestream-script/references/products.json`
  - `skills/barrage-responder/references/products.json`

Rules:

1. Edit the canonical source first.
2. After changes, run `python scripts/sync-product-catalog.py`.
3. Do not manually patch one mirrored copy and leave the others stale.
4. Do not silently rename fields such as `live_price`, `faq`, or `purchase_links`.
5. Do not convert structured objects like `specs` into freeform paragraphs.

---

## When To Centralize

Centralize shared data only when:

- three or more skills need the same file
- drift has already caused bugs
- you are prepared to update every consumer in the same task

The repo now uses a shared source plus synchronized mirrors; keep that pattern consistent unless you are migrating runtime consumers too.

---

## Output Data Rules

- Save generated reports under `data/review-reports/`.
- Save raw or semi-structured runtime logs under `data/barrage-logs/`.
- Prefer append-only or date-stamped files over mutating historical records.

---

## Secrets

Secrets such as `FEISHU_WEBHOOK_URL` must live in environment configuration, never in repo data files.
