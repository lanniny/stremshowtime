# Directory Structure

> How automation logic, reference data, and generated outputs are organized in this project.

---

## Overview

The repo currently uses a self-contained skill layout:

```text
showman/
├── apps/
│   └── live-studio/      # Local operator console assets
├── config/
│   └── *.json            # Local bridge configuration examples / overrides
├── skills/
│   └── <skill>/
│       ├── SKILL.md         # Behavior contract and workflow
│       ├── references/      # Data or template files consumed by the skill
│       └── scripts/         # Optional implementation helpers if needed later
├── data/
│   ├── barrage-logs/        # Runtime log output
│   └── review-reports/      # Generated markdown reports
├── scripts/
│   ├── live_bridge.py       # Local bridge server entry point
│   └── showman_runtime/     # Shared runtime and adapters
├── docs/
│   ├── requirements/        # Frozen product/system requirements
│   ├── plans/               # Execution plans and decisions
│   └── guides/              # Operator runbooks and integrations
└── .trellis/                # Workflow and coding guidance
```

---

## Placement Rules

- New runtime or automation scripts belong under the owning skill's `scripts/` directory unless they are explicitly shared across multiple skills and the local bridge.
- Shared knowledge consumed by a skill belongs in that skill's `references/` directory unless you are explicitly doing a centralization refactor.
- Shared bridge/runtime helpers belong under `scripts/showman_runtime/`.
- Local console assets belong under `apps/live-studio/`.
- Runtime outputs go under `data/`.
- Frozen decisions and requirements stay in `docs/requirements/` or `docs/plans/`.
- Do not add more generic root-level `utils/`, `scripts/`, or `helpers/` unless multiple skills truly share the implementation.

---

## Naming Conventions

- Skill directories: kebab-case
- Script files: English snake_case or kebab-case, consistent within the skill
- Generated reports: date-prefixed
- Docs: capability-oriented or date-prefixed markdown names

---

## Cross-File Update Rule

When a change affects:

- product schema
- barrage categories
- notification payload fields
- report output structure

update all consuming skills, templates, and docs in the same change.

This repo is small enough that partial updates create confusion quickly.
