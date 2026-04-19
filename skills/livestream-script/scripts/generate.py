#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
LIB_ROOT = ROOT / "scripts"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from showman_runtime.catalog import load_products, match_product
from showman_runtime.paths import CANONICAL_CATALOG
from showman_runtime.script_writer import build_livestream_script


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a livestream script from product data.")
    parser.add_argument("--product", required=True, help="Product name, id, or keyword.")
    parser.add_argument("--host-name", default="主播小桑", help="Host name used in the script.")
    parser.add_argument(
        "--next-live",
        default="[待确认]",
        help="Next livestream time shown in the closing section.",
    )
    parser.add_argument(
        "--catalog-file",
        type=Path,
        default=CANONICAL_CATALOG,
        help="Path to the canonical product catalog JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional markdown output path. Prints to stdout when omitted.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        products = load_products(args.catalog_file)
        product = match_product(products, args.product)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    script_text = build_livestream_script(
        product=product,
        host_name=args.host_name,
        next_live_time=args.next_live,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(script_text + "\n", encoding="utf-8")
        print(f"Saved script to {args.output}")
    else:
        print(script_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
