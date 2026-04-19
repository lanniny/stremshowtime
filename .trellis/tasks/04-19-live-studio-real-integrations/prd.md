# Live Studio Console And Real Integrations

## Goal

Upgrade the local digital-human demo into a livestream-room style console and connect it to real integration boundaries for AIGCPanel, Feishu, and barrage sources.

## Requirements

- Provide a local HTTP bridge that exposes a single live session state for the UI and integrations.
- Add an operator-facing live-studio UI under `apps/` that feels like a livestream control room instead of a static preview page.
- Reuse the existing script generation, barrage reply, and review runtime modules instead of duplicating business logic.
- Support real Feishu webhook testing and complaint escalation through configured webhook URLs.
- Support real AIGCPanel launcher API calls using the official `/ping`, `/submit`, `/query`, and `/cancel` flow.
- Support real barrage ingestion through HTTP plus a relay script for BarrageGrab-style WebSocket sources.
- Keep product facts sourced from `data/product-catalog/products.json`.
- Keep failures operator-actionable and visible in the UI.

## Acceptance Criteria

- [ ] Running `python scripts/live_bridge.py` starts a local server that serves the live-studio UI.
- [ ] The UI shows a digital-human stage, livestream stats, current script, barrage feed, alerts, and integration status panels.
- [ ] Starting or resetting a session regenerates the script from the canonical catalog for the selected product.
- [ ] Posting a barrage through the bridge classifies it, appends runtime logs, updates the UI state, and triggers Feishu alerts for D-class messages when configured.
- [ ] Triggering an AIGCPanel action submits a launcher task and records the returned token/status in session state.
- [ ] A relay script exists for BarrageGrab-compatible WebSocket output and forwards normalized messages into the bridge API.
- [ ] Unit tests cover the new config/session/integration helpers and the existing runtime tests still pass.
- [ ] Documentation explains how to configure and run the upgraded local console with real integrations.

## Technical Notes

- Use stdlib-friendly server and HTTP client code where possible.
- Keep the UI isolated under `apps/live-studio/`.
- Treat AIGCPanel integration as launcher-task orchestration, with placeholder-based command submission driven by config.
- Treat barrage source integration as boundary normalization: convert external event shape into `{user, message}` before calling existing reply logic.
- Persist generated reports and barrage logs under `data/`, not under `docs/`.
