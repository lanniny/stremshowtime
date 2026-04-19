from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .paths import CANONICAL_CATALOG


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", (text or "")).lower()


def _chunk_query(text: str) -> set[str]:
    normalized = normalize_text(text)
    chunks: set[str] = set()
    if not normalized:
        return chunks

    if len(normalized) <= 2:
        chunks.add(normalized)
        return chunks

    for start in range(len(normalized) - 1):
        chunks.add(normalized[start : start + 2])
    return chunks


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _string_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key).strip(): str(item).strip()
        for key, item in value.items()
        if str(key).strip() and str(item).strip()
    }


def _link_list(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    links: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            normalized = {
                str(key).strip(): str(val).strip()
                for key, val in item.items()
                if str(key).strip() and str(val).strip()
            }
            if normalized:
                links.append(normalized)
            continue

        text = str(item).strip()
        if text:
            links.append({"label": "商品链接", "url": text, "copy_text": text})

    return links


@dataclass(slots=True)
class Product:
    id: str
    name: str
    brand: str | None = None
    category: str | None = None
    selling_points: list[str] = field(default_factory=list)
    regular_price: str | None = None
    live_price: str | None = None
    per_unit_price: str | None = None
    gifts: str | None = None
    specs: dict[str, str] = field(default_factory=dict)
    ingredients: str | None = None
    stock: int | None = None
    pain_points: list[str] = field(default_factory=list)
    story: str | None = None
    competitors: list[dict[str, str]] = field(default_factory=list)
    purchase_links: list[dict[str, str]] = field(default_factory=list)
    faq: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Product":
        stock_value = data.get("stock")
        stock: int | None
        if isinstance(stock_value, int):
            stock = stock_value
        elif isinstance(stock_value, str) and stock_value.strip().isdigit():
            stock = int(stock_value.strip())
        else:
            stock = None

        competitors = []
        raw_competitors = data.get("competitors")
        if isinstance(raw_competitors, list):
            for item in raw_competitors:
                if isinstance(item, dict):
                    normalized = {
                        str(key).strip(): str(val).strip()
                        for key, val in item.items()
                        if str(key).strip() and str(val).strip()
                    }
                    if normalized:
                        competitors.append(normalized)

        return cls(
            id=_optional_text(data.get("id")) or "",
            name=_optional_text(data.get("name")) or "",
            brand=_optional_text(data.get("brand")),
            category=_optional_text(data.get("category")),
            selling_points=_string_list(data.get("selling_points")),
            regular_price=_optional_text(data.get("regular_price")),
            live_price=_optional_text(data.get("live_price")),
            per_unit_price=_optional_text(data.get("per_unit_price")),
            gifts=_optional_text(data.get("gifts")),
            specs=_string_map(data.get("specs")),
            ingredients=_optional_text(data.get("ingredients")),
            stock=stock,
            pain_points=_string_list(data.get("pain_points")),
            story=_optional_text(data.get("story")),
            competitors=competitors,
            purchase_links=_link_list(data.get("purchase_links")),
            faq=_string_map(data.get("faq")),
        )

    def search_terms(self) -> set[str]:
        terms = {
            normalize_text(self.id),
            normalize_text(self.name),
            normalize_text(self.brand or ""),
            normalize_text(self.category or ""),
        }
        terms.update(normalize_text(point) for point in self.selling_points[:2])
        return {term for term in terms if term}

    @property
    def primary_link_label(self) -> str:
        if self.purchase_links:
            return self.purchase_links[0].get("label", "小黄车")
        return "小黄车"

    def spec_value(self, key: str) -> str | None:
        return self.specs.get(key)


def load_products(catalog_path: Path | None = None) -> list[Product]:
    path = catalog_path or CANONICAL_CATALOG
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError(f"Catalog must be a list of products: {path}")

    products = [Product.from_dict(item) for item in data if isinstance(item, dict)]
    if not products:
        raise ValueError(f"No products found in catalog: {path}")

    return products


def match_product(products: list[Product], query: str | None) -> Product:
    if not query:
        if len(products) == 1:
            return products[0]
        names = ", ".join(product.name for product in products)
        raise ValueError(f"Multiple products available. Please specify one of: {names}")

    normalized_query = normalize_text(query)

    exact_matches = [
        product
        for product in products
        if normalized_query in {normalize_text(product.id), normalize_text(product.name)}
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        names = ", ".join(product.name for product in exact_matches)
        raise ValueError(f"Ambiguous product query '{query}'. Matches: {names}")

    partial_matches = [
        product
        for product in products
        if any(normalized_query and normalized_query in term for term in product.search_terms())
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        names = ", ".join(product.name for product in partial_matches)
        raise ValueError(f"Ambiguous product query '{query}'. Matches: {names}")

    query_chunks = _chunk_query(query)
    chunk_matches = [
        product
        for product in products
        if query_chunks
        and any(
            chunk in normalize_text(product.name) or chunk in normalize_text(product.category or "")
            for chunk in query_chunks
        )
    ]
    if len(chunk_matches) == 1:
        return chunk_matches[0]
    if len(chunk_matches) > 1:
        names = ", ".join(product.name for product in chunk_matches)
        raise ValueError(f"Ambiguous product query '{query}'. Matches: {names}")

    names = ", ".join(product.name for product in products)
    raise ValueError(f"Product '{query}' not found. Available products: {names}")
