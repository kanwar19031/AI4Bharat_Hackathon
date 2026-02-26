from uuid import uuid4

from fastapi import APIRouter, Depends

from app.config.settings import get_settings
from app.dependencies import get_jobs_repo, get_s3_service
from app.models.schemas import PresignedUrlRequest, PresignedUrlResponse
from app.repo.jobs_repo import JobsRepository
from app.services.s3_service import S3Service

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/presigned-url", response_model=PresignedUrlResponse)
def create_presigned_url(
    payload: PresignedUrlRequest,
    jobs_repo: JobsRepository = Depends(get_jobs_repo),
    s3_service: S3Service = Depends(get_s3_service),
) -> PresignedUrlResponse:
    video_id = str(uuid4())
    job = jobs_repo.create_job(video_id)
    upload_url = s3_service.create_presigned_upload_url(video_id, payload.content_type)
    return PresignedUrlResponse(
        video_id=video_id,
        job_id=job["job_id"],
        upload_url=upload_url,
        expires_in=get_settings().presigned_url_expiry_seconds,
    )
