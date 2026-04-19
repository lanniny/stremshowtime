#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "product-catalog" / "products.json"
TARGETS = [
    ROOT / "skills" / "livestream-script" / "references" / "products.json",
    ROOT / "skills" / "barrage-responder" / "references" / "products.json",
]


def load_catalog() -> list[object]:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Canonical catalog not found: {SOURCE}")

    with SOURCE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_catalog(data: list[object]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def check_targets(expected_text: str) -> int:
    mismatches: list[Path] = []
    for target in TARGETS:
        if not target.is_file():
            mismatches.append(target)
            continue
        if target.read_text(encoding="utf-8") != expected_text:
            mismatches.append(target)

    if mismatches:
        print("Out-of-sync product catalog mirrors:")
        for path in mismatches:
            print(f" - {path.relative_to(ROOT)}")
        return 1

    print("All product catalog mirrors are in sync.")
    return 0


def sync_targets(expected_text: str) -> int:
    for target in TARGETS:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(expected_text, encoding="utf-8")
        print(f"Synced {target.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync the canonical product catalog into skill-local mirrors."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that skill-local mirrors match the canonical catalog.",
    )
    args = parser.parse_args()

    try:
        catalog = load_catalog()
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    expected_text = render_catalog(catalog)

    if args.check:
        return check_targets(expected_text)

    return sync_targets(expected_text)


if __name__ == "__main__":
    raise SystemExit(main())
