"""Background removal for product frames using Nova Canvas.

Replaces the old outpainting pipeline (crop→canvas→mask→generate).
Much simpler: just send the frame, get back a transparent PNG with
the product cleanly isolated, then composite onto white background.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from uuid import uuid4

from PIL import Image

from app.config.settings import get_settings
from app.services.bedrock_service import BedrockService
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


def _composite_on_white(transparent_png_bytes: bytes, size: int = 1024) -> bytes:
    """Composite a transparent PNG onto a white background.

    Returns a JPEG/PNG with clean white background — ready for catalog use.
    """
    img = Image.open(io.BytesIO(transparent_png_bytes)).convert("RGBA")
    white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    composite = Image.alpha_composite(white_bg, img)

    # Resize to square for consistency
    composite = composite.convert("RGB")
    composite.thumbnail((size, size), Image.LANCZOS)

    # Center on square canvas
    canvas = Image.new("RGB", (size, size), (255, 255, 255))
    x = (size - composite.size[0]) // 2
    y = (size - composite.size[1]) // 2
    canvas.paste(composite, (x, y))

    out = io.BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue()


def remove_backgrounds(
    frames_with_ocr: list[dict],
    video_id: str,
    bedrock_service: BedrockService,
    s3_service: S3Service | None = None,
) -> list[dict]:
    """Remove background from each frame and save as studio images.

    Returns list of {"image_url": ..., "frame_type": ...} dicts.
    """
    settings = get_settings()
    output_dir = Path(settings.local_generated_images_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    images = []
    logger.info("=" * 60)
    logger.info("BACKGROUND REMOVAL — Starting for %d frames (video_id=%s)",
                len(frames_with_ocr), video_id)
    logger.info("=" * 60)

    for idx, frame_data in enumerate(frames_with_ocr, start=1):
        frame_path = frame_data["frame_path"]
        frame_type = frame_data["ocr"].get("frame_type", "unknown")
        image_bytes = frame_data["image_bytes"]
        image_id = str(uuid4())

        logger.info(
            "[BGREM] Frame %d/%d — type=%s path=%s size=%.1f KB",
            idx, len(frames_with_ocr), frame_type, frame_path,
            len(image_bytes) / 1024,
        )

        try:
            # Call Nova Canvas background removal
            logger.info("[BGREM] Sending to Nova Canvas BACKGROUND_REMOVAL (region=%s)...",
                        settings.nova_canvas_region)
            transparent_bytes = bedrock_service.nova_canvas_background_removal(image_bytes)

            logger.info(
                "[BGREM] Got transparent PNG: %.1f KB — compositing on white...",
                len(transparent_bytes) / 1024,
            )

            # Composite onto white background
            studio_bytes = _composite_on_white(transparent_bytes)

            # Save locally
            out_path = output_dir / f"{image_id}.png"
            out_path.write_bytes(studio_bytes)
            # URL served via /static/images mount
            image_url = f"http://127.0.0.1:5001/static/images/{video_id}/{image_id}.png"

            logger.info("[BGREM] ✓ Frame %d/%d saved: %s (%.1f KB)",
                        idx, len(frames_with_ocr), out_path,
                        len(studio_bytes) / 1024)

            images.append({
                "image_id": image_id,
                "image_url": image_url,
                "frame_type": frame_type,
                "original_frame": frame_path,
            })

        except Exception as e:
            logger.error("[BGREM] ✗ Frame %d/%d failed: %s", idx, len(frames_with_ocr), e)
            # Still include the original frame path as fallback
            images.append({
                "image_id": image_id,
                "image_url": frame_path,
                "frame_type": frame_type,
                "original_frame": frame_path,
            })

    success = sum(1 for img in images if img["image_url"] != img["original_frame"])
    logger.info("=" * 60)
    logger.info("BACKGROUND REMOVAL — Complete. success=%d failed=%d total=%d",
                success, len(images) - success, len(images))
    logger.info("=" * 60)

    return images
