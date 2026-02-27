"""
Run the full pipeline (extract -> filter -> detect -> dedupe -> generate -> format)
using a local video file. No S3 or DynamoDB.

Usage (from backend/):
  python scripts/run_local_pipeline.py <video_id>

Example: if your video is sample_video/chips.mp4, run:
  python scripts/run_local_pipeline.py chips

Requires: video at {local_videos_dir}/{video_id}.mp4 (default: sample_video/chips.mp4 for video_id=chips).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.settings import get_settings
from app.dependencies import get_jobs_repo, get_pipeline_orchestrator


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python scripts/run_local_pipeline.py <video_id>")
        print("Example: python scripts/run_local_pipeline.py chips")
        print("  (expects video at sample_video/chips.mp4 by default)")
        sys.exit(1)

    video_id = sys.argv[1].strip()
    settings = get_settings()
    # video_path = Path(settings.resolved_local_videos_dir) / f"{video_id}.mp4"

    # if not video_path.is_file():
    #     print(f"Video not found: {video_path}")
    #     print(f"Place your video at: {video_path}")
    #     sys.exit(1)

    jobs_repo = get_jobs_repo()
    job = jobs_repo.get_by_video_id(video_id)
    if not job:
        job = jobs_repo.create_job(video_id)
        print(f"Created job {job['job_id']} for video_id={video_id}")

    orchestrator = get_pipeline_orchestrator()
    print(f"Running pipeline for video_id={video_id} ...")
    orchestrator.run(video_id, job["job_id"])
    print("Pipeline finished. Check status with GET /api/v1/jobs/{video_id}/status")
    updated = jobs_repo.get_by_video_id(video_id)
    print(f"Status: {updated['status']}, product_count: {updated.get('product_count', 0)}")


if __name__ == "__main__":
    main()
