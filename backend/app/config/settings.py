from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "KiranaStudio Backend"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    aws_region: str = "ap-south-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    s3_videos_bucket: str = "kiranastudio-videos"
    s3_frames_bucket: str = "kiranastudio-frames"
    s3_images_bucket: str = "kiranastudio-images"

    jobs_table_name: str = "kiranastudio-jobs"
    catalogs_table_name: str = "kiranastudio-catalogs"

    bedrock_claude_model_id: str = "anthropic.claude-3-5-haiku-20241022-v1:0"
    bedrock_titan_image_model_id: str = "amazon.titan-image-generator-v2:0"

    presigned_url_expiry_seconds: int = 300
    cors_origins: str = "*"

    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        parsed = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        return parsed or ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
