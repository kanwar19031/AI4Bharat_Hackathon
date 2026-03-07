from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.config.settings import get_settings
from app.dependencies import get_jobs_repo, get_s3_service
from app.models.schemas import PresignedUrlRequest, PresignedUrlResponse
from app.repo.interfaces import JobsRepo
from app.services.s3_service import S3Service

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/presigned-url", response_model=PresignedUrlResponse)
def create_presigned_url(
    payload: PresignedUrlRequest,
    jobs_repo: JobsRepo = Depends(get_jobs_repo),
    s3_service: S3Service | None = Depends(get_s3_service),
) -> PresignedUrlResponse:
    if s3_service is None:
        raise HTTPException(
            status_code=501,
            detail=(
                "S3 storage is not enabled or AWS credentials were not found. "
                "Set USE_AWS_STORAGE=true (or set AWS credentials / profile with AUTO_USE_AWS_STORAGE=true) to enable presigned uploads."
            ),
        )
    video_id = str(uuid4())
    job = jobs_repo.create_job(video_id)
    upload_url = s3_service.create_presigned_upload_url(video_id, payload.content_type)
    return PresignedUrlResponse(
        video_id=video_id,
        job_id=job["job_id"],
        upload_url=upload_url,
        expires_in=get_settings().presigned_url_expiry_seconds,
    )


class VideoUploadResponse(PresignedUrlResponse):
    """Re-uses the same shape but upload_url will be empty (already uploaded)."""
    pass


@router.post("/video", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    jobs_repo: JobsRepo = Depends(get_jobs_repo),
    s3_service: S3Service | None = Depends(get_s3_service),
) -> VideoUploadResponse:
    """Upload a video file directly through the backend (avoids S3 CORS)."""
    if s3_service is None:
        raise HTTPException(
            status_code=501,
            detail="S3 storage is not enabled. Set USE_AWS_STORAGE=true.",
        )

    content_type = file.content_type or "video/mp4"
    if not content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video files are accepted.")

    video_id = str(uuid4())
    job = jobs_repo.create_job(video_id)

    # Read the file and upload to S3
    data = await file.read()
    s3_key = s3_service.build_video_key(video_id)
    s3_service.upload_bytes(
        get_settings().s3_bucket, s3_key, data, content_type=content_type
    )

    return VideoUploadResponse(
        video_id=video_id,
        job_id=job["job_id"],
        upload_url="",  # already uploaded
        expires_in=0,
    )
