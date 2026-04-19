# Directory Structure

> How operator-facing and visual assets are organized in this project.

---

## Overview

The current repository is a **skills + docs + data** project, not a conventional frontend codebase.

Use the existing top-level structure instead of inventing a UI app layout:

```text
showman/
├── apps/
│   └── live-studio/    # 本地直播控制台（静态 HTML/CSS/JS）
├── docs/
│   ├── guides/          # Operator-facing setup and runbooks
│   ├── plans/           # Execution plans and rollout notes
│   └── requirements/    # Frozen requirement documents
├── skills/
│   └── <skill>/
│       ├── SKILL.md     # User-invocable behavior contract
│       └── references/  # Templates and knowledge files used by the skill
├── data/
│   ├── barrage-logs/    # Runtime log outputs
│   └── review-reports/  # Generated review reports
└── *.png / *.mp4        # Visual references and captured states
```

---

## Placement Rules

- Put operator instructions in `docs/guides/`.
- Put the local livestream console in `apps/live-studio/`.
- Put requirement snapshots in `docs/requirements/`.
- Put reusable output templates under the owning skill's `references/` directory.
- Keep generated outputs under `data/`, never under `docs/`.
- Treat root-level images and videos as references for now; if they grow further, reorganize them in a dedicated refactor.

---

## If Real UI Code Is Added Later

This repo does not yet define a checked-in frontend runtime.

If the user explicitly asks for another local UI:

1. Confirm the runtime first.
2. Prefer another isolated `apps/<app-name>/` directory over dropping `src/` at repo root.
3. Keep UI code isolated from `docs/`, `skills/`, and `data/`.

Do not create framework directories speculatively.

---

## Naming Conventions

- New docs: date-prefixed or capability-prefixed markdown files are preferred.
- New reusable assets: prefer ASCII + kebab-case unless the file is intentionally operator-facing Chinese documentation.
- Skill directories stay kebab-case, matching existing examples:
  - `livestream-script`
  - `barrage-responder`
  - `livestream-review`

---

## Examples

- `docs/guides/P0-弹幕抓取工具指南.md`
- `docs/requirements/2026-04-15-ai-livestream-system.md`
- `skills/livestream-review/references/review-template.md`
- `apps/live-studio/index.html`
