# Code Reuse Thinking Guide

> Before adding a new prompt pattern, schema, or helper, check whether this repo already has the same idea elsewhere.

---

## The Real Duplication Risks In This Repo

The main duplication risks here are not classes or utility functions. They are:

- product facts edited in one place but not synced to all mirrored `products.json` files
- repeated barrage reply wording
- repeated report sections and headings
- repeated human-escalation rules
- repeated references to the same external workflow in docs and skills

These drift quietly and are hard for operators to notice until a live session goes wrong.

---

## Search First

Use `rg`, not guesswork.

Examples:

```bash
rg "live_price" .
rg "投诉预警" .
rg "A类" .
rg "review-template" .
```

---

## Reuse Targets That Already Exist

Before creating something new, look for:

- the five-part livestream script structure in `skills/livestream-script/SKILL.md`
- the A/B/C/D/E barrage model in `skills/barrage-responder/SKILL.md`
- the review report structure in `skills/livestream-review/references/review-template.md`
- existing product schema in `data/product-catalog/products.json`

---

## Duplication Rule For Product Data

If you change any product fact:

1. update `data/product-catalog/products.json`
2. run `python scripts/sync-product-catalog.py`
3. verify every mirrored `products.json`
4. check the consuming skill instructions for stale wording

Do not fix one mirrored file and leave the rest behind.

---

## When To Extract Shared Structure

Extract shared files or helpers when:

- three or more consumers need the same contract
- drift has already caused confusion
- the new shared abstraction has a clear owner and migration plan

Do **not** centralize halfway.

Bad:

- add a new shared file but leave old copies in place without migrating consumers

Good:

- keep duplication explicit until you can migrate all readers together

---

## Checklist Before Commit

- [ ] Searched for repeated fields or wording
- [ ] Updated all copies of shared product facts
- [ ] Reused an existing template where possible
- [ ] Avoided introducing a partial abstraction with unclear ownership
