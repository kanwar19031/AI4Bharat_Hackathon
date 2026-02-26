from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.dependencies import get_jobs_repo, get_pipeline_orchestrator
from app.models.schemas import JobStatusResponse, ProcessJobResponse
from app.pipeline.orchestrator import PipelineOrchestrator
from app.repo.jobs_repo import JobsRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/{video_id}/process", response_model=ProcessJobResponse)
def process_job(
    video_id: str,
    background_tasks: BackgroundTasks,
    jobs_repo: JobsRepository = Depends(get_jobs_repo),
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> ProcessJobResponse:
    job = jobs_repo.get_by_video_id(video_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found for video_id")

    if job["status"] in {
        "QUEUED",
        "EXTRACTING",
        "FILTERING",
        "DETECTING",
        "DEDUPLICATING",
        "GENERATING",
        "FORMATTING",
    }:
        return ProcessJobResponse(
            job_id=job["job_id"],
            status=job["status"],
            message="Processing already in progress",
        )

    jobs_repo.update_status(job["job_id"], "QUEUED")
    background_tasks.add_task(orchestrator.run, video_id, job["job_id"])

    return ProcessJobResponse(
        job_id=job["job_id"],
        status="QUEUED",
        message="Pipeline queued in background",
    )


@router.get("/{video_id}/status", response_model=JobStatusResponse)
def get_job_status(
    video_id: str,
    jobs_repo: JobsRepository = Depends(get_jobs_repo),
) -> JobStatusResponse:
    job = jobs_repo.get_by_video_id(video_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found for video_id")

    return JobStatusResponse(**job)
