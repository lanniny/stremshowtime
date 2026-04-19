# Type Safety

> This project relies more on contract safety for JSON and markdown than on TypeScript today.

---

## Current Contract Surface

The main structured contract in this repo is the product catalog stored in `products.json`.

Keep these rules stable:

- keys stay English and machine-readable
- display values may be Chinese
- repeated structures stay shape-consistent across products
- missing data is handled explicitly, never guessed

---

## Product Catalog Shape

Current product records commonly use fields such as:

- `id`
- `name`
- `brand`
- `category`
- `selling_points`
- `regular_price`
- `live_price`
- `per_unit_price`
- `gifts`
- `specs`
- `ingredients`
- `stock`
- `pain_points`
- `story`
- `competitors`
- `purchase_links`
- `faq`

Not every product currently has every pricing or ingredient field. Consumers must degrade gracefully when a field is absent.

---

## Shape Rules

### Arrays

- `selling_points`, `pain_points`, and `purchase_links` must remain arrays.
- Avoid mixing strings and objects in the same array.

### Nested Objects

- `specs` should stay an object with named keys such as `volume`, `packaging`, `storage`, `shelf_life`.
- `faq` should remain a simple key-value map for fast lookup.

### Purchase Links

Each entry should keep:

- `label`
- `url`
- `copy_text`

---

## Handling Missing Data

If a consuming skill needs a field that is missing:

1. do not invent it
2. mark it `[To confirm]` in human-facing output
3. or block the step with a clear operator message

---

## Future Code Rule

If scripts or UI code are later added, validate JSON shape at read time before using it in generated outputs.
