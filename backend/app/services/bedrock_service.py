from app.config.settings import Settings


class BedrockService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def detect_products(self, frame_keys: list[str]) -> list[dict]:
        # Placeholder response so pipeline wiring can be developed end-to-end.
        if not frame_keys:
            return []
        return [
            {
                "product_id": "sample-product-1",
                "brand": "Sample",
                "product_name": "Demo Product",
                "net_weight": "500g",
                "variant": None,
                "price": None,
                "image_url": None,
            }
        ]

    def generate_studio_images(self, products: list[dict], video_id: str) -> list[dict]:
        for product in products:
            product["image_url"] = (
                f"https://{self.settings.s3_images_bucket}.s3.{self.settings.aws_region}.amazonaws.com/"
                f"images/{video_id}/{product['product_id']}.jpg"
            )
        return products

