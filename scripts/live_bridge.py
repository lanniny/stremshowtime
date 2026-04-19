#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
LIB_ROOT = ROOT / "scripts"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from showman_runtime.live_bridge import LiveStudioService, create_live_studio_server
from showman_runtime.live_config import load_live_bridge_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local live-studio bridge server.")
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional JSON config path. Defaults to config/live-bridge.json when present.",
    )
    parser.add_argument("--host", help="Optional host override.")
    parser.add_argument("--port", type=int, help="Optional port override.")
    parser.add_argument(
        "--load-demo",
        action="store_true",
        help="Load the sample barrage stream into the session after startup.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_live_bridge_config(args.config)
    if args.host:
        config.server.host = args.host
    if args.port:
        config.server.port = args.port
        config.barrage_source.relay_url = (
            f"http://{config.server.host}:{config.server.port}/api/barrage"
        )

    service = LiveStudioService(config)
    if args.load_demo:
        service.load_demo_stream()

    server = create_live_studio_server(config.server.host, config.server.port, service)
    url = f"http://{config.server.host}:{config.server.port}"
    print(f"Live studio bridge is running at {url}")
    print("Open the URL above in a browser to view the livestream console.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping live studio bridge...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
