from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

from .catalog import Product


def _cap_list(items: list[dict[str, object]], entry: dict[str, object], limit: int) -> None:
    items.insert(0, entry)
    del items[limit:]


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass(slots=True)
class LiveSessionState:
    room_title: str
    session_status: str = "idle"
    session_id: str | None = None
    started_at: str | None = None
    host_name: str = ""
    next_live_time: str = ""
    selected_product_query: str = ""
    product_id: str | None = None
    product_name: str | None = None
    script_text: str = ""
    media: dict[str, str] = field(default_factory=dict)
    current_reply: dict[str, object] | None = None
    reply_history: list[dict[str, object]] = field(default_factory=list)
    barrage_entries: list[dict[str, object]] = field(default_factory=list)
    alerts: list[dict[str, object]] = field(default_factory=list)
    review: dict[str, object] = field(default_factory=dict)
    integrations: dict[str, dict[str, object]] = field(default_factory=dict)
    stats: dict[str, object] = field(default_factory=dict)
    recent_errors: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, room_title: str, media: dict[str, str]) -> "LiveSessionState":
        return cls(
            room_title=room_title,
            media=media,
            integrations={
                "feishu": {
                    "configured": False,
                    "last_alert_status": "idle",
                    "last_test_status": "idle",
                    "last_test_time": None,
                },
                "aigcpanel": {
                    "enabled": False,
                    "ready": False,
                    "base_url": "",
                    "resolved_entry": "",
                    "last_action": "idle",
                    "last_token": None,
                    "last_status": "idle",
                    "last_message": "",
                    "last_logs": "",
                    "last_media_url": "",
                    "last_media_kind": "",
                    "last_local_path": "",
                    "last_remote_config": {},
                    "last_result_data": {},
                    "last_artifacts": [],
                },
                "barrage_source": {
                    "websocket_url": "",
                    "format": "",
                    "last_status": "idle",
                    "last_detail": "",
                    "last_event_at": None,
                },
            },
            stats={
                "barrages": 0,
                "replies": 0,
                "alerts": 0,
                "comments": 0,
                "likes": 0,
                "product_clicks": 0,
                "orders": 0,
                "sales_amount": 0.0,
            },
        )

    def update_integration_flags(
        self,
        *,
        feishu_configured: bool,
        aigcpanel_enabled: bool,
        aigcpanel_ready: bool,
        aigcpanel_base_url: str,
        barrage_websocket_url: str,
        barrage_format: str,
    ) -> None:
        self.integrations["feishu"]["configured"] = feishu_configured
        self.integrations["aigcpanel"]["enabled"] = aigcpanel_enabled
        self.integrations["aigcpanel"]["ready"] = aigcpanel_ready
        self.integrations["aigcpanel"]["base_url"] = aigcpanel_base_url
        self.integrations["barrage_source"]["websocket_url"] = barrage_websocket_url
        self.integrations["barrage_source"]["format"] = barrage_format

    def start_session(
        self,
        *,
        product: Product,
        product_query: str,
        host_name: str,
        next_live_time: str,
        room_title: str,
        script_text: str,
        now: datetime,
    ) -> None:
        self.room_title = room_title
        self.session_status = "live"
        self.session_id = now.strftime("%Y%m%d-%H%M%S")
        self.started_at = now.isoformat(timespec="seconds")
        self.host_name = host_name
        self.next_live_time = next_live_time
        self.selected_product_query = product_query
        self.product_id = product.id
        self.product_name = product.name
        self.script_text = script_text
        self.current_reply = None
        self.reply_history.clear()
        self.barrage_entries.clear()
        self.alerts.clear()
        self.review = {}
        self.recent_errors.clear()
        self.stats.update(
            {
                "barrages": 0,
                "replies": 0,
                "alerts": 0,
                "comments": 0,
                "likes": 0,
                "product_clicks": 0,
                "orders": 0,
                "sales_amount": 0.0,
            }
        )
        self.integrations["aigcpanel"].update(
            {
                "last_action": "idle",
                "last_token": None,
                "last_status": "idle",
                "last_message": "",
                "last_logs": "",
                "last_media_url": "",
                "last_media_kind": "",
                "last_local_path": "",
                "last_result_data": {},
                "last_artifacts": [],
            }
        )
        self.integrations["barrage_source"].update(
            {
                "last_status": "waiting",
                "last_detail": "等待弹幕源接入",
                "last_event_at": None,
            }
        )

    def add_error(self, message: str) -> None:
        clean = message.strip()
        if not clean:
            return
        self.recent_errors.insert(0, clean)
        del self.recent_errors[8:]

    def record_barrage(self, payload: dict[str, object]) -> None:
        _cap_list(self.barrage_entries, payload, limit=40)
        self.stats["barrages"] = len(self.barrage_entries)
        self.stats["comments"] = len(self.barrage_entries)
        self.integrations["barrage_source"]["last_status"] = "receiving"
        self.integrations["barrage_source"]["last_detail"] = "最近一条弹幕已入桥"
        self.integrations["barrage_source"]["last_event_at"] = str(payload.get("timestamp") or "")

        reply_text = str(payload.get("reply") or "").strip()
        if reply_text:
            current_reply = {
                "user": str(payload.get("user") or "匿名用户"),
                "category": str(payload.get("category") or ""),
                "reply": reply_text,
                "tts_text": str(payload.get("tts_text") or reply_text),
                "timestamp": str(payload.get("timestamp") or ""),
            }
            self.current_reply = current_reply
            _cap_list(self.reply_history, current_reply, limit=20)
            self.stats["replies"] = len(self.reply_history)

        if bool(payload.get("alert_required")):
            alert_entry = {
                "user": str(payload.get("user") or "匿名用户"),
                "message": str(payload.get("message") or ""),
                "status": str(payload.get("alert_status") or "unknown"),
                "timestamp": str(payload.get("timestamp") or ""),
            }
            _cap_list(self.alerts, alert_entry, limit=20)
            self.stats["alerts"] = len(self.alerts)
            self.integrations["feishu"]["last_alert_status"] = alert_entry["status"]

    def record_manual_broadcast(
        self,
        text: str,
        *,
        speaker: str = "主播",
        source: str = "manual_broadcast",
    ) -> dict[str, object]:
        timestamp = _now_iso()
        current_reply = {
            "user": speaker,
            "category": "MANUAL",
            "reply": text,
            "tts_text": text,
            "timestamp": timestamp,
            "source": source,
        }
        self.current_reply = current_reply
        _cap_list(self.reply_history, current_reply, limit=20)
        self.stats["replies"] = len(self.reply_history)
        return current_reply

    def record_manual_reply(
        self,
        *,
        user: str,
        message: str,
        reply: str,
        category: str = "MANUAL",
    ) -> dict[str, object]:
        payload = {
            "user": user or "匿名用户",
            "message": message,
            "product_id": self.product_id or "",
            "product_name": self.product_name or "",
            "category": category,
            "reply": reply,
            "tts_text": reply,
            "alert_required": False,
            "alert_status": "not_required",
            "timestamp": _now_iso(),
            "source": "manual_reply",
        }
        self.record_barrage(payload)
        return payload

    def record_review(
        self,
        *,
        markdown: str,
        summary: dict[str, object],
        markdown_path: str,
        json_path: str,
    ) -> None:
        self.review = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "markdown": markdown,
            "summary": summary,
            "markdown_path": markdown_path,
            "json_path": json_path,
        }
        metrics = summary.get("metrics", {}) if isinstance(summary, dict) else {}
        if isinstance(metrics, dict):
            for field in ("likes", "product_clicks", "orders", "sales_amount", "comments"):
                if field in metrics:
                    self.stats[field] = metrics[field]

    def record_feishu_test(self, status: str, message: str) -> None:
        self.integrations["feishu"]["last_test_status"] = status
        self.integrations["feishu"]["last_test_time"] = datetime.now().astimezone().isoformat(timespec="seconds")
        self.integrations["feishu"]["last_message"] = message

    def record_aigcpanel_result(self, result: dict[str, object]) -> None:
        token = result.get("token")
        status = str(result.get("status") or result.get("message") or "unknown")
        self.integrations["aigcpanel"]["last_action"] = str(result.get("action") or "unknown")
        self.integrations["aigcpanel"]["last_status"] = status
        self.integrations["aigcpanel"]["last_message"] = str(result.get("message") or "")
        self.integrations["aigcpanel"]["last_logs"] = str(result.get("logs") or "")
        if result.get("base_url"):
            self.integrations["aigcpanel"]["base_url"] = str(result.get("base_url") or "")
        resolved_launcher = result.get("resolved_launcher")
        if isinstance(resolved_launcher, dict):
            self.integrations["aigcpanel"]["resolved_entry"] = str(resolved_launcher.get("entry") or "")
        remote_config = result.get("remote_config")
        if isinstance(remote_config, dict):
            self.integrations["aigcpanel"]["last_remote_config"] = remote_config
        result_data = result.get("result_data")
        if isinstance(result_data, dict):
            self.integrations["aigcpanel"]["last_result_data"] = result_data
        artifacts = result.get("artifacts")
        if isinstance(artifacts, list):
            self.integrations["aigcpanel"]["last_artifacts"] = artifacts
        if result.get("media_url"):
            self.integrations["aigcpanel"]["last_media_url"] = str(result.get("media_url") or "")
        if result.get("media_kind"):
            self.integrations["aigcpanel"]["last_media_kind"] = str(result.get("media_kind") or "")
        if result.get("local_path"):
            self.integrations["aigcpanel"]["last_local_path"] = str(result.get("local_path") or "")
        if token:
            self.integrations["aigcpanel"]["last_token"] = str(token)

    def record_barrage_source_status(self, status: str, detail: str) -> None:
        self.integrations["barrage_source"]["last_status"] = status
        self.integrations["barrage_source"]["last_detail"] = detail
        self.integrations["barrage_source"]["last_event_at"] = datetime.now().astimezone().isoformat(timespec="seconds")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
