import json
import logging
from pathlib import Path

from app.config.settings import get_settings
from app.services.bedrock_service import BedrockService
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


class ProductDetector:
    def __init__(self, s3: S3Service, bedrock: BedrockService):
        self.s3 = s3
        self.bedrock = bedrock

    def detect_from_frame_s3(self, bucket: str, key: str) -> dict:
        img_bytes = self.s3.download_bytes(bucket, key)
        result = self.bedrock.detect_products_json(img_bytes, media_type="image/jpeg")
        return result


def detect_products(
    frame_keys: list[str],
    bedrock_service: BedrockService,
    s3_service: S3Service | None = None,
) -> list[dict]:
    """
    Supports:
    - Local file paths
    - S3 keys
    """

    settings = get_settings()

    if s3_service is None:
        s3_service = S3Service(settings)

    all_products = []

    logger.info("=" * 60)
    logger.info("PRODUCT DETECTION — Starting detection on %d frames", len(frame_keys))
    logger.info("=" * 60)

    for frame_idx, key in enumerate(frame_keys, start=1):
        try:
            # -------- LOAD FRAME --------
            if Path(key).exists():
                with open(key, "rb") as f:
                    img_bytes = f.read()
                source = "LOCAL"
            else:
                img_bytes = s3_service.download_bytes(
                    settings.s3_bucket, key
                )
                source = "S3"

            logger.info(
                "[DETECT] Frame %d/%d — source=%s path=%s size=%d bytes (%.1f KB)",
                frame_idx, len(frame_keys), source, key,
                len(img_bytes), len(img_bytes) / 1024,
            )

            # -------- SEND TO VISION MODEL --------
            logger.info(
                "[DETECT] Sending frame to vision model (Nova Pro → Claude fallback)..."
            )
            result = bedrock_service.detect_products_json(
                img_bytes,
                media_type="image/jpeg",
            )

            products_found = result.get("products", [])
            logger.info(
                "[DETECT] Frame %d/%d — Model returned %d products",
                frame_idx, len(frame_keys), len(products_found),
            )

            # Log each detected product
            for p_idx, p in enumerate(products_found, start=1):
                logger.info(
                    "[DETECT]   Product %d: brand=%s name=%s weight=%s mrp=%s "
                    "confidence=%.2f bbox=%s",
                    p_idx,
                    p.get("brand"),
                    p.get("product_name"),
                    p.get("net_weight"),
                    p.get("mrp"),
                    p.get("confidence", 0),
                    p.get("bbox"),
                )
                p["frame_key"] = key
                all_products.append(p)

            # Log raw JSON for debugging (truncated)
            raw_json = json.dumps(result, indent=2, default=str)
            if len(raw_json) > 2000:
                raw_json = raw_json[:2000] + "\n... (truncated)"
            logger.info("[DETECT] Raw model response:\n%s", raw_json)

        except Exception as e:
            logger.error("[DETECT ERROR] Frame %d/%d key=%s: %s",
                         frame_idx, len(frame_keys), key, e)
            continue

    logger.info("=" * 60)
    logger.info(
        "PRODUCT DETECTION — Complete. Total products from all frames: %d",
        len(all_products),
    )
    logger.info("=" * 60)

    return all_products
