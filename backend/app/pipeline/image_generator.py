from app.services.bedrock_service import BedrockService


def generate_studio_images(products: list[dict], video_id: str, bedrock_service: BedrockService) -> list[dict]:
    return bedrock_service.generate_studio_images(products, video_id)

