# Quality Guidelines

> Backend quality in this repo is about clear ownership, trustworthy data use, and predictable skill behavior.

---

## Design Principles

1. One skill, one job.
2. Keep skills self-contained unless there is a clear shared abstraction.
3. Reference files are authoritative for factual content.
4. Generated outputs must follow stable structures.
5. Human escalation is part of the designed system behavior.

---

## Skill Design Rules

- `livestream-script` owns script generation.
- `barrage-responder` owns barrage classification and reply behavior.
- `livestream-review` owns post-session analysis and report generation.

Do not merge those responsibilities casually into one giant skill.

---

## Determinism Rules

- Use explicit section structures.
- Keep classification schemes stable.
- Keep output paths predictable.
- When business facts change, update the source data instead of patching around it in prompts.

---

## Validation Expectations

Before finishing backend-like work, verify:

- [ ] required source files exist
- [ ] schema changes are reflected in every consumer
- [ ] operator-facing messages explain next steps
- [ ] complaint flows still escalate correctly
- [ ] outputs land in the right `data/` directory

---

## Common Bad Patterns

- Hardcoding product facts directly in `SKILL.md`
- Allowing one skill's reference data to drift from another's
- Writing generated outputs into `docs/`
- Mixing setup instructions, runtime logic, and postmortem output in one file

---

## Testing Guidance For Future Scripts

If executable scripts are added later, cover at least:

- happy path
- unknown product
- missing required field
- missing webhook configuration
- complaint escalation path
