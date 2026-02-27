from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.config.settings import get_settings
from app.dependencies import get_jobs_repo, get_pipeline_orchestrator
from app.models.schemas import JobStatusResponse, ProcessJobResponse, UseSampleResponse
from app.pipeline.orchestrator import PipelineOrchestrator
from app.repo.jobs_repo import JobsRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/use-sample", response_model=UseSampleResponse)
def use_sample_video(
    jobs_repo: JobsRepository = Depends(get_jobs_repo),
) -> UseSampleResponse:
    """
    Create a job that uses the sample video from sample_video/ (no upload).
    Video file must exist at {local_videos_dir}/{sample_video_id}.mp4.
    Then call POST /jobs/{video_id}/process to run the pipeline.
    """
    settings = get_settings()
    video_id = settings.sample_video_id
    video_path = Path(settings.resolved_local_videos_dir) / f"{video_id}.mp4"
    if not video_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Sample video not found: {video_path}. Add {video_id}.mp4 to {settings.resolved_local_videos_dir}.",
        )
    job = jobs_repo.get_by_video_id(video_id)
    if not job:
        job = jobs_repo.create_job(video_id)
    return UseSampleResponse(
        video_id=video_id,
        job_id=job["job_id"],
    )


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
