from __future__ import annotations

import mimetypes
from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config.settings import Settings


class S3Service:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = boto3.client(
            "s3",
            region_name=self.settings.aws_region,
            config=Config(retries={"max_attempts": 5, "mode": "standard"}),
        )

    def build_video_key(self, video_id: str) -> str:
        return f"videos/{video_id}.mp4"

    def build_frame_prefix(self, video_id: str) -> str:
        return f"frames/{video_id}/"

    def build_image_prefix(self, video_id: str) -> str:
        return f"images/{video_id}/"

    def create_presigned_upload_url(self, video_id: str, content_type: str) -> str:
        key = self.build_video_key(video_id)
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.settings.s3_videos_bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )

    def download_bytes(self, bucket: str, key: str) -> bytes:
        try:
            obj = self.client.get_object(Bucket=bucket, Key=key)
            return obj["Body"].read()
        except ClientError as e:
            raise RuntimeError(f"S3 download failed s3://{bucket}/{key}: {e}") from e

    def upload_bytes(self, bucket: str, key: str, data: bytes, content_type: str | None = None) -> None:
        if content_type is None:
            content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        try:
            self.client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
        except ClientError as e:
            raise RuntimeError(f"S3 upload failed s3://{bucket}/{key}: {e}") from e
