from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIB_ROOT = ROOT / "scripts"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from showman_runtime.barrage import classify_barrage_message, process_single_barrage
from showman_runtime.catalog import load_products, match_product
from showman_runtime.review import generate_review_artifacts, save_review_outputs
from showman_runtime.script_writer import build_livestream_script


class CatalogTests(unittest.TestCase):
    def test_match_product_by_partial_name(self) -> None:
        products = load_products(ROOT / "data" / "product-catalog" / "products.json")
        product = match_product(products, "果汁饮料")
        self.assertEqual(product.id, "sanghen-juice-01")

    def test_match_product_requires_query_when_ambiguous(self) -> None:
        products = load_products(ROOT / "data" / "product-catalog" / "products.json")
        with self.assertRaises(ValueError):
            match_product(products, "一川桑语")


class ScriptWriterTests(unittest.TestCase):
    def test_generated_script_contains_five_sections(self) -> None:
        product = match_product(
            load_products(ROOT / "data" / "product-catalog" / "products.json"),
            "果汁饮料",
        )
        script = build_livestream_script(product, host_name="主播小桑", next_live_time="周五晚上8点")
        self.assertIn("环节① 开场预热", script)
        self.assertIn("环节⑤ 下播预告", script)
        self.assertIn("22.8元/2瓶", script)
        self.assertIn("主播小桑", script)


class BarrageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.product = match_product(
            load_products(ROOT / "data" / "product-catalog" / "products.json"),
            "果汁饮料",
        )

    def test_classification_keywords(self) -> None:
        self.assertEqual(classify_barrage_message("多少钱？"), "A")
        self.assertEqual(classify_barrage_message("已拍，加急发货"), "B")
        self.assertEqual(classify_barrage_message("讲得真好"), "C")
        self.assertEqual(classify_barrage_message("质量太差了"), "D")
        self.assertEqual(classify_barrage_message("http://spam.example"), "E")

    def test_process_single_barrage_logs_and_requires_alert(self) -> None:
        log_dir = ROOT / "data" / "barrage-logs"
        log_path = log_dir / "2026-04-19-barrage.jsonl"
        if log_path.exists():
            log_path.unlink()

        decision, written_log_path = process_single_barrage(
            product=self.product,
            user="测试用户",
            message="质量太差了",
            webhook_url=None,
            now=datetime.fromisoformat("2026-04-19T20:00:00+08:00"),
            log_dir=log_dir,
        )
        self.assertEqual(decision.category, "D")
        self.assertTrue(decision.alert_required)
        self.assertEqual(decision.alert_status, "missing_webhook")
        self.assertTrue(written_log_path.is_file())

        written_log_path.unlink(missing_ok=True)


class ReviewTests(unittest.TestCase):
    def test_generate_and_save_review_outputs(self) -> None:
        products = load_products(ROOT / "data" / "product-catalog" / "products.json")
        metrics = {
            "session_date": "2026-04-19",
            "product_name": "一川桑语 NFC60%桑葚复合果汁饮料",
            "host_name": "主播小桑",
            "duration_minutes": 90,
            "total_views": 3200,
            "peak_online": 420,
            "new_followers": 68,
            "comments": 126,
            "likes": 1880,
            "product_clicks": 214,
            "orders": 16,
            "sales_amount": 364.8,
        }
        barrage_entries = [
            {"category": "A", "message": "多少钱", "user": "A"},
            {"category": "A", "message": "保质期多久", "user": "B"},
            {"category": "B", "message": "已拍", "user": "C"},
            {"category": "D", "message": "物流太慢", "user": "D", "alert_status": "sent:200"},
        ]

        outputs = generate_review_artifacts(metrics, barrage_entries, products)
        self.assertIn("# 直播复盘报告", outputs.markdown)
        self.assertIn("多少钱", outputs.markdown)
        self.assertEqual(outputs.summary["barrage_counts"]["D"], 1)

        report_dir = ROOT / "data" / "review-reports"
        markdown_path = report_dir / "unit-test-review.md"
        json_path = report_dir / "unit-test-review.json"
        if markdown_path.exists():
            markdown_path.unlink()
        if json_path.exists():
            json_path.unlink()

        saved_markdown_path, saved_json_path = save_review_outputs(
            outputs,
            output_path=markdown_path,
        )
        self.assertTrue(saved_markdown_path.is_file())
        self.assertTrue(saved_json_path.is_file())
        payload = json.loads(saved_json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["product_name"], metrics["product_name"])

        saved_markdown_path.unlink(missing_ok=True)
        saved_json_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
