# Hook Guidelines

> There is no browser hook layer in this repo today. Use this file mainly as a guardrail against premature framework code.

---

## Current State

Current automation entry points are:

- Trellis / Codex session hooks
- OpenClaw skills
- the polling-based `apps/live-studio/app.js` runtime talking to `scripts/live_bridge.py`
- external livestream tools and web dashboards

Do **not** introduce React/Vue hook abstractions unless the task explicitly creates a frontend runtime.

---

## Present-Day Equivalent

In this project, "hook-like" behavior usually means:

- session-start context injection
- skill invocation by trigger phrase
- local UI polling against `/api/state`
- external platform callbacks or exported data

Those should remain documented in `docs/` and `skills/`, not hidden behind hypothetical frontend abstractions.

---

## If Hooks Become Necessary Later

- One hook should wrap one external concern.
- Return explicit states: `idle`, `loading`, `success`, `error`.
- Normalize raw external data at the boundary.
- Keep retry, debounce, and timeout behavior explicit.
- Never perform secret management or webhook construction in UI code.

---

## Forbidden Patterns

- Adding hooks only because "modern frontend usually has hooks"
- Letting components directly parse raw barrage logs
- Letting presentation code call Feishu, TTS, or LLM APIs directly
