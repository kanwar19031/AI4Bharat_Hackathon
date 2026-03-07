import io
import json
import logging
import uuid
from pathlib import Path

from PIL import Image, ImageOps

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generate studio-quality product images using Nova Canvas.

    Pipeline:
        1. Crop the product from the frame (using Claude's bounding box)
        2. Place the crop centered on a white canvas (1024×1024)
        3. Create a mask (white = product area to keep, black = background to repaint)
        4. Send to Nova Canvas outpainting → clean white studio background

    Nova Canvas is 50% cheaper than Titan v2 ($0.04 vs $0.08 per image)
    and supports text-based mask prompts for simpler workflows.
    """

    def __init__(self, s3, bedrock):
        self.s3 = s3
        self.bedrock = bedrock

    def _make_canvas_and_mask(self, crop_bytes: bytes, size: int = 1024, padding_ratio: float = 0.25):
        """Place product crop centered on white canvas and build a mask.

        Returns (canvas_png_bytes, mask_png_bytes) where:
          - canvas: white 1024×1024 with the product centered
          - mask: white (keep) for product region, black (repaint) for background
            NOTE: Nova Canvas outpainting mask convention is OPPOSITE to inpainting:
            white = area to KEEP, black = area to REPAINT.
        """
        crop = Image.open(io.BytesIO(crop_bytes)).convert("RGBA")

        logger.info(
            "[IMGGEN] Input crop: %dx%d pixels, %.1f KB",
            crop.size[0], crop.size[1], len(crop_bytes) / 1024,
        )

        canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))

        max_w = int(size * (1.0 - padding_ratio * 2))
        max_h = int(size * (1.0 - padding_ratio * 2))
        crop = ImageOps.contain(crop, (max_w, max_h))

        x = (size - crop.size[0]) // 2
        y = (size - crop.size[1]) // 2
        canvas.paste(crop, (x, y), crop)

        # Build mask: white where product is, black where background should be repainted
        mask = Image.new("L", (size, size), 0)  # black = repaint
        prod_mask = Image.new("L", crop.size, 255)  # white = keep
        mask.paste(prod_mask, (x, y))

        canvas_bytes = io.BytesIO()
        canvas.convert("RGB").save(canvas_bytes, format="PNG")
        mask_bytes = io.BytesIO()
        mask.save(mask_bytes, format="PNG")

        canvas_size = len(canvas_bytes.getvalue())
        mask_size = len(mask_bytes.getvalue())
        logger.info(
            "[IMGGEN] Canvas: %dx%d, %.1f KB | Mask: %.1f KB | "
            "Product placed at (%d,%d), resized to %dx%d",
            size, size, canvas_size / 1024, mask_size / 1024,
            x, y, crop.size[0], crop.size[1],
        )

        return canvas_bytes.getvalue(), mask_bytes.getvalue()

    # ------------------------------------------------------------------
    # Nova Canvas methods (primary)
    # ------------------------------------------------------------------

    def generate_studio_nova(self, crop_bytes: bytes) -> bytes:
        """Generate a studio product shot using Nova Canvas outpainting.

        Takes raw crop bytes, creates canvas + mask, sends to Nova Canvas.
        Returns the generated image bytes (PNG).
        """
        canvas_bytes, mask_bytes = self._make_canvas_and_mask(crop_bytes)

        prompt = (
            "Product on a clean pure white studio background, centered, "
            "realistic, preserve the product label and text, "
            "soft natural shadow, high quality product photography"
        )
        negative = "blurry, distorted text, watermark, artifacts, extra objects"

        logger.info(
            "[IMGGEN] Sending to Nova Canvas OUTPAINTING:\n"
            "  Model: amazon.nova-canvas-v1:0\n"
            "  Region: %s\n"
            "  Canvas size: %.1f KB\n"
            "  Mask size: %.1f KB\n"
            "  Prompt: %s\n"
            "  Negative: %s",
            self.bedrock.settings.nova_canvas_region,
            len(canvas_bytes) / 1024,
            len(mask_bytes) / 1024,
            prompt,
            negative,
        )

        result = self.bedrock.nova_canvas_outpaint(
            image_bytes=canvas_bytes,
            mask_bytes=mask_bytes,
            prompt=prompt,
            negative=negative,
        )

        logger.info(
            "[IMGGEN] Nova Canvas returned image: %.1f KB",
            len(result) / 1024,
        )
        return result

    def save_studio_locally(self, crop_bytes: bytes, out_path: str) -> str:
        """Generate studio image via Nova Canvas and write to local filesystem."""
        out_img_bytes = self.generate_studio_nova(crop_bytes)

        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(out_img_bytes)
        logger.info("[IMGGEN] Saved studio image to %s (%.1f KB)",
                     path, len(out_img_bytes) / 1024)
        return str(path)

    def generate_studio_to_s3(self, crop_bytes: bytes, out_bucket: str, out_key: str) -> dict:
        """Generate studio image via Nova Canvas and upload to S3."""
        out_img_bytes = self.generate_studio_nova(crop_bytes)
        self.s3.upload_bytes(out_bucket, out_key, out_img_bytes, content_type="image/png")
        return {"bucket": out_bucket, "key": out_key}

    # ------------------------------------------------------------------
    # Titan v2 methods (legacy — kept for backward compatibility)
    # ------------------------------------------------------------------

    def _make_canvas_and_mask_titan(self, crop_bytes: bytes, size: int = 1024, padding_ratio: float = 0.25):
        """Titan uses inverted mask convention: white = product, mask gets inverted."""
        crop = Image.open(io.BytesIO(crop_bytes)).convert("RGBA")

        canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))

        max_w = int(size * (1.0 - padding_ratio * 2))
        max_h = int(size * (1.0 - padding_ratio * 2))
        crop = ImageOps.contain(crop, (max_w, max_h))

        x = (size - crop.size[0]) // 2
        y = (size - crop.size[1]) // 2
        canvas.paste(crop, (x, y), crop)

        mask = Image.new("L", (size, size), 255)
        prod_mask = Image.new("L", (size, size), 0)
        prod_mask.paste(crop.split()[-1], (x, y))
        mask = ImageOps.invert(prod_mask)

        canvas_bytes = io.BytesIO()
        canvas.convert("RGB").save(canvas_bytes, format="PNG")
        mask_bytes = io.BytesIO()
        mask.save(mask_bytes, format="PNG")

        return canvas_bytes.getvalue(), mask_bytes.getvalue()

    def generate_studio_titan(self, crop_bytes: bytes) -> bytes:
        """DEPRECATED: Use generate_studio_nova() instead."""
        canvas_bytes, mask_bytes = self._make_canvas_and_mask_titan(crop_bytes)

        prompt = (
            "Product on a clean pure white studio background, centered, "
            "realistic, preserve the product label and text, "
            "soft natural shadow, high quality"
        )
        negative = "blurry, distorted text, watermark, artifacts, extra objects"

        return self.bedrock.titan_outpaint(
            image_bytes=canvas_bytes,
            mask_bytes=mask_bytes,
            prompt=prompt,
            negative=negative,
        )


def generate_studio_images(
    products: list[dict],
    video_id: str,
    bedrock_service,
    s3_service=None,
) -> list[dict]:
    import os

    from app.services.s3_service import S3Service

    settings = get_settings()

    if s3_service is None:
        s3_service = S3Service(settings)

    gen = ImageGenerator(s3_service, bedrock_service)

    output_local_dir = str(Path(settings.local_generated_images_dir) / video_id)
    os.makedirs(output_local_dir, exist_ok=True)

    logger.info("=" * 60)
    logger.info("IMAGE GENERATION — Starting for %d products (video_id=%s)",
                len(products), video_id)
    logger.info("=" * 60)

    for prod_idx, product in enumerate(products, start=1):
        frame_key = product.get("frame_key")
        bbox = product.get("bbox")

        logger.info(
            "[IMGGEN] Product %d/%d: name=%s brand=%s frame_key=%s bbox=%s",
            prod_idx, len(products),
            product.get("product_name"),
            product.get("brand"),
            frame_key,
            bbox,
        )

        if not frame_key:
            logger.warning("[IMGGEN] No frame_key — skipping image generation")
            product["image_url"] = None
            continue

        try:
            # -------- LOAD FRAME --------
            if Path(frame_key).exists():
                frame_bytes = Path(frame_key).read_bytes()
                local_mode = True
                logger.info("[IMGGEN] Loaded frame from LOCAL: %s (%.1f KB)",
                           frame_key, len(frame_bytes) / 1024)
            else:
                frame_bytes = s3_service.download_bytes(settings.s3_bucket, frame_key)
                local_mode = False
                logger.info("[IMGGEN] Loaded frame from S3: %s (%.1f KB)",
                           frame_key, len(frame_bytes) / 1024)

            # -------- CROP USING BBOX --------
            if bbox:
                logger.info(
                    "[IMGGEN] Cropping with bbox: x=%.3f y=%.3f w=%.3f h=%.3f",
                    bbox.get("x", 0), bbox.get("y", 0),
                    bbox.get("w", 0), bbox.get("h", 0),
                )
                crop_bytes = _crop_from_bbox(frame_bytes, bbox)
                logger.info("[IMGGEN] Crop result: %.1f KB", len(crop_bytes) / 1024)
            else:
                logger.info("[IMGGEN] No bbox — using full frame as input")
                crop_bytes = frame_bytes

            product_id = product.get("product_id") or str(uuid.uuid4())
            product["product_id"] = product_id

            # -------- LOCAL DEV MODE --------
            if local_mode:
                out_path = str(Path(output_local_dir) / f"{product_id}.png")
                saved_path = gen.save_studio_locally(crop_bytes, out_path)
                product["image_url"] = saved_path
                logger.info("[IMGGEN] ✓ Product %d/%d saved locally: %s",
                           prod_idx, len(products), saved_path)

            # -------- S3 MODE --------
            else:
                out_key = f"images/{video_id}/{product_id}.png"
                gen.generate_studio_to_s3(
                    crop_bytes,
                    settings.s3_bucket,
                    out_key,
                )
                product["image_url"] = (
                    f"https://{settings.s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{out_key}"
                )
                logger.info("[IMGGEN] ✓ Product %d/%d uploaded to S3: %s",
                           prod_idx, len(products), product["image_url"])

        except Exception as e:
            logger.error("[IMGGEN] ✗ Image generation failed for product %s: %s",
                         product.get("product_name"), e)
            product["image_url"] = None

    success_count = sum(1 for p in products if p.get("image_url"))
    fail_count = len(products) - success_count
    logger.info("=" * 60)
    logger.info(
        "IMAGE GENERATION — Complete. success=%d failed=%d total=%d",
        success_count, fail_count, len(products),
    )
    logger.info("=" * 60)

    return products

def _crop_from_bbox(frame_bytes: bytes, bbox: dict, margin: float = 0.08) -> bytes:
    img = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
    W, H = img.size

    x = float(bbox.get("x", 0))
    y = float(bbox.get("y", 0))
    w = float(bbox.get("w", 0))
    h = float(bbox.get("h", 0))

    # Expand bbox slightly
    x0 = max(0.0, x - margin * w)
    y0 = max(0.0, y - margin * h)
    x1 = min(1.0, x + w + margin * w)
    y1 = min(1.0, y + h + margin * h)

    left = int(x0 * W)
    top = int(y0 * H)
    right = int(x1 * W)
    bottom = int(y1 * H)

    logger.info(
        "[IMGGEN] Crop pixels: (%d,%d) -> (%d,%d) from %dx%d frame",
        left, top, right, bottom, W, H,
    )

    crop = img.crop((left, top, right, bottom))

    out = io.BytesIO()
    crop.save(out, format="PNG")
    return out.getvalue()