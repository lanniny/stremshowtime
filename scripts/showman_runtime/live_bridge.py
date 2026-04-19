from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
from threading import Lock, Thread
import time
from urllib.parse import parse_qs, quote, unquote, urlparse

from .aigcpanel import (
    cancel_aigcpanel_launcher_task,
    ping_aigcpanel_launcher,
    query_aigcpanel_launcher_task,
    submit_aigcpanel_launcher_task,
)
from .barrage import process_single_barrage, send_feishu_alert
from .barrage_source import normalize_barrage_event
from .catalog import load_products, match_product
from .live_config import LiveBridgeConfig
from .paths import (
    BARRAGE_LOG_DIR,
    DEMO_BARRAGE_INPUT_PATH,
    DEMO_METRICS_TEMPLATE_PATH,
    LIVE_STUDIO_APP_DIR,
    REVIEW_REPORT_DIR,
    ROOT,
)
from .review import generate_review_artifacts, save_review_outputs
from .script_writer import build_livestream_script
from .session_state import LiveSessionState


def _load_json_file(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return payload


class LiveStudioService:
    def __init__(self, config: LiveBridgeConfig) -> None:
        self.config = config
        self.products = load_products()
        self.lock = Lock()
        self._aigcpanel_watchers: dict[str, Thread] = {}
        self.state = LiveSessionState.create(
            room_title=config.session.room_title,
            media={
                "stage_video": self._asset_url(config.assets.stage_video),
                "idle_image": self._asset_url(config.assets.idle_image),
                "speaking_image": self._asset_url(config.assets.speaking_image),
                "poster_image": self._asset_url(config.assets.poster_image),
            },
        )
        self._sync_integration_flags()
        self.start_session(
            product_query=config.session.product_query,
            host_name=config.session.host_name,
            next_live_time=config.session.next_live_time,
            room_title=config.session.room_title,
        )

    def _asset_url(self, path: Path) -> str:
        try:
            relative = path.resolve().relative_to(ROOT.resolve())
        except ValueError:
            return ""
        return "/media/" + relative.as_posix()

    def _sync_integration_flags(self) -> None:
        aigc_state = self.state.integrations.get("aigcpanel", {})
        self.state.update_integration_flags(
            feishu_configured=bool(self.config.feishu.resolved_webhook_url()),
            aigcpanel_enabled=self.config.aigcpanel.enabled,
            aigcpanel_ready=bool(self.config.aigcpanel.ready or aigc_state.get("resolved_entry")),
            aigcpanel_base_url=str(aigc_state.get("base_url") or self.config.aigcpanel.base_url),
            barrage_websocket_url=self.config.barrage_source.websocket_url,
            barrage_format=self.config.barrage_source.format_name,
        )

    def _can_submit_to_aigcpanel(self) -> bool:
        return self.config.aigcpanel.enabled and bool(
            self.config.aigcpanel.base_url
            or self.config.aigcpanel.probe_base_urls
            or self.config.aigcpanel.entry
        )

    def _can_auto_submit_to_aigcpanel(self) -> bool:
        aigc_state = self.state.integrations.get("aigcpanel", {})
        has_launcher = bool(
            self.config.aigcpanel.entry
            or aigc_state.get("resolved_entry")
        )
        if not self._can_submit_to_aigcpanel() or not has_launcher:
            return False
        action = str(aigc_state.get("last_action") or "")
        status = str(aigc_state.get("last_status") or "").strip().lower()
        if action not in {"ping", "submit", "query"}:
            return False
        if status in {"error", "failed", "failure", "timeout", "cancelled", "canceled"}:
            return False
        return True

    def _aigcpanel_allowed_roots(self) -> list[Path]:
        candidates: list[Path] = []
        if self.config.aigcpanel.root:
            candidates.append(Path(self.config.aigcpanel.root))
        for root in self.config.aigcpanel.result_roots:
            if root:
                candidates.append(Path(root))
        appdata = os.environ.get("APPDATA")
        local_appdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            candidates.append(Path(appdata) / "aigcpanel")
        if local_appdata:
            candidates.append(Path(local_appdata) / "aigcpanel")

        resolved_roots: list[Path] = []
        seen: set[Path] = set()
        for candidate in candidates:
            resolved = candidate.expanduser().resolve(strict=False)
            if resolved in seen:
                continue
            seen.add(resolved)
            resolved_roots.append(resolved)
        return resolved_roots

    def _is_allowed_aigcpanel_file(self, path: Path) -> bool:
        resolved = path.expanduser().resolve(strict=False)
        for root in self._aigcpanel_allowed_roots():
            try:
                resolved.relative_to(root)
            except ValueError:
                continue
            return True
        return False

    def _build_aigcpanel_result_url(self, local_path: str) -> str:
        return "/api/integrations/aigcpanel/result-file?path=" + quote(local_path, safe="")

    def resolve_aigcpanel_result_file(self, path_text: str) -> Path:
        clean = path_text.strip()
        if not clean:
            raise ValueError("AIGCPanel 结果文件路径为空。")
        target = Path(clean)
        if not self._is_allowed_aigcpanel_file(target):
            raise ValueError("AIGCPanel 结果文件不在允许访问的目录中。")
        resolved = target.expanduser().resolve(strict=False)
        if not resolved.is_file():
            raise ValueError(f"AIGCPanel 结果文件不存在：{resolved}")
        return resolved

    def _decorate_aigcpanel_result(self, result: dict[str, object]) -> dict[str, object]:
        base_url = str(result.get("base_url") or "").strip()
        if base_url and bool(result.get("ok")):
            self.config.aigcpanel.base_url = base_url

        local_path = str(result.get("local_path") or "").strip()
        if local_path and self._is_allowed_aigcpanel_file(Path(local_path)):
            result["media_url"] = self._build_aigcpanel_result_url(local_path)
        return result

    def _is_terminal_aigcpanel_status(self, status: str) -> bool:
        lowered = status.strip().lower()
        return lowered in {
            "success",
            "succeeded",
            "completed",
            "complete",
            "done",
            "error",
            "failed",
            "failure",
            "cancelled",
            "canceled",
            "timeout",
        }

    def _watch_aigcpanel_task(self, token: str) -> None:
        try:
            for _ in range(max(self.config.aigcpanel.query_max_attempts, 1)):
                time.sleep(max(self.config.aigcpanel.query_interval_ms, 250) / 1000.0)
                try:
                    result = self._decorate_aigcpanel_result(
                        query_aigcpanel_launcher_task(self.config.aigcpanel, token).to_dict()
                    )
                except ValueError as exc:
                    with self.lock:
                        self.state.add_error(str(exc))
                    break
                with self.lock:
                    self.state.record_aigcpanel_result(result)
                status = str(result.get("status") or "")
                if result.get("media_url") or self._is_terminal_aigcpanel_status(status):
                    break
        finally:
            self._aigcpanel_watchers.pop(token, None)

    def _start_aigcpanel_watch(self, token: str) -> None:
        if not token:
            return
        existing = self._aigcpanel_watchers.get(token)
        if existing and existing.is_alive():
            return
        watcher = Thread(target=self._watch_aigcpanel_task, args=(token,), daemon=True)
        self._aigcpanel_watchers[token] = watcher
        watcher.start()

    def _auto_submit_reply_text(self, text: str) -> None:
        if not self.config.server.auto_push_replies:
            return
        if not self._can_auto_submit_to_aigcpanel():
            return
        try:
            self.submit_to_aigcpanel(text=text)
        except ValueError as exc:
            with self.lock:
                self.state.add_error(str(exc))

    def snapshot(self) -> dict[str, object]:
        with self.lock:
            self._sync_integration_flags()
            return self.state.to_dict()

    def start_session(
        self,
        *,
        product_query: str,
        host_name: str,
        next_live_time: str,
        room_title: str,
    ) -> dict[str, object]:
        now = datetime.now().astimezone()
        product = match_product(self.products, product_query)
        script_text = build_livestream_script(
            product=product,
            host_name=host_name,
            next_live_time=next_live_time,
        )
        with self.lock:
            self.state.start_session(
                product=product,
                product_query=product_query,
                host_name=host_name,
                next_live_time=next_live_time,
                room_title=room_title,
                script_text=script_text,
                now=now,
            )
            self._sync_integration_flags()
            return self.state.to_dict()

    def process_barrage(
        self,
        payload: dict[str, object],
        *,
        sender=send_feishu_alert,
        webhook_url_override: str | None = None,
    ) -> dict[str, object]:
        product_query = str(payload.get("product") or "")
        if not product_query:
            product_query = str(self.state.selected_product_query or self.config.session.product_query)
        product = match_product(self.products, product_query)
        now = datetime.now().astimezone()
        webhook_url = webhook_url_override or self.config.feishu.resolved_webhook_url()
        decision, log_path = process_single_barrage(
            product=product,
            user=str(payload.get("user") or "匿名用户"),
            message=str(payload.get("message") or ""),
            webhook_url=webhook_url,
            now=now,
            log_dir=BARRAGE_LOG_DIR,
            sender=sender,
        )
        decision_payload = asdict(decision)
        decision_payload["log_path"] = str(log_path.relative_to(ROOT))
        with self.lock:
            self.state.record_barrage(decision_payload)
        if decision.tts_text:
            self._auto_submit_reply_text(decision.tts_text)
        return decision_payload

    def _demo_sender(
        self,
        webhook_url: str,
        user: str,
        message: str,
        product_name: str,
        alert_time: str,
    ) -> tuple[bool, str]:
        return True, "demo_alert_sent"

    def load_demo_stream(self) -> dict[str, object]:
        self.start_session(
            product_query=self.config.session.product_query,
            host_name=self.config.session.host_name,
            next_live_time=self.config.session.next_live_time,
            room_title=self.config.session.room_title,
        )
        with DEMO_BARRAGE_INPUT_PATH.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    continue
                self.process_barrage(
                    payload,
                    sender=self._demo_sender,
                    webhook_url_override="demo://feishu-webhook",
                )
        return self.snapshot()

    def broadcast_text(self, text: str, speaker: str | None = None) -> dict[str, object]:
        content = text.strip()
        if not content:
            raise ValueError("请输入要播报的内容。")
        with self.lock:
            entry = self.state.record_manual_broadcast(
                content,
                speaker=(speaker or self.state.host_name or "主播").strip() or "主播",
            )
        self._auto_submit_reply_text(content)
        return entry

    def reply_to_barrage(
        self,
        *,
        user: str,
        message: str,
        reply: str,
        category: str = "MANUAL",
    ) -> dict[str, object]:
        clean_reply = reply.strip()
        clean_message = message.strip()
        if not clean_message:
            raise ValueError("请输入要回复的弹幕内容。")
        if not clean_reply:
            raise ValueError("请输入回复内容。")
        with self.lock:
            entry = self.state.record_manual_reply(
                user=(user or "匿名用户").strip() or "匿名用户",
                message=clean_message,
                reply=clean_reply,
                category=(category or "MANUAL").strip() or "MANUAL",
            )
        self._auto_submit_reply_text(clean_reply)
        return entry

    def ping_aigcpanel(self) -> dict[str, object]:
        result = self._decorate_aigcpanel_result(
            ping_aigcpanel_launcher(self.config.aigcpanel).to_dict()
        )
        with self.lock:
            self.state.record_aigcpanel_result(result)
        return result

    def submit_to_aigcpanel(self, text: str | None = None) -> dict[str, object]:
        selected_text = text or str((self.state.current_reply or {}).get("tts_text") or "").strip()
        if not selected_text:
            raise ValueError("当前没有可推送给数字人的回复文本。")
        result = self._decorate_aigcpanel_result(
            submit_aigcpanel_launcher_task(
                self.config.aigcpanel,
                selected_text,
                context={
                    "host_name": self.state.host_name,
                    "product_name": self.state.product_name,
                    "product_id": self.state.product_id,
                    "room_title": self.state.room_title,
                    "session_id": self.state.session_id,
                },
            ).to_dict()
        )
        with self.lock:
            self.state.record_aigcpanel_result(result)
        if result.get("token") and self.config.aigcpanel.auto_query:
            self._start_aigcpanel_watch(str(result.get("token") or ""))
        return result

    def query_aigcpanel(self, token: str | None = None) -> dict[str, object]:
        selected_token = token or str(self.state.integrations["aigcpanel"].get("last_token") or "")
        result = self._decorate_aigcpanel_result(
            query_aigcpanel_launcher_task(self.config.aigcpanel, selected_token).to_dict()
        )
        with self.lock:
            self.state.record_aigcpanel_result(result)
        return result

    def cancel_aigcpanel(self) -> dict[str, object]:
        result = self._decorate_aigcpanel_result(
            cancel_aigcpanel_launcher_task(self.config.aigcpanel).to_dict()
        )
        with self.lock:
            self.state.record_aigcpanel_result(result)
        return result

    def test_feishu(self) -> dict[str, object]:
        webhook_url = self.config.feishu.resolved_webhook_url()
        if not webhook_url:
            raise ValueError("FEISHU_WEBHOOK_URL 未配置，无法发送联调测试。")
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        ok, status = send_feishu_alert(
            webhook_url=webhook_url,
            user="联调测试",
            message="本地直播桥测试消息",
            product_name=self.state.product_name or self.config.session.product_query,
            timestamp=timestamp,
        )
        payload = {
            "ok": ok,
            "status": status,
            "timestamp": timestamp,
        }
        with self.lock:
            self.state.record_feishu_test(status, "联调测试消息已触发")
        return payload

    def generate_review(self, overrides: dict[str, object] | None = None) -> dict[str, object]:
        metrics = _load_json_file(DEMO_METRICS_TEMPLATE_PATH)
        metrics.update(
            {
                "session_date": datetime.now().astimezone().date().isoformat(),
                "host_name": self.state.host_name,
                "product_name": self.state.product_name,
                "comments": len(self.state.barrage_entries),
                "likes": max(int(metrics.get("likes", 0)), len(self.state.barrage_entries) * 120),
            }
        )
        if overrides:
            metrics.update(overrides)
        outputs = generate_review_artifacts(
            metrics=metrics,
            barrage_entries=list(reversed(self.state.barrage_entries)),
            products=self.products,
            previous_summary=None,
        )
        timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        output_path = REVIEW_REPORT_DIR / f"{timestamp}-live-bridge-review.md"
        markdown_path, json_path = save_review_outputs(outputs, output_path=output_path)
        with self.lock:
            self.state.record_review(
                markdown=outputs.markdown,
                summary=outputs.summary,
                markdown_path=str(markdown_path.relative_to(ROOT)),
                json_path=str(json_path.relative_to(ROOT)),
            )
        return {
            "markdown_path": str(markdown_path.relative_to(ROOT)),
            "json_path": str(json_path.relative_to(ROOT)),
            "summary": outputs.summary,
        }

    def update_barrage_source_status(self, status: str, detail: str) -> dict[str, object]:
        with self.lock:
            self.state.record_barrage_source_status(status, detail)
            return self.state.integrations["barrage_source"].copy()


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, object]) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _serve_file(handler: BaseHTTPRequestHandler, path: Path) -> None:
    if not path.is_file():
        _json_response(handler, 404, {"ok": False, "error": "File not found"})
        return
    content_type, _ = mimetypes.guess_type(str(path))
    data = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type or "application/octet-stream")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def create_live_studio_handler(service: LiveStudioService) -> type[BaseHTTPRequestHandler]:
    class LiveStudioHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            route = parsed.path
            if route == "/api/health":
                _json_response(self, 200, {"ok": True, "data": {"status": "ok"}})
                return
            if route == "/api/state":
                _json_response(self, 200, {"ok": True, "data": service.snapshot()})
                return
            if route == "/api/integrations/aigcpanel/result-file":
                params = parse_qs(parsed.query, keep_blank_values=False)
                path_text = str((params.get("path") or [""])[0] or "")
                try:
                    target = service.resolve_aigcpanel_result_file(path_text)
                except ValueError as exc:
                    _json_response(self, 400, {"ok": False, "error": str(exc)})
                    return
                _serve_file(self, target)
                return
            if route == "/":
                _serve_file(self, LIVE_STUDIO_APP_DIR / "index.html")
                return
            if route.startswith("/media/"):
                relative = Path(unquote(route.removeprefix("/media/")))
                target = ROOT / relative
                try:
                    target.resolve().relative_to(ROOT.resolve())
                except ValueError:
                    _json_response(self, 403, {"ok": False, "error": "Forbidden media path"})
                    return
                _serve_file(self, target)
                return

            static_target = LIVE_STUDIO_APP_DIR / route.lstrip("/")
            try:
                static_target.resolve().relative_to(LIVE_STUDIO_APP_DIR.resolve())
            except ValueError:
                _json_response(self, 403, {"ok": False, "error": "Forbidden app path"})
                return
            if static_target.is_file():
                _serve_file(self, static_target)
                return
            _json_response(self, 404, {"ok": False, "error": "Not found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            route = parsed.path
            payload = self._read_json()
            try:
                if route == "/api/session/start":
                    state = service.start_session(
                        product_query=str(payload.get("product") or service.config.session.product_query),
                        host_name=str(payload.get("host_name") or service.config.session.host_name),
                        next_live_time=str(payload.get("next_live_time") or service.config.session.next_live_time),
                        room_title=str(payload.get("room_title") or service.config.session.room_title),
                    )
                    _json_response(self, 200, {"ok": True, "data": state})
                    return
                if route == "/api/demo/load":
                    _json_response(self, 200, {"ok": True, "data": service.load_demo_stream()})
                    return
                if route == "/api/barrage":
                    normalized = payload
                    if "message" not in payload:
                        normalized = normalize_barrage_event(
                            payload,
                            format_name=str(payload.get("source_format") or service.config.barrage_source.format_name),
                        )
                    decision = service.process_barrage(normalized)
                    _json_response(self, 200, {"ok": True, "data": decision})
                    return
                if route == "/api/broadcast/manual":
                    _json_response(
                        self,
                        200,
                        {
                            "ok": True,
                            "data": service.broadcast_text(
                                text=str(payload.get("text") or ""),
                                speaker=str(payload.get("speaker") or ""),
                            ),
                        },
                    )
                    return
                if route == "/api/barrage/reply":
                    _json_response(
                        self,
                        200,
                        {
                            "ok": True,
                            "data": service.reply_to_barrage(
                                user=str(payload.get("user") or ""),
                                message=str(payload.get("message") or ""),
                                reply=str(payload.get("reply") or ""),
                                category=str(payload.get("category") or "MANUAL"),
                            ),
                        },
                    )
                    return
                if route == "/api/review":
                    report = service.generate_review(payload)
                    _json_response(self, 200, {"ok": True, "data": report})
                    return
                if route == "/api/integrations/feishu/test":
                    _json_response(self, 200, {"ok": True, "data": service.test_feishu()})
                    return
                if route == "/api/integrations/aigcpanel/ping":
                    _json_response(self, 200, {"ok": True, "data": service.ping_aigcpanel()})
                    return
                if route == "/api/integrations/aigcpanel/submit":
                    _json_response(
                        self,
                        200,
                        {"ok": True, "data": service.submit_to_aigcpanel(text=str(payload.get("text") or "").strip() or None)},
                    )
                    return
                if route == "/api/integrations/aigcpanel/query":
                    _json_response(self, 200, {"ok": True, "data": service.query_aigcpanel(token=str(payload.get("token") or "").strip() or None)})
                    return
                if route == "/api/integrations/aigcpanel/cancel":
                    _json_response(self, 200, {"ok": True, "data": service.cancel_aigcpanel()})
                    return
                if route == "/api/integrations/barrage/heartbeat":
                    status = str(payload.get("status") or "connected")
                    detail = str(payload.get("detail") or "外部弹幕源已联通")
                    _json_response(
                        self,
                        200,
                        {"ok": True, "data": service.update_barrage_source_status(status, detail)},
                    )
                    return
            except ValueError as exc:
                _json_response(self, 400, {"ok": False, "error": str(exc)})
                return
            _json_response(self, 404, {"ok": False, "error": "Not found"})

        def _read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                return {}
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            if not body.strip():
                return {}
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object.")
            return {str(key): value for key, value in payload.items()}

    return LiveStudioHandler


def create_live_studio_server(
    host: str,
    port: int,
    service: LiveStudioService,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), create_live_studio_handler(service))
    server.daemon_threads = True
    return server
