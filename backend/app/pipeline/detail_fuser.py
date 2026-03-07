"""Multi-frame fusion: merge OCR from all frames into one comprehensive product profile.

Pass 2 of the single-product pipeline:
- Sends ALL unique frames + their OCR text to Nova Pro in a SINGLE call
- Model combines front/back/side info into one rich product record
"""
from __future__ import annotations

import base64
import json
import logging
from uuid import uuid4

from app.config.settings import get_settings
from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)

FUSION_SYSTEM_PROMPT = (
    "You are a product information extraction engine.\n"
    "You are given multiple frames of the SAME product from different angles.\n"
    "You are also given OCR text extracted from each frame.\n"
    "Combine ALL information to produce a comprehensive product profile.\n"
    "Return STRICT JSON ONLY (no markdown, no commentary, no code fences).\n"
    "Schema:\n"
    "{\n"
    '  "brand": "string",\n'
    '  "product_name": "string",\n'
    '  "variant": "string or null",\n'
    '  "category": "string, e.g. Snacks, Beverages, Dairy",\n'
    '  "net_weight": "string, e.g. 44g, 500ml, or null",\n'
    '  "mrp": number or null (price in INR),\n'
    '  "ingredients": "string or null (full ingredients list if visible)",\n'
    '  "nutrition_facts": {"energy":"...", "protein":"...", "fat":"...", "carbs":"..."} or null,\n'
    '  "barcode": "string or null",\n'
    '  "fssai_license": "string or null",\n'
    '  "manufacturer": "string or null",\n'
    '  "shelf_life": "string or null",\n'
    '  "description": "string — 2-3 sentence product description",\n'
    '  "tags": ["string", ...] — relevant search tags\n'
    "}\n"
    "Do not hallucinate. Only include information clearly visible in the frames or OCR.\n"
    "If a field is not visible, set it to null."
)


def fuse_product_details(
    frames_with_ocr: list[dict],
    bedrock_service: BedrockService,
) -> dict:
    """Send all frames + OCR text to Nova Pro for multi-frame fusion.

    Args:
        frames_with_ocr: List of {"frame_path", "image_bytes", "ocr"} dicts.
        bedrock_service: BedrockService instance.

    Returns:
        Dict with comprehensive product details.
    """
    logger.info("=" * 60)
    logger.info("DETAIL FUSION — Sending %d frames for multi-frame analysis",
                len(frames_with_ocr))
    logger.info("=" * 60)

    settings = get_settings()

    # Build the content array with alternating images and OCR text
    content_blocks = []
    for idx, frame_data in enumerate(frames_with_ocr, start=1):
        b64 = base64.b64encode(frame_data["image_bytes"]).decode("utf-8")
        ocr = frame_data["ocr"]
        frame_type = ocr.get("frame_type", "unknown")
        visible_text = ocr.get("visible_text", [])

        # Add image
        content_blocks.append({
            "image": {
                "format": "jpeg",
                "source": {"bytes": b64},
            }
        })

        # Add OCR context for this frame
        ocr_summary = ", ".join(visible_text) if visible_text else "(no text extracted)"
        content_blocks.append({
            "text": f"Frame {idx} ({frame_type}) OCR: {ocr_summary}"
        })

        logger.info(
            "[FUSION] Frame %d: type=%s, ocr_items=%d, size=%.1f KB",
            idx, frame_type, len(visible_text),
            len(frame_data["image_bytes"]) / 1024,
        )

    # Final instruction
    content_blocks.append({
        "text": "Combine all frames and OCR data above. "
                "Extract the complete product information into a single JSON object."
    })

    body = {
        "system": [{"text": FUSION_SYSTEM_PROMPT}],
        "inferenceConfig": {
            "maxTokens": 4000,
            "temperature": 0.1,
        },
        "messages": [
            {
                "role": "user",
                "content": content_blocks,
            }
        ],
    }

    total_payload_kb = sum(len(f["image_bytes"]) for f in frames_with_ocr) / 1024
    logger.info(
        "[FUSION] Sending to Nova Pro — model=%s total_images=%d total_payload=%.1f KB",
        settings.bedrock_nova_pro_model_id,
        len(frames_with_ocr),
        total_payload_kb,
    )

    resp = bedrock_service.client.invoke_model(
        modelId=settings.bedrock_nova_pro_model_id,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json",
    )

    payload = json.loads(resp["body"].read())
    text = ""
    for block in payload.get("output", {}).get("message", {}).get("content", []):
        if "text" in block:
            text += block["text"]

    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    product = json.loads(text)

    # Ensure product_id
    if "product_id" not in product:
        product["product_id"] = str(uuid4())

    # Normalize net_weight if it came back as a dict
    nw = product.get("net_weight")
    if isinstance(nw, dict):
        v = nw.get("value")
        u = nw.get("unit")
        product["net_weight"] = f"{v}{u}" if v and u else None

    # Normalize mrp → price
    mrp = product.get("mrp")
    if mrp is not None:
        try:
            product["price"] = float(mrp)
        except (TypeError, ValueError):
            product["price"] = None
    else:
        product["price"] = None

    logger.info(
        "[FUSION] Extracted product: brand=%s name=%s variant=%s weight=%s price=%s",
        product.get("brand"),
        product.get("product_name"),
        product.get("variant"),
        product.get("net_weight"),
        product.get("price"),
    )
    logger.info(
        "[FUSION] Extra fields: ingredients=%s nutrition=%s barcode=%s manufacturer=%s",
        "yes" if product.get("ingredients") else "no",
        "yes" if product.get("nutrition_facts") else "no",
        product.get("barcode"),
        product.get("manufacturer"),
    )

    raw_json = json.dumps(product, indent=2, default=str)
    if len(raw_json) > 3000:
        raw_json = raw_json[:3000] + "\n... (truncated)"
    logger.info("[FUSION] Full product JSON:\n%s", raw_json)

    logger.info("=" * 60)
    logger.info("DETAIL FUSION — Complete")
    logger.info("=" * 60)

    return product
