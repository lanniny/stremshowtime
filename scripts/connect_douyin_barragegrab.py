#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
LIB_ROOT = ROOT / "scripts"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from showman_runtime.barrage_source import normalize_barrage_event, post_barrage_to_bridge
from showman_runtime.live_config import load_live_bridge_config


try:
    import websocket
except ImportError:  # pragma: no cover - exercised by runtime availability, not unit tests
    websocket = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Relay BarrageGrab WebSocket comments into the local live bridge."
    )
    parser.add_argument("--config", type=Path, help="Optional JSON config path.")
    parser.add_argument("--bridge-url", help="Override the bridge POST URL.")
    parser.add_argument("--websocket-url", help="Override the BarrageGrab WebSocket URL.")
    parser.add_argument("--format", default="barragegrab_type3", help="Source event format name.")
    parser.add_argument("--product", help="Optional product override forwarded to the bridge.")
    parser.add_argument(
        "--retry-seconds",
        type=float,
        default=3.0,
        help="Reconnect delay after the source disconnects.",
    )
    return parser.parse_args()


def _post_json(url: str, payload: dict[str, object], timeout_seconds: float = 5.0) -> None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds):
        return


def main() -> int:
    if websocket is None:
        print(
            "Missing dependency: websocket-client. Install it with 'pip install websocket-client' first.",
            file=sys.stderr,
        )
        return 2

    args = parse_args()
    config = load_live_bridge_config(args.config)
    bridge_url = args.bridge_url or config.barrage_source.relay_url
    websocket_url = args.websocket_url or config.barrage_source.websocket_url
    heartbeat_url = bridge_url.rsplit("/", 1)[0] + "/integrations/barrage/heartbeat"

    while True:
        print(f"Connecting to barrage source: {websocket_url}")

        def on_open(ws: websocket.WebSocketApp) -> None:
            print("Barrage source connected.")
            try:
                _post_json(
                    heartbeat_url,
                    {"status": "connected", "detail": f"BarrageGrab 已连接: {websocket_url}"},
                )
            except urllib.error.URLError:
                pass

        def on_message(ws: websocket.WebSocketApp, raw_message: str) -> None:
            try:
                payload = json.loads(raw_message)
                if not isinstance(payload, dict):
                    return
                normalized = normalize_barrage_event(payload, format_name=args.format)
            except (ValueError, json.JSONDecodeError):
                return

            bridge_payload: dict[str, object] = dict(normalized)
            if args.product:
                bridge_payload["product"] = args.product
            ok, status = post_barrage_to_bridge(bridge_url, bridge_payload)
            if ok:
                print(f"[relay] {normalized['user']}: {normalized['message']}")
            else:
                print(f"[relay-error] {status}", file=sys.stderr)

        def on_error(ws: websocket.WebSocketApp, error: object) -> None:
            print(f"[source-error] {error}", file=sys.stderr)

        def on_close(
            ws: websocket.WebSocketApp,
            status_code: int | None,
            close_msg: str | None,
        ) -> None:
            print(f"Source disconnected: {status_code} {close_msg or ''}".strip())
            try:
                _post_json(
                    heartbeat_url,
                    {"status": "disconnected", "detail": f"BarrageGrab 已断开: {status_code or ''}"},
                )
            except urllib.error.URLError:
                pass

        client = websocket.WebSocketApp(
            websocket_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        client.run_forever()
        print(f"Retrying in {args.retry_seconds:.1f}s...")
        time.sleep(args.retry_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
