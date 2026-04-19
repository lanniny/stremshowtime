#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import json
import os
import sys


ROOT = Path(__file__).resolve().parents[3]
LIB_ROOT = ROOT / "scripts"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from showman_runtime.barrage import process_single_barrage
from showman_runtime.catalog import load_products, match_product
from showman_runtime.paths import CANONICAL_CATALOG


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify barrage messages and generate replies.")
    parser.add_argument(
        "--product",
        help="Current livestream product. Required when the catalog contains multiple products.",
    )
    parser.add_argument("--message", help="Single barrage message to process.")
    parser.add_argument("--user", default="匿名用户", help="Nickname for the barrage sender.")
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        help="Optional batch input JSONL file. Each line should contain {user, message, product}.",
    )
    parser.add_argument(
        "--webhook-url",
        help="Optional Feishu webhook URL. Falls back to FEISHU_WEBHOOK_URL when omitted.",
    )
    parser.add_argument(
        "--catalog-file",
        type=Path,
        default=CANONICAL_CATALOG,
        help="Path to the canonical product catalog JSON file.",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        help="Optional batch output JSONL path. Defaults to stdout.",
    )
    return parser.parse_args()


def _write_batch_output(output_path: Path | None, results: list[dict[str, object]]) -> None:
    lines = [json.dumps(result, ensure_ascii=False) for result in results]
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Saved batch results to {output_path}")
        return
    for line in lines:
        print(line)


def main() -> int:
    args = parse_args()
    if not args.message and not args.input_jsonl:
        print("Provide either --message or --input-jsonl.", file=sys.stderr)
        return 1

    try:
        products = load_products(args.catalog_file)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    webhook_url = args.webhook_url or os.environ.get("FEISHU_WEBHOOK_URL")

    if args.message:
        try:
            product = match_product(products, args.product)
            decision, log_path = process_single_barrage(
                product=product,
                user=args.user,
                message=args.message,
                webhook_url=webhook_url,
            )
        except (OSError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

        payload = asdict(decision)
        payload["log_path"] = str(log_path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    results: list[dict[str, object]] = []
    assert args.input_jsonl is not None
    try:
        with args.input_jsonl.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if not isinstance(item, dict):
                    continue
                product_query = str(item.get("product") or args.product or "")
                user = str(item.get("user") or args.user)
                message = str(item.get("message") or "")
                product = match_product(products, product_query)
                decision, log_path = process_single_barrage(
                    product=product,
                    user=user,
                    message=message,
                    webhook_url=webhook_url,
                )
                payload = asdict(decision)
                payload["log_path"] = str(log_path)
                results.append(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _write_batch_output(args.output_jsonl, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
