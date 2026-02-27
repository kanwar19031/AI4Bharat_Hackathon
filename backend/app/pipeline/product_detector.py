from app.services.bedrock_service import BedrockService


def detect_products(frame_keys: list[str], bedrock_service: BedrockService) -> list[dict]:
    return bedrock_service.detect_products(frame_keys)

