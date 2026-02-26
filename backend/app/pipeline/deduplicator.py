def deduplicate_products(products: list[dict]) -> list[dict]:
    deduped: dict[tuple[str, str, str], dict] = {}
    for item in products:
        key = (
            str(item.get("brand", "")).strip().lower(),
            str(item.get("product_name", "")).strip().lower(),
            str(item.get("net_weight", "")).strip().lower(),
        )
        if key not in deduped:
            deduped[key] = item
    return list(deduped.values())

