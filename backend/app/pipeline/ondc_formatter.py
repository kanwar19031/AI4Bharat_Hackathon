from datetime import datetime, timezone


def format_ondc_catalog(video_id: str, products: list[dict]) -> dict:
    return {
        "context": {
            "domain": "ONDC:RET10",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_id": video_id,
        },
        "message": {"catalog": {"providers": [{"items": products}]}},
    }

