from __future__ import annotations

import logging
import warnings
from pathlib import Path

import blur_detector
import cv2
import numpy as np
from skimage.metrics import structural_similarity

logger = logging.getLogger(__name__)

# Tuned for runtime on frame batches while preserving stable ranking behavior.
_BLUR_DETECTOR_CONFIG = {
    "downsampling_factor": 8,
    "num_scales": 3,
    "scale_start": 2,
    "num_iterations_RF_filter": 1,
    "show_progress": False,
}


def _read_gray_frame(frame_path: str) -> cv2.typing.MatLike:
    image = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Unable to read frame: {frame_path}")
    return image


def _blur_score_lib(gray_image: cv2.typing.MatLike) -> float:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r".*`square` is deprecated.*", category=FutureWarning)
        warnings.filterwarnings(
            "ignore",
            message=r".*Possible precision loss converting image of type float64 to uint8.*",
            category=UserWarning,
        )
        blur_map = blur_detector.detectBlur(gray_image, **_BLUR_DETECTOR_CONFIG)
    return float(np.mean(blur_map))

def _blur_score(gray_image: cv2.typing.MatLike) -> float:
    return float(cv2.Laplacian(gray_image, cv2.CV_64F).var())


def filter_frames(
    frame_keys: list[str],
    blur_threshold: float = 0.11,
    ssim_threshold: float = 0.95,
    max_frames: int | None = None,
) -> list[str]:
    if not (0.0 <= ssim_threshold <= 1.0):
        raise ValueError("ssim_threshold must be between 0 and 1")
    if max_frames is not None and max_frames < 0:
        raise ValueError("max_frames must be >= 0")

    logger.info(
        "Starting frame filter input_frames=%s blur_threshold=%s ssim_threshold=%s max_frames=%s",
        len(frame_keys),
        blur_threshold,
        ssim_threshold,
        max_frames,
    )

    sharp_candidates: list[dict] = []
    for frame_index, frame_path in enumerate(frame_keys, start=1):
        gray = _read_gray_frame(frame_path)
        score = _blur_score_lib(gray)
        if score >= blur_threshold:
            logger.info(
                "Frame %s/%s passed blur check path=%s blur_score=%.2f",
                frame_index,
                len(frame_keys),
                frame_path,
                score,
            )
            gray_small = cv2.resize(gray, (256, 256), interpolation=cv2.INTER_AREA)
            sharp_candidates.append(
                {
                    "path": str(Path(frame_path)),
                    "blur_score": score,
                    "gray_small": gray_small,
                }
            )
        else:
            logger.info(
                "Frame %s/%s rejected as blurry path=%s blur_score=%.2f",
                frame_index,
                len(frame_keys),
                frame_path,
                score,
            )

    unique_frames: list[dict] = []
    for candidate in sharp_candidates:
        duplicate_index: int | None = None
        for idx, existing in enumerate(unique_frames):
            score = structural_similarity(candidate["gray_small"], existing["gray_small"])
            if score >= ssim_threshold:
                duplicate_index = idx
                break

        if duplicate_index is None:
            logger.info("Frame kept as unique path=%s", candidate["path"])
            unique_frames.append(candidate)
        else:
            existing = unique_frames[duplicate_index]
            if candidate["blur_score"] > existing["blur_score"]:
                logger.info(
                    "Duplicate frame replaced with sharper one old=%s new=%s old_score=%.2f new_score=%.2f",
                    existing["path"],
                    candidate["path"],
                    existing["blur_score"],
                    candidate["blur_score"],
                )
                unique_frames[duplicate_index] = candidate
            else:
                logger.info(
                    "Duplicate frame dropped path=%s score=%.2f existing=%s existing_score=%.2f",
                    candidate["path"],
                    candidate["blur_score"],
                    existing["path"],
                    existing["blur_score"],
                )

    unique_frames.sort(key=lambda frame: frame["blur_score"], reverse=True)
    if max_frames is None:
        selected = [frame["path"] for frame in unique_frames]
    else:
        selected = [frame["path"] for frame in unique_frames[:max_frames]]
    logger.info(
        "Frame filter complete sharp_candidates=%s unique_frames=%s selected=%s",
        len(sharp_candidates),
        len(unique_frames),
        len(selected),
    )
    return selected
