"""Per-frame text extraction using Nova Pro vision model.

Pass 1 of the single-product pipeline:
- Send each unique frame individually to Nova Pro
- Extract ALL visible text and classify the frame type (front/back/side/etc.)
- Output feeds into the multi-frame fusion step (Pass 2)
"""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path

from app.config.settings import get_settings
from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)

FRAME_OCR_SYSTEM_PROMPT = (
    "You are a product label OCR engine.\n"
    "The image shows a SINGLE packaged product from one angle.\n"
    "Read ALL visible text on the product packaging — every word, number, symbol.\n"
    "Return STRICT JSON ONLY (no markdown, no commentary, no code fences).\n"
    "Schema:\n"
    "{\n"
    '  "visible_text": ["line1", "line2", ...],\n'
    '  "frame_type": "front" | "back" | "side" | "top" | "bottom" | "nutrition_label" | "barcode" | "close_up" | "other"\n'
    "}\n"
    "Include every word, number, and symbol you can read.\n"
    "Do not guess — only report what is clearly visible."
)


def extract_frame_text(
    image_bytes: bytes,
    bedrock_service: BedrockService,
    media_type: str = "image/jpeg",
) -> dict:
    """Extract visible text from a single product frame using Nova Pro."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    body = {
        "system": [{"text": FRAME_OCR_SYSTEM_PROMPT}],
        "inferenceConfig": {
            "maxTokens": 2000,
            "temperature": 0.1,
        },
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": media_type.split("/")[-1],
                            "source": {"bytes": b64},
                        }
                    },
                    {"text": "Read all text visible on this product packaging."},
                ],
            }
        ],
    }

    settings = get_settings()
    logger.info(
        "[OCR] Sending frame to Nova Pro — image=%.1f KB",
        len(image_bytes) / 1024,
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

    result = json.loads(text)
    logger.info(
        "[OCR] Frame type=%s, text_items=%d: %s",
        result.get("frame_type", "unknown"),
        len(result.get("visible_text", [])),
        result.get("visible_text", [])[:5],
    )
    return result


def extract_all_frames_text(
    frame_paths: list[str],
    bedrock_service: BedrockService,
) -> list[dict]:
    """Extract text from all frames. Returns list of {frame_path, image_bytes, ocr}."""

    results = []
    logger.info("=" * 60)
    logger.info("FRAME OCR — Starting text extraction on %d frames", len(frame_paths))
    logger.info("=" * 60)

    for idx, frame_path in enumerate(frame_paths, start=1):
        try:
            path = Path(frame_path)
            image_bytes = path.read_bytes()

            logger.info(
                "[OCR] Frame %d/%d — path=%s size=%.1f KB",
                idx, len(frame_paths), frame_path, len(image_bytes) / 1024,
            )

            ocr_result = extract_frame_text(image_bytes, bedrock_service)

            results.append({
                "frame_path": frame_path,
                "image_bytes": image_bytes,
                "ocr": ocr_result,
            })

        except Exception as e:
            logger.error("[OCR] Frame %d/%d failed: %s", idx, len(frame_paths), e)
            # Still include the frame for image generation even if OCR fails
            results.append({
                "frame_path": frame_path,
                "image_bytes": Path(frame_path).read_bytes(),
                "ocr": {"visible_text": [], "frame_type": "unknown"},
            })

    logger.info("=" * 60)
    logger.info("FRAME OCR — Complete. Extracted text from %d frames", len(results))
    logger.info("=" * 60)

    return results
