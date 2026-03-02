from __future__ import annotations

import logging
from pathlib import Path

import cv2

logger = logging.getLogger(__name__)


def _read_gray_frame(frame_path: str) -> cv2.typing.MatLike:
    image = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Unable to read frame: {frame_path}")
    return image


def _blur_score(gray_image: cv2.typing.MatLike) -> float:
    """Return Laplacian variance as a sharpness score (higher = sharper)."""
    return float(cv2.Laplacian(gray_image, cv2.CV_64F).var())


def filter_frames(
    frame_paths: list[str],
    blur_threshold: float = 100.0,
    max_frames: int | None = None,
) -> list[str]:
    """Filter frames by sharpness using Laplacian variance.

    Frames whose blur score falls below *blur_threshold* are discarded.  The
    remaining frames are sorted by sharpness (descending) and optionally
    truncated to *max_frames*.

    Args:
        frame_paths: Paths to candidate frame images.
        blur_threshold: Minimum Laplacian variance to keep a frame.
        max_frames: If set, return at most this many frames (sharpest first).
    """
    if max_frames is not None and max_frames < 0:
        raise ValueError("max_frames must be >= 0")

    logger.info(
        "Starting frame filter input_frames=%s blur_threshold=%s max_frames=%s",
        len(frame_paths),
        blur_threshold,
        max_frames,
    )

    sharp_frames: list[dict] = []
    for frame_index, frame_path in enumerate(frame_paths, start=1):
        gray = _read_gray_frame(frame_path)
        score = _blur_score(gray)
        if score >= blur_threshold:
            logger.info(
                "Frame %s/%s passed blur check path=%s blur_score=%.2f",
                frame_index,
                len(frame_paths),
                frame_path,
                score,
            )
            sharp_frames.append({"path": str(Path(frame_path)), "blur_score": score})
        else:
            logger.info(
                "Frame %s/%s rejected as blurry path=%s blur_score=%.2f",
                frame_index,
                len(frame_paths),
                frame_path,
                score,
            )

    # Sort by sharpness descending and apply optional cap.
    sharp_frames.sort(key=lambda f: f["blur_score"], reverse=True)
    if max_frames is not None:
        sharp_frames = sharp_frames[:max_frames]

    selected = [f["path"] for f in sharp_frames]
    logger.info(
        "Frame filter complete sharp_frames=%s selected=%s",
        len(sharp_frames),
        len(selected),
    )
    return selected
