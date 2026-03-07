import base64
import json
import logging

import boto3
from botocore.config import Config

from app.config.settings import get_settings

_settings = get_settings()
logger = logging.getLogger(__name__)


class BedrockService:
    def __init__(self, settings=None):
        self.settings = settings or _settings
        kwargs: dict = {
            "region_name": self.settings.aws_region,
            "config": Config(
                retries={"max_attempts": 5, "mode": "standard"},
                read_timeout=300,
            ),
        }
        if self.settings.aws_access_key_id and self.settings.aws_secret_access_key:
            kwargs["aws_access_key_id"] = self.settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = self.settings.aws_secret_access_key
        self.client = boto3.client("bedrock-runtime", **kwargs)

        # Nova Canvas is only available in us-east-1/eu-west-1/ap-northeast-1
        # Create a separate client for image generation if region differs
        canvas_region = self.settings.nova_canvas_region
        if canvas_region != self.settings.aws_region:
            canvas_kwargs = {**kwargs, "region_name": canvas_region}
            canvas_kwargs["config"] = Config(
                retries={"max_attempts": 5, "mode": "standard"},
                read_timeout=300,
            )
            self.canvas_client = boto3.client("bedrock-runtime", **canvas_kwargs)
            logger.info("Nova Canvas client using region: %s", canvas_region)
        else:
            self.canvas_client = self.client

    # ------------------------------------------------------------------
    # Nova Canvas — Background Removal
    # ------------------------------------------------------------------

    def nova_canvas_background_removal(self, image_bytes: bytes) -> bytes:
        """Remove background from an image using Nova Canvas.

        Returns a PNG with full 8-bit transparency — the product is
        cleanly isolated with no background. Perfect for compositing
        onto a white studio background afterwards.
        """
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")

        body = {
            "taskType": "BACKGROUND_REMOVAL",
            "backgroundRemovalParams": {
                "image": img_b64,
            },
        }

        logger.info("Nova Canvas BACKGROUND_REMOVAL request")

        resp = self.canvas_client.invoke_model(
            modelId=self.settings.bedrock_nova_canvas_model_id,
            body=json.dumps(body),
            accept="application/json",
            contentType="application/json",
        )

        payload = json.loads(resp["body"].read())
        if payload.get("error"):
            raise RuntimeError(f"Nova Canvas error: {payload['error']}")

        images = payload.get("images", [])
        if not images:
            raise RuntimeError(f"No images in Nova Canvas response: {payload.keys()}")

        return base64.b64decode(images[0])
