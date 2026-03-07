from __future__ import annotations

from typing import Any
from uuid import uuid4


def _net_weight_to_text(net_weight: Any) -> str | None:
    if net_weight is None:
        return None
    if isinstance(net_weight, str):
        text = net_weight.strip()
        return text or None
    if isinstance(net_weight, dict):
        value = net_weight.get("value")
        unit = net_weight.get("unit")
        if value is None or not unit:
            return None
        return f"{value}{unit}"
    return str(net_weight).strip() or None


def _mrp_to_price(mrp: Any) -> float | None:
    if mrp is None:
        return None
    if isinstance(mrp, (int, float)):
        return float(mrp)
    if isinstance(mrp, dict):
        value = mrp.get("value")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    try:
        return float(mrp)
    except (TypeError, ValueError):
        return None


def normalize_catalog_products(products: list[dict]) -> list[dict]:
    """
    Convert Claude-style fields into the API-friendly schema:
    - net_weight (dict) -> net_weight (string like "200g")
    - mrp (dict) -> price (float)
    Keeps original keys too (so we don't lose evidence/bbox/etc).
    """
    normalized: list[dict] = []
    for product in products:
        item = dict(product)

        if not item.get("product_id"):
            item["product_id"] = str(uuid4())

        # Always normalize net_weight — convert dict to string or None
        raw_net_weight = item.get("net_weight")
        if raw_net_weight is not None:
            item["net_weight"] = _net_weight_to_text(raw_net_weight)

        price = _mrp_to_price(item.get("mrp"))
        if price is not None and item.get("price") is None:
            item["price"] = price

        normalized.append(item)
    return normalized
