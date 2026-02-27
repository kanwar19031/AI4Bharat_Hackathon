from pathlib import Path

from app.config.settings import get_settings
from app.services.bedrock_service import BedrockService
from app.services.s3_service import S3Service


class ProductDetector:
    def __init__(self, s3: S3Service, bedrock: BedrockService):
        self.s3 = s3
        self.bedrock = bedrock

    def detect_from_frame_s3(self, bucket: str, key: str) -> dict:
        img_bytes = self.s3.download_bytes(bucket, key)
        result = self.bedrock.claude_detect_products_json(img_bytes, media_type="image/jpeg")
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

    for key in frame_keys:
        try:
            # -------- LOCAL FILE --------
            if Path(key).exists():
                with open(key, "rb") as f:
                    img_bytes = f.read()

            # -------- S3 FILE --------
            else:
                img_bytes = s3_service.download_bytes(
                    settings.s3_frames_bucket, key
                )

            result = bedrock_service.claude_detect_products_json(
                img_bytes,
                media_type="image/jpeg",
            )

            for p in result.get("products", []):
                p["frame_key"] = key
                all_products.append(p)

        except Exception as e:
            print(f"[DETECT ERROR] Frame {key}: {e}")
            continue

    return all_products
