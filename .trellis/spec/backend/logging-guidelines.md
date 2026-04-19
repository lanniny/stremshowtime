# Logging Guidelines

> Logs and reports in this repo must help operators review what happened without leaking unnecessary data.

---

## Current Logging Surfaces

| Output | Location | Audience |
|--------|----------|----------|
| Barrage logs | `data/barrage-logs/` | Operators / future automation |
| Review reports | `data/review-reports/` | Operators / decision makers |
| Alert payloads | External Feishu messages | Human controllers |

---

## What To Capture

For runtime or generated records, keep the minimum useful context:

- timestamp
- skill or flow name
- product identifier when relevant
- barrage category when relevant
- action taken
- outcome or status

---

## Privacy Rules

- Do not persist secrets in logs.
- Keep user-identifying data minimal.
- If a complaint path needs the sender nickname for follow-up, include only what is operationally necessary.
- Do not dump full raw chat history into reports unless explicitly required.

---

## File Placement Rules

- Raw or machine-oriented records go in `data/barrage-logs/`.
- Human-readable summaries go in `data/review-reports/`.
- Do not store generated runtime logs inside `docs/`.

---

## Formatting Rules

- Prefer stable markdown or JSON formats over ad hoc prose.
- Use date-prefixed filenames where possible.
- Keep report sections consistent with `review-template.md`.

---

## Alert Logging Rule

If a complaint notification fails, that failure must be visible to the operator.

Do not act as if a human was notified when the webhook call failed or was not configured.
