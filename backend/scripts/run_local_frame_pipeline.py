from __future__ import annotations

"""
Run from backend dir:  python scripts/run_local_frame_pipeline.py
Run from repo root:    python backend/scripts/run_local_frame_pipeline.py
"""

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.settings import get_settings
from app.pipeline.frame_extractor import extract_frames_with_ffmpeg
from app.pipeline.frame_filter import filter_frames

settings = get_settings()

VIDEO_PATH = Path(settings.resolved_local_videos_dir) / "chips.mp4"
RAW_FRAMES_DIR = Path(settings.resolved_local_raw_frames_dir)
LOG_FILE = Path(settings.resolved_local_logs_dir) / "frame_pipeline.txt"

JPEG_QUALITY = settings.frame_jpeg_quality
BLUR_THRESHOLD = settings.frame_blur_threshold
MAX_FRAMES = None


def main() -> None:
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, mode="w", encoding="utf-8"),
        ],
    )

    video_file = Path(VIDEO_PATH)
    if not video_file.is_file():
        raise FileNotFoundError(f"Set VIDEO_PATH to a valid local file. Current: {VIDEO_PATH}")

    extraction = extract_frames_with_ffmpeg(
        video_path=str(VIDEO_PATH),
        output_dir=str(RAW_FRAMES_DIR),
        jpeg_quality=JPEG_QUALITY,
        scene_threshold=settings.frame_scene_threshold,
        min_interval=settings.frame_min_interval,
        clean_output_dir=True,
    )

    filtered = filter_frames(
        extraction.frame_paths,
        blur_threshold=BLUR_THRESHOLD,
        max_frames=MAX_FRAMES,
    )

    print("source_fps:", extraction.source_fps)
    print("extracted_count:", len(extraction.frame_paths))
    print("filtered_count:", len(filtered))
    filtered_sorted = sorted(filtered, key=lambda path: Path(path).name)
    print("filtered_paths_sorted:")
    for path in filtered_sorted:
        print(path)
    print("log_file:", log_path)


if __name__ == "__main__":
    main()
