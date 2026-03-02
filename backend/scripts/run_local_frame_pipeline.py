from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipeline.frame_extractor import extract_frames_with_ffmpeg
from app.pipeline.frame_filter import filter_frames

# Set this before running.
output_dir = "output5"
VIDEO_PATH = r"sample_video/chips.mp4"
RAW_FRAMES_DIR = f"{output_dir}/raw_frames"
FILTERED_FRAMES_DIR = f"{output_dir}/filtered_frames"
LOG_FILE = f"{output_dir}/frame_pipeline_log4.txt"

JPEG_QUALITY = 2
BLUR_THRESHOLD = 175.0
SSIM_THRESHOLD = 0.80
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
        video_path=VIDEO_PATH,
        output_dir=RAW_FRAMES_DIR,
        jpeg_quality=JPEG_QUALITY,
        clean_output_dir=True,
    )

    filtered = filter_frames(
        extraction.frame_paths,
        blur_threshold=BLUR_THRESHOLD,
        ssim_threshold=SSIM_THRESHOLD,
        max_frames=MAX_FRAMES,
    )

    # Copy final frames into a single folder for easy review
    filtered_dir = Path(FILTERED_FRAMES_DIR)
    filtered_dir.mkdir(parents=True, exist_ok=True)
    for i, src_path in enumerate(filtered, start=1):
        dst_name = f"frame_{i:06d}.jpg"
        shutil.copy2(src_path, filtered_dir / dst_name)

    print("source_fps:", extraction.source_fps)
    print("extracted_count:", len(extraction.frame_paths))
    print("filtered_count:", len(filtered))
    print("filtered_paths:")
    for path in filtered:
        print(path)
    print("filtered_frames_dir:", filtered_dir.resolve())
    print("log_file:", log_path)


if __name__ == "__main__":
    main()
