from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = parent of backend/ (so sample_video at project_root/sample_video is found when running from backend/)
_PROJECT_ROOT = Path(__file__).resolve().parents[2].parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "KiranaStudio Backend"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    aws_region: str = "ap-south-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    s3_bucket: str = "kiranastudio"  # single bucket; folders: videos/, frames/, images/

    jobs_table_name: str = "kiranastudio-jobs"
    catalogs_table_name: str = "kiranastudio-catalogs"

    # Temporarily using Sonnet while Haiku Marketplace subscription activates
    # Once Haiku is enabled, override via .env: BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
    bedrock_claude_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    # Amazon models: available directly in ap-south-1 (no prefix needed)
    bedrock_titan_image_model_id: str = "amazon.titan-image-generator-v2:0"
    bedrock_nova_canvas_model_id: str = "amazon.nova-canvas-v1:0"

    claude_max_tokens: int = 1200
    claude_temperature: float = 0.1

    # ---------- Titan Image v2 (legacy) ----------
    titan_cfg_scale: float = 8.0
    titan_width: int = 1024
    titan_height: int = 1024
    titan_quality: str = "standard"
    titan_outpaint_mode: str = "PRECISE"

    # ---------- Nova Canvas (recommended — 50% cheaper) ----------
    nova_canvas_quality: str = "standard"       # "standard" ($0.04) or "premium" ($0.06)
    nova_canvas_cfg_scale: float = 6.5           # 1.1-10; 6.5 is balanced default

    presigned_url_expiry_seconds: int = 300
    cors_origins: str = "*"

    # ---------- Local dev paths (single source of truth) ----------
    local_data_root: str = "./output"
    local_videos_dir: str = "sample_video"  # use resolved_local_videos_dir for actual path (relative resolved against project root)
    sample_video_id: str = "chips"  # use-sample endpoint and run_local_pipeline use this (file: {local_videos_dir}/{sample_video_id}.mp4)
    local_raw_frames_dir: str = "./output/raw_frames"
    local_filtered_frames_dir: str = "./output/filtered_frames"
    local_generated_images_dir: str = "./output/generated_images"
    local_logs_dir: str = "./output/logs"

    # ---------- Feature flags ----------
    use_aws_storage: bool = False
    use_aws_db: bool = False
    auto_use_aws_db: bool = True
    auto_use_aws_storage: bool = True

    frame_jpeg_quality: int = 2
    frame_blur_threshold: float = 150.0
    frame_scene_threshold: float = 0.3
    frame_min_interval: float = 1
    frame_max_frames: int = 5
    frame_hash_size: int = 16
    frame_hamming_threshold: int = 10

    def _resolve_local_path(self, path_str: str) -> str:
        """Resolve a relative path against project root so it works from any CWD."""
        path = Path(path_str)
        if path.is_absolute():
            return path_str
        return str((_PROJECT_ROOT / path).resolve())

    @property
    def resolved_local_videos_dir(self) -> str:
        """Local videos directory resolved against project root when relative (works from any CWD)."""
        return self._resolve_local_path(self.local_videos_dir)

    @property
    def resolved_local_raw_frames_dir(self) -> str:
        """Raw frames directory resolved against project root when relative."""
        return self._resolve_local_path(self.local_raw_frames_dir)

    @property
    def resolved_local_logs_dir(self) -> str:
        """Logs directory resolved against project root when relative."""
        return self._resolve_local_path(self.local_logs_dir)

    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        parsed = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        return parsed or ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
