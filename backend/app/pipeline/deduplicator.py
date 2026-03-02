def _net_weight_key(nw) -> str:
    if isinstance(nw, dict):
        v = nw.get("value")
        u = nw.get("unit")
        if v is None or not u:
            return ""
        return f"{v}{u}".strip().lower()
    return str(nw or "").strip().lower()


def deduplicate_products(products: list[dict]) -> list[dict]:
    deduped: dict[tuple[str, str, str], dict] = {}
    for item in products:
        key = (
            str(item.get("brand", "")).strip().lower(),
            str(item.get("product_name", "")).strip().lower(),
            _net_weight_key(item.get("net_weight")),
        )
        if key not in deduped:
            deduped[key] = item
    return list(deduped.values())

