from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

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
