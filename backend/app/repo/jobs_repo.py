from datetime import datetime, timezone
from uuid import uuid4


class JobsRepository:
    """Temporary in-memory repository.

    Swap this implementation with DynamoDB access once AWS wiring is added.
    """

    def __init__(self) -> None:
        self._jobs_by_id: dict[str, dict] = {}
        self._job_id_by_video: dict[str, str] = {}

    def create_job(self, video_id: str) -> dict:
        now = datetime.now(timezone.utc)
        job_id = str(uuid4())
        record = {
            "job_id": job_id,
            "video_id": video_id,
            "status": "UPLOADED",
            "product_count": 0,
            "error_message": None,
            "catalog_id": None,
            "created_at": now,
            "updated_at": now,
        }
        self._jobs_by_id[job_id] = record
        self._job_id_by_video[video_id] = job_id
        return record

    def get_by_video_id(self, video_id: str) -> dict | None:
        job_id = self._job_id_by_video.get(video_id)
        if not job_id:
            return None
        return self._jobs_by_id.get(job_id)

    def get_by_job_id(self, job_id: str) -> dict | None:
        return self._jobs_by_id.get(job_id)

    def update_status(
        self,
        job_id: str,
        status: str,
        *,
        product_count: int | None = None,
        error_message: str | None = None,
        catalog_id: str | None = None,
    ) -> dict:
        job = self._jobs_by_id[job_id]
        job["status"] = status
        job["updated_at"] = datetime.now(timezone.utc)
        if product_count is not None:
            job["product_count"] = product_count
        if error_message is not None:
            job["error_message"] = error_message
        if catalog_id is not None:
            job["catalog_id"] = catalog_id
        return job

