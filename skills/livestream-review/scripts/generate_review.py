#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[3]
LIB_ROOT = ROOT / "scripts"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from showman_runtime.catalog import load_products, match_product
from showman_runtime.paths import BARRAGE_LOG_DIR, CANONICAL_CATALOG, REVIEW_REPORT_DIR
from showman_runtime.review import (
    METRIC_FIELDS,
    ReviewOutputs,
    generate_review_artifacts,
    load_barrage_entries,
    save_review_outputs,
    _find_previous_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a livestream review report.")
    parser.add_argument("--metrics-file", type=Path, help="JSON file containing session metrics.")
    parser.add_argument("--product", help="Current product name, id, or keyword.")
    parser.add_argument("--host-name", default="主播", help="Host name used in the report.")
    parser.add_argument("--session-date", help="Report date in YYYY-MM-DD format.")
    parser.add_argument("--barrage-log", type=Path, help="Specific barrage log JSONL file.")
    parser.add_argument(
        "--catalog-file",
        type=Path,
        default=CANONICAL_CATALOG,
        help="Path to the canonical product catalog JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional markdown output path. Defaults to data/review-reports/YYYY-MM-DD-review.md",
    )
    parser.add_argument("--duration-minutes", type=float)
    parser.add_argument("--total-views", type=int)
    parser.add_argument("--peak-online", type=int)
    parser.add_argument("--new-followers", type=int)
    parser.add_argument("--comments", type=int)
    parser.add_argument("--likes", type=int)
    parser.add_argument("--product-clicks", type=int)
    parser.add_argument("--orders", type=int)
    parser.add_argument("--sales-amount", type=float)
    return parser.parse_args()


def _load_metrics_file(path: Path | None) -> dict[str, object]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Metrics file must contain a JSON object: {path}")
    return data


def _merge_metrics(args: argparse.Namespace) -> dict[str, object]:
    metrics = _load_metrics_file(args.metrics_file)
    for field in METRIC_FIELDS:
        cli_value = getattr(args, field)
        if cli_value is not None:
            metrics[field] = cli_value

    if args.session_date:
        metrics["session_date"] = args.session_date
    if args.host_name:
        metrics["host_name"] = args.host_name
    return metrics


def main() -> int:
    args = parse_args()

    try:
        products = load_products(args.catalog_file)
        selected_product = match_product(products, args.product) if args.product else None
        metrics = _merge_metrics(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if selected_product:
        metrics.setdefault("product_name", selected_product.name)
    metrics.setdefault("host_name", args.host_name)

    try:
        barrage_entries = load_barrage_entries(args.barrage_log, log_dir=BARRAGE_LOG_DIR)
        previous_summary = _find_previous_summary(
            REVIEW_REPORT_DIR,
            str(metrics.get("session_date") or ""),
            str(metrics.get("product_name") or ""),
        )
        outputs: ReviewOutputs = generate_review_artifacts(
            metrics=metrics,
            barrage_entries=barrage_entries,
            products=products,
            previous_summary=previous_summary,
        )
        markdown_path, json_path = save_review_outputs(outputs, output_path=args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Saved markdown report to {markdown_path}")
    print(f"Saved structured summary to {json_path}")
    print(outputs.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
