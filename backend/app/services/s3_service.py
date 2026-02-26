from urllib.parse import quote

from app.config.settings import Settings


class S3Service:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_video_key(self, video_id: str) -> str:
        return f"videos/{video_id}.mp4"

    def create_presigned_upload_url(self, video_id: str, content_type: str) -> str:
        key = self.build_video_key(video_id)

        # Placeholder URL to keep the scaffold runnable before AWS integration.
        # Replace with boto3 generate_presigned_url in next implementation step.
        return (
            f"https://{self.settings.s3_videos_bucket}.s3.{self.settings.aws_region}.amazonaws.com/"
            f"{quote(key)}?content-type={quote(content_type)}"
        )

