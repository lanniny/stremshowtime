from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import os

from .paths import (
    DEFAULT_STAGE_IDLE_IMAGE,
    DEFAULT_STAGE_SPEAKING_IMAGE,
    DEFAULT_STAGE_VIDEO,
    LIVE_BRIDGE_CONFIG_PATH,
    ROOT,
)


DEFAULT_PRODUCT_QUERY = "一川桑语 NFC60%桑葚复合果汁饮料"
DEFAULT_HOST_NAME = "主播小桑"
DEFAULT_NEXT_LIVE = "本周五晚上 8 点"
DEFAULT_ROOM_TITLE = "一川桑语数字人直播间"


def _bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _int(value: object, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return default


def _float(value: object, default: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _text(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _string_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key).strip(): str(item).strip()
        for key, item in value.items()
        if str(key).strip()
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _resolve_repo_path(value: object, fallback: Path) -> Path:
    text = _text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.is_absolute():
        return path
    return ROOT / path


@dataclass(slots=True)
class BridgeServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    auto_push_replies: bool = False
    poll_interval_ms: int = 1500


@dataclass(slots=True)
class SessionDefaultsConfig:
    room_title: str = DEFAULT_ROOM_TITLE
    product_query: str = DEFAULT_PRODUCT_QUERY
    host_name: str = DEFAULT_HOST_NAME
    next_live_time: str = DEFAULT_NEXT_LIVE


@dataclass(slots=True)
class AssetConfig:
    stage_video: Path = DEFAULT_STAGE_VIDEO
    idle_image: Path = DEFAULT_STAGE_IDLE_IMAGE
    speaking_image: Path = DEFAULT_STAGE_SPEAKING_IMAGE
    poster_image: Path = DEFAULT_STAGE_SPEAKING_IMAGE


@dataclass(slots=True)
class FeishuConfig:
    webhook_url: str | None = None
    webhook_env: str = "FEISHU_WEBHOOK_URL"

    def resolved_webhook_url(self, env: dict[str, str] | None = None) -> str | None:
        if self.webhook_url:
            return self.webhook_url
        variables = env or dict(os.environ)
        candidate = variables.get(self.webhook_env)
        if candidate:
            return candidate.strip() or None
        return None


@dataclass(slots=True)
class AIGCPanelLauncherConfig:
    enabled: bool = False
    base_url: str = "http://127.0.0.1:8888"
    probe_base_urls: list[str] = field(default_factory=list)
    ping_path: str = "/ping"
    config_path: str = "/config"
    submit_path: str = "/submit"
    query_path: str = "/query"
    cancel_path: str = "/cancel"
    upload_path: str = "/upload"
    download_path: str = "/download"
    root: str | None = None
    entry: str | None = None
    entry_args: list[str] = field(default_factory=list)
    entry_placeholders: dict[str, str] = field(default_factory=dict)
    envs: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    result_roots: list[str] = field(default_factory=list)
    auto_query: bool = True
    query_interval_ms: int = 2000
    query_max_attempts: int = 45
    timeout_seconds: float = 10.0

    @property
    def ready(self) -> bool:
        return self.enabled and bool(self.entry)


@dataclass(slots=True)
class BarrageRelayConfig:
    websocket_url: str = "ws://127.0.0.1:8888"
    relay_url: str = "http://127.0.0.1:8765/api/barrage"
    format_name: str = "barragegrab_type3"
    timeout_seconds: float = 5.0


@dataclass(slots=True)
class LiveBridgeConfig:
    server: BridgeServerConfig = field(default_factory=BridgeServerConfig)
    session: SessionDefaultsConfig = field(default_factory=SessionDefaultsConfig)
    assets: AssetConfig = field(default_factory=AssetConfig)
    feishu: FeishuConfig = field(default_factory=FeishuConfig)
    aigcpanel: AIGCPanelLauncherConfig = field(default_factory=AIGCPanelLauncherConfig)
    barrage_source: BarrageRelayConfig = field(default_factory=BarrageRelayConfig)
    source_path: Path | None = None


def load_live_bridge_config(
    path: Path | None = None,
    env: dict[str, str] | None = None,
) -> LiveBridgeConfig:
    config_path = path or LIVE_BRIDGE_CONFIG_PATH
    payload: dict[str, object] = {}

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError(f"Live bridge config must be a JSON object: {config_path}")
        payload = {str(key): value for key, value in loaded.items()}
    elif path is not None:
        raise FileNotFoundError(config_path)

    server_payload = _mapping(payload.get("server"))
    session_payload = _mapping(payload.get("session"))
    assets_payload = _mapping(payload.get("assets"))
    integrations_payload = _mapping(payload.get("integrations"))
    feishu_payload = _mapping(integrations_payload.get("feishu"))
    aigcpanel_payload = _mapping(integrations_payload.get("aigcpanel"))
    barrage_payload = _mapping(payload.get("barrage_source"))

    server = BridgeServerConfig(
        host=_text(server_payload.get("host"), "127.0.0.1"),
        port=_int(server_payload.get("port"), 8765),
        auto_push_replies=_bool(server_payload.get("auto_push_replies")),
        poll_interval_ms=_int(server_payload.get("poll_interval_ms"), 1500),
    )
    session = SessionDefaultsConfig(
        room_title=_text(session_payload.get("room_title"), DEFAULT_ROOM_TITLE),
        product_query=_text(session_payload.get("product"), DEFAULT_PRODUCT_QUERY),
        host_name=_text(session_payload.get("host_name"), DEFAULT_HOST_NAME),
        next_live_time=_text(session_payload.get("next_live_time"), DEFAULT_NEXT_LIVE),
    )
    assets = AssetConfig(
        stage_video=_resolve_repo_path(assets_payload.get("stage_video"), DEFAULT_STAGE_VIDEO),
        idle_image=_resolve_repo_path(assets_payload.get("idle_image"), DEFAULT_STAGE_IDLE_IMAGE),
        speaking_image=_resolve_repo_path(
            assets_payload.get("speaking_image"),
            DEFAULT_STAGE_SPEAKING_IMAGE,
        ),
        poster_image=_resolve_repo_path(
            assets_payload.get("poster_image"),
            DEFAULT_STAGE_SPEAKING_IMAGE,
        ),
    )
    feishu = FeishuConfig(
        webhook_url=_text(feishu_payload.get("webhook_url")) or None,
        webhook_env=_text(feishu_payload.get("webhook_env"), "FEISHU_WEBHOOK_URL"),
    )
    aigcpanel = AIGCPanelLauncherConfig(
        enabled=_bool(aigcpanel_payload.get("enabled")),
        base_url=_text(aigcpanel_payload.get("base_url"), "http://127.0.0.1:8888"),
        probe_base_urls=_string_list(aigcpanel_payload.get("probeBaseUrls")),
        ping_path=_text(aigcpanel_payload.get("ping_path"), "/ping"),
        config_path=_text(aigcpanel_payload.get("config_path"), "/config"),
        submit_path=_text(aigcpanel_payload.get("submit_path"), "/submit"),
        query_path=_text(aigcpanel_payload.get("query_path"), "/query"),
        cancel_path=_text(aigcpanel_payload.get("cancel_path"), "/cancel"),
        upload_path=_text(aigcpanel_payload.get("upload_path"), "/upload"),
        download_path=_text(aigcpanel_payload.get("download_path"), "/download"),
        root=_text(aigcpanel_payload.get("root")) or None,
        entry=_text(aigcpanel_payload.get("entry")) or None,
        entry_args=_string_list(aigcpanel_payload.get("entryArgs")),
        entry_placeholders=_string_mapping(aigcpanel_payload.get("entryPlaceholders")),
        envs=_string_mapping(aigcpanel_payload.get("envs")),
        headers=_string_mapping(aigcpanel_payload.get("headers")),
        result_roots=_string_list(aigcpanel_payload.get("resultRoots")),
        auto_query=_bool(aigcpanel_payload.get("auto_query"), True),
        query_interval_ms=_int(aigcpanel_payload.get("query_interval_ms"), 2000),
        query_max_attempts=_int(aigcpanel_payload.get("query_max_attempts"), 45),
        timeout_seconds=_float(aigcpanel_payload.get("timeout_seconds"), 10.0),
    )
    barrage_source = BarrageRelayConfig(
        websocket_url=_text(barrage_payload.get("websocket_url"), "ws://127.0.0.1:8888"),
        relay_url=_text(
            barrage_payload.get("relay_url"),
            f"http://{server.host}:{server.port}/api/barrage",
        ),
        format_name=_text(barrage_payload.get("format"), "barragegrab_type3"),
        timeout_seconds=_float(barrage_payload.get("timeout_seconds"), 5.0),
    )

    config = LiveBridgeConfig(
        server=server,
        session=session,
        assets=assets,
        feishu=feishu,
        aigcpanel=aigcpanel,
        barrage_source=barrage_source,
        source_path=config_path if config_path.exists() else None,
    )

    variables = env or dict(os.environ)
    if not config.feishu.webhook_url:
        webhook_override = variables.get(config.feishu.webhook_env)
        if webhook_override:
            config.feishu.webhook_url = webhook_override.strip() or None

    return config
