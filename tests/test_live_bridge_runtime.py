from __future__ import annotations

import base64
from pathlib import Path
import json
import sys
import threading
import unittest
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
LIB_ROOT = ROOT / "scripts"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from showman_runtime.aigcpanel import build_aigcpanel_submit_payload, parse_aigcpanel_query_logs
from showman_runtime.barrage_source import normalize_barrage_event
from showman_runtime.live_bridge import LiveStudioService, create_live_studio_server
from showman_runtime.live_config import load_live_bridge_config


EXAMPLE_CONFIG_PATH = ROOT / "config" / "live-bridge.example.json"


class LiveConfigTests(unittest.TestCase):
    def test_load_live_bridge_config_resolves_env_webhook(self) -> None:
        config_path = ROOT / "data" / "test-live-bridge-config.json"
        config_path.write_text(
            json.dumps({"integrations": {"feishu": {"webhook_env": "MY_FEISHU_URL"}}}),
            encoding="utf-8",
        )
        try:
            config = load_live_bridge_config(
                config_path,
                env={"MY_FEISHU_URL": "https://example.com/feishu-hook"},
            )
            self.assertEqual(
                config.feishu.resolved_webhook_url({"MY_FEISHU_URL": "https://example.com/feishu-hook"}),
                "https://example.com/feishu-hook",
            )
        finally:
            config_path.unlink(missing_ok=True)

    def test_aigcpanel_ready_requires_explicit_entry(self) -> None:
        config = load_live_bridge_config(EXAMPLE_CONFIG_PATH)
        config.aigcpanel.enabled = True
        config.aigcpanel.entry = None
        self.assertFalse(config.aigcpanel.ready)


class AIGCPanelPayloadTests(unittest.TestCase):
    def test_build_submit_payload_keeps_launcher_contract(self) -> None:
        config = load_live_bridge_config(EXAMPLE_CONFIG_PATH)
        config.aigcpanel.enabled = True
        config.aigcpanel.entry = "python"
        config.aigcpanel.entry_args = [
            "worker.py",
            "--text",
            "${TEXT}",
            "--host",
            "${HOST_NAME}",
        ]
        config.aigcpanel.entry_placeholders = {"VOICE_NAME": "主播小桑"}
        config.aigcpanel.envs = {"SHOWMAN_ROOM_TITLE": "${ROOM_TITLE}"}
        payload = build_aigcpanel_submit_payload(
            config.aigcpanel,
            "欢迎来到直播间",
            context={"host_name": "主播小桑", "room_title": "测试直播间"},
        )
        self.assertEqual(payload["entry"], "python")
        self.assertEqual(payload["entryArgs"][1], "--text")
        self.assertEqual(payload["entryPlaceholders"]["TEXT"], "欢迎来到直播间")
        self.assertEqual(payload["entryPlaceholders"]["HOST_NAME"], "主播小桑")
        self.assertEqual(payload["envs"]["SHOWMAN_ROOM_TITLE"], "测试直播间")

    def test_parse_query_logs_extracts_media_artifact(self) -> None:
        result_json = json.dumps(
            {"audio": "C:\\Users\\demo\\AppData\\Roaming\\aigcpanel\\cache\\reply.wav"},
            ensure_ascii=False,
        ).encode("utf-8")
        encoded = base64.b64encode(result_json).decode("ascii")
        parsed = parse_aigcpanel_query_logs(
            f"prefix AigcPanelRunResult[test][{encoded}] suffix",
            base_url="http://127.0.0.1:8888",
        )
        self.assertEqual(parsed["media_kind"], "audio")
        self.assertEqual(
            parsed["local_path"],
            "C:\\Users\\demo\\AppData\\Roaming\\aigcpanel\\cache\\reply.wav",
        )


class BarrageSourceTests(unittest.TestCase):
    def test_normalize_barragegrab_type3_message(self) -> None:
        event = {
            "Type": 3,
            "Data": {
                "User": {"NickName": "观众A"},
                "Content": "多少钱？",
            },
        }
        normalized = normalize_barrage_event(event, "barragegrab_type3")
        self.assertEqual(normalized["user"], "观众A")
        self.assertEqual(normalized["message"], "多少钱？")


class LiveStudioServiceTests(unittest.TestCase):
    def test_process_barrage_updates_live_state(self) -> None:
        config = load_live_bridge_config(EXAMPLE_CONFIG_PATH)
        config.feishu.webhook_url = "https://example.com/mock-feishu"
        service = LiveStudioService(config)
        payload = service.process_barrage(
            {"user": "测试用户", "message": "质量太差了"},
            sender=lambda *args: (True, "sent:200"),
        )
        snapshot = service.snapshot()
        self.assertEqual(payload["category"], "D")
        self.assertEqual(snapshot["stats"]["alerts"], 1)
        self.assertEqual(snapshot["integrations"]["feishu"]["last_alert_status"], "sent:200")

    def test_manual_broadcast_and_manual_reply_update_live_state(self) -> None:
        service = LiveStudioService(load_live_bridge_config(EXAMPLE_CONFIG_PATH))
        broadcast = service.broadcast_text("家人们现在可以直接拍 1 号链接")
        manual_reply = service.reply_to_barrage(
            user="小雨",
            message="还有库存吗？",
            reply="库存还在，喜欢的话现在就可以下单。",
        )
        snapshot = service.snapshot()

        self.assertEqual(broadcast["tts_text"], "家人们现在可以直接拍 1 号链接")
        self.assertEqual(manual_reply["reply"], "库存还在，喜欢的话现在就可以下单。")
        self.assertEqual(snapshot["current_reply"]["tts_text"], "库存还在，喜欢的话现在就可以下单。")
        self.assertEqual(snapshot["barrage_entries"][0]["message"], "还有库存吗？")
        self.assertGreaterEqual(snapshot["stats"]["replies"], 2)

    def test_auto_push_skips_when_aigcpanel_not_preflighted(self) -> None:
        config = load_live_bridge_config(EXAMPLE_CONFIG_PATH)
        config.server.auto_push_replies = True
        config.aigcpanel.enabled = True
        config.aigcpanel.entry = "python"
        service = LiveStudioService(config)

        service.broadcast_text("这条播报先不要阻塞在未联通的 AIGCPanel 上。")
        snapshot = service.snapshot()

        self.assertEqual(snapshot["integrations"]["aigcpanel"]["last_action"], "idle")


class LiveStudioServerTests(unittest.TestCase):
    def test_http_server_serves_index_and_state(self) -> None:
        service = LiveStudioService(load_live_bridge_config(EXAMPLE_CONFIG_PATH))
        server = create_live_studio_server("127.0.0.1", 0, service)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        try:
            with urllib.request.urlopen(f"http://{host}:{port}/api/state", timeout=5) as response:
                payload = json.load(response)
            with urllib.request.urlopen(f"http://{host}:{port}/", timeout=5) as response:
                html = response.read().decode("utf-8", errors="replace")
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertTrue(payload["ok"])
        self.assertIn("data", payload)
        self.assertIn("直播控制台", html)


if __name__ == "__main__":
    unittest.main()
