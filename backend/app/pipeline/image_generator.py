import io
import uuid
from pathlib import Path

from PIL import Image, ImageOps

from app.config.settings import get_settings


class ImageGenerator:
    def __init__(self, s3, bedrock):
        self.s3 = s3
        self.bedrock = bedrock

    def _make_canvas_and_mask(self, crop_bytes: bytes, size: int = 1024, padding_ratio: float = 0.25):
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

    def generate_studio(self, crop_bucket: str, crop_key: str, out_bucket: str, out_key: str):
        crop_bytes = self.s3.download_bytes(crop_bucket, crop_key)

        canvas_bytes, mask_bytes = self._make_canvas_and_mask(crop_bytes)

        prompt = "Product on a clean pure white studio background, centered, realistic, preserve the product label and text, soft natural shadow, high quality"
        negative = "blurry, distorted text, watermark, artifacts, extra objects"

        out_img_bytes = self.bedrock.titan_outpaint(
            image_bytes=canvas_bytes,
            mask_bytes=mask_bytes,
            prompt=prompt,
            negative=negative,
        )

        self.s3.upload_bytes(out_bucket, out_key, out_img_bytes, content_type="image/png")
        return {"bucket": out_bucket, "key": out_key}

    def generate_studio_from_bytes(self, crop_bytes: bytes, out_bucket: str, out_key: str):
        """Same as generate_studio but with crop from bytes (e.g. local file). Uploads to S3."""
        canvas_bytes, mask_bytes = self._make_canvas_and_mask(crop_bytes)
        prompt = "Product on a clean pure white studio background, centered, realistic, preserve the product label and text, soft natural shadow, high quality"
        negative = "blurry, distorted text, watermark, artifacts, extra objects"
        out_img_bytes = self.bedrock.titan_outpaint(
            image_bytes=canvas_bytes, mask_bytes=mask_bytes, prompt=prompt, negative=negative
        )
        self.s3.upload_bytes(out_bucket, out_key, out_img_bytes, content_type="image/png")
        return {"bucket": out_bucket, "key": out_key}

    def save_studio_locally(self, crop_bytes: bytes, out_path: str) -> str:
        """
        Generate studio image via Titan and write to local filesystem.
        """
        canvas_bytes, mask_bytes = self._make_canvas_and_mask(crop_bytes)

        prompt = (
            "Product on a clean pure white studio background, centered, realistic, "
            "preserve the product label and text, soft natural shadow, high quality"
        )
        negative = "blurry, distorted text, watermark, artifacts, extra objects"

        out_img_bytes = self.bedrock.titan_outpaint(
            image_bytes=canvas_bytes,
            mask_bytes=mask_bytes,
            prompt=prompt,
            negative=negative,
        )

        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(out_img_bytes)
        return str(path)


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

    for product in products:
        frame_key = product.get("frame_key")
        bbox = product.get("bbox")

        if not frame_key:
            product["image_url"] = None
            continue

        try:
            # -------- LOAD FRAME --------
            if Path(frame_key).exists():
                frame_bytes = Path(frame_key).read_bytes()
                local_mode = True
            else:
                frame_bytes = s3_service.download_bytes(settings.s3_frames_bucket, frame_key)
                local_mode = False

            # -------- CROP USING BBOX --------
            crop_bytes = _crop_from_bbox(frame_bytes, bbox) if bbox else frame_bytes

            product_id = product.get("product_id") or str(uuid.uuid4())
            product["product_id"] = product_id

            # -------- LOCAL DEV MODE --------
            if local_mode:
                out_path = str(Path(output_local_dir) / f"{product_id}.png")
                saved_path = gen.save_studio_locally(crop_bytes, out_path)
                product["image_url"] = saved_path

            # -------- S3 MODE --------
            else:
                out_key = f"images/{video_id}/{product_id}.png"
                gen.generate_studio_from_bytes(
                    crop_bytes,
                    settings.s3_images_bucket,
                    out_key,
                )
                product["image_url"] = (
                    f"https://{settings.s3_images_bucket}.s3.{settings.aws_region}.amazonaws.com/{out_key}"
                )

        except Exception as e:
            print(f"[GEN ERROR] Product {product.get('product_name')}: {e}")
            product["image_url"] = None

    return products

def _crop_from_bbox(frame_bytes: bytes, bbox: dict, margin: float = 0.08) -> bytes:
    import io
    from PIL import Image

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

    crop = img.crop((left, top, right, bottom))

    out = io.BytesIO()
    crop.save(out, format="PNG")
    return out.getvalue()