# Cross-Layer Thinking Guide

> Map the full flow before changing anything that moves between prompts, data files, LLM outputs, and external tools.

---

## Why This Matters In This Repo

This project's core workflows are all cross-layer:

### Pre-live

```text
Operator request -> skill trigger -> skill-local products.json mirror -> canonical catalog maintenance flow -> LLM generation -> script output -> digital-human / broadcast tool
```

### During live

```text
Barrage source -> capture tool -> classification logic -> public reply -> webhook escalation -> human controller
```

### Post-live

```text
Session metrics + barrage logs -> analysis skill -> report template -> markdown report -> operator review
```

If one boundary shifts, the whole workflow can silently degrade.

---

## Boundaries To Check

| Boundary | What Can Break |
|----------|----------------|
| Operator request -> skill trigger | Wrong skill invoked, missing task context |
| Skill -> `products.json` | Missing fields, renamed keys, stale mirrors |
| Skill -> LLM output | Hallucinated values, wrong structure |
| Complaint flow -> Feishu | Alert not sent, false sense of coverage |
| Logs -> review report | Missing metrics, malformed categories |

---

## Before Implementing

### Step 1: Write the Flow

Write the exact path:

```text
input -> lookup -> transform -> output -> handoff
```

For each step, answer:

- What is the input format?
- Which file or system owns it?
- What validation happens here?
- What is the failure behavior?

### Step 2: Define the Contract

Be explicit about:

- required fields
- optional fields
- fallback behavior
- human escalation points

### Step 3: Check the External Handoff

Any flow touching external tools must answer:

- What if the tool is unavailable?
- What if the webhook is missing?
- What if the output arrives late?
- What if the result is high risk and should not be auto-posted?

---

## Common Repo-Specific Mistakes

- Updating the canonical catalog but forgetting to sync mirrored files
- Making the script generator rely on a field the barrage responder does not have
- Treating screenshots or docs as if they were live data
- Saving generated outputs into `docs/` instead of `data/`
- Assuming a complaint alert succeeded without confirming the notification path

---

## Checklist

Before shipping a cross-layer change:

- [ ] mapped the full flow end to end
- [ ] identified all source files and consumers
- [ ] defined behavior for missing data
- [ ] verified human escalation points
- [ ] confirmed output location and format
