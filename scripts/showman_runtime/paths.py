from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_CATALOG = ROOT / "data" / "product-catalog" / "products.json"
BARRAGE_LOG_DIR = ROOT / "data" / "barrage-logs"
REVIEW_REPORT_DIR = ROOT / "data" / "review-reports"
REVIEW_TEMPLATE_PATH = (
    ROOT / "skills" / "livestream-review" / "references" / "review-template.md"
)
LIVE_STUDIO_APP_DIR = ROOT / "apps" / "live-studio"
LIVE_BRIDGE_CONFIG_PATH = ROOT / "config" / "live-bridge.json"
LIVE_BRIDGE_EXAMPLE_CONFIG_PATH = ROOT / "config" / "live-bridge.example.json"
DEMO_BARRAGE_INPUT_PATH = (
    ROOT / "skills" / "barrage-responder" / "references" / "full-demo-input.jsonl"
)
DEMO_METRICS_TEMPLATE_PATH = (
    ROOT / "skills" / "livestream-review" / "references" / "session-metrics-template.json"
)
DEFAULT_STAGE_VIDEO = ROOT / "讲解视频.mp4"
DEFAULT_STAGE_IDLE_IMAGE = ROOT / "static_idle.png"
DEFAULT_STAGE_SPEAKING_IMAGE = ROOT / "static_speaking.png"
