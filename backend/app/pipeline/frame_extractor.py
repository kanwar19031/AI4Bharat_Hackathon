from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FrameExtractionResult:
    frame_paths: list[str]
    source_fps: float


def _run_binary(command: list[str], error_prefix: str) -> str:
    logger.info("Running command: %s", " ".join(command))
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        logger.info("Command completed: %s", command[0])
        return completed.stdout
    except FileNotFoundError as exc:
        binary = command[0]
        raise RuntimeError(f"{binary} not found. Install FFmpeg and ensure it is on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"{error_prefix}: {stderr}") from exc


def _parse_ffprobe_rate(rate: str) -> float:
    if not rate or rate == "0/0":
        return 0.0

    if "/" in rate:
        numerator_text, denominator_text = rate.split("/", maxsplit=1)
        numerator = float(numerator_text)
        denominator = float(denominator_text)
        if denominator == 0:
            return 0.0
        return numerator / denominator

    return float(rate)


def extract_frames_with_ffmpeg(
    video_path: str,
    output_dir: str,
    jpeg_quality: int = 2,
    scene_threshold: float = 0.3,
    min_interval: float = 1.5,
    clean_output_dir: bool = True,
) -> FrameExtractionResult:
    """Extract keyframes using FFmpeg scene-change detection.

    Only frames where the scene-change score exceeds *scene_threshold* are
    emitted.  A time-based fallback guarantees at least one frame every
    *min_interval* seconds so that slow, static segments are still covered.

    Args:
        video_path: Path to the source video file.
        output_dir: Directory where extracted JPEG frames are written.
        jpeg_quality: JPEG quality for ``-q:v`` (2 = best, 31 = worst).
        scene_threshold: FFmpeg scene-change score in ``[0, 1]``.
            Lower values extract more frames; higher values are stricter.
        min_interval: Maximum gap (seconds) between selected frames.
            Acts as a fallback to prevent long gaps in static footage.
        clean_output_dir: If True, delete *output_dir* before extraction.
    """
    if not (2 <= jpeg_quality <= 31):
        raise ValueError("jpeg_quality must be between 2 and 31")
    if not (0.0 < scene_threshold <= 1.0):
        raise ValueError("scene_threshold must be in (0, 1]")
    if min_interval <= 0:
        raise ValueError("min_interval must be > 0")

    video_file = Path(video_path)
    if not video_file.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    output_path = Path(output_dir)
    if clean_output_dir and output_path.exists():
        logger.info("Cleaning existing output directory: %s", output_path)
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Starting frame extraction video=%s output_dir=%s "
        "jpeg_quality=%s scene_threshold=%s min_interval=%s",
        video_file,
        output_path,
        jpeg_quality,
        scene_threshold,
        min_interval,
    )

    # --- Probe source FPS ---------------------------------------------------
    probe_command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate,r_frame_rate",
        "-of",
        "json",
        str(video_file),
    ]
    probe_output = _run_binary(probe_command, "Failed to probe input video")
    payload = json.loads(probe_output)

    streams = payload.get("streams") or []
    if not streams:
        raise RuntimeError("No video stream found in input file.")

    stream_info = streams[0]
    source_fps = _parse_ffprobe_rate(stream_info.get("avg_frame_rate", ""))
    if source_fps <= 0:
        source_fps = _parse_ffprobe_rate(stream_info.get("r_frame_rate", ""))
    if source_fps <= 0:
        raise RuntimeError("Unable to determine source FPS from ffprobe.")
    logger.info("Detected source FPS: %.3f", source_fps)

    # --- Extract only scene-change / interval frames -------------------------
    # select expression:
    #   gt(scene,T)                    – scene change exceeds threshold
    #   isnan(prev_selected_t)         – always pick the very first frame
    #   gte(t-prev_selected_t, I)      – fallback: at least 1 frame every I sec
    select_expr = (
        f"gt(scene\\,{scene_threshold})"
        f"+isnan(prev_selected_t)"
        f"+gte(t-prev_selected_t\\,{min_interval})"
    )

    frame_pattern = output_path / "frame_%06d.jpg"
    extract_command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_file),
        "-vf",
        f"select='{select_expr}'",
        "-vsync",
        "vfr",
        "-q:v",
        str(jpeg_quality),
        str(frame_pattern),
    ]
    _run_binary(extract_command, "Failed to extract frames")

    frame_paths = [str(path) for path in sorted(output_path.glob("frame_*.jpg"))]
    logger.info("Frame extraction complete. total_frames=%s", len(frame_paths))
    return FrameExtractionResult(
        frame_paths=frame_paths,
        source_fps=source_fps,
    )


def extract_frames_from_video(
    video_path: str,
    output_dir: str,
    jpeg_quality: int = 2,
    scene_threshold: float = 0.3,
    min_interval: float = 1.5,
    clean_output_dir: bool = True,
) -> list[str]:
    result = extract_frames_with_ffmpeg(
        video_path=video_path,
        output_dir=output_dir,
        jpeg_quality=jpeg_quality,
        scene_threshold=scene_threshold,
        min_interval=min_interval,
        clean_output_dir=clean_output_dir,
    )
    return result.frame_paths


def extract_frames(video_id: str) -> list[str]:
    """
    Local-dev implementation:
    - reads video from settings.resolved_local_videos_dir/{video_id}.mp4
    - writes frames to settings.local_raw_frames_dir/{video_id}/
    - returns list of frame file paths
    """
    settings = get_settings()

    video_path = Path(settings.resolved_local_videos_dir) / f"{video_id}.mp4"
    output_dir = Path(settings.local_raw_frames_dir) / video_id

    return extract_frames_from_video(
        video_path=str(video_path),
        output_dir=str(output_dir),
        jpeg_quality=settings.frame_jpeg_quality,
        scene_threshold=settings.frame_scene_threshold,
        min_interval=settings.frame_min_interval,
        clean_output_dir=True,
    )

