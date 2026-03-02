"""Frame deduplication using perceptual hashing.

Replaces the old SSIM-based approach with pHash (DCT-based perceptual hash).
pHash is ~100-1000x faster per comparison (integer XOR vs full pixel scan) and
far more robust to camera motion, lighting changes, and minor color shifts.

Reference: frame_deduplication_research.md — Priority 2
"""
from __future__ import annotations

import logging
from pathlib import Path

import imagehash
from PIL import Image

logger = logging.getLogger(__name__)


class FrameDeduplicator:
    """Remove near-duplicate frames via perceptual hashing.

    Each frame is converted to a compact 256-bit hash (when hash_size=16).
    Frames whose Hamming distance to any already-accepted frame is below
    *hamming_threshold* are discarded as duplicates.

    Threshold guidelines (for 256-bit pHash, hash_size=16):
        6–8  bits  → strict  (removes only near-identical frames)
        10–15 bits → moderate (recommended starting point)
        20+  bits  → aggressive (risk of merging distinct scenes)
    """

    def __init__(
        self,
        hash_size: int = 16,
        hamming_threshold: int = 10,
    ) -> None:
        if hash_size < 2:
            raise ValueError("hash_size must be >= 2")
        if hamming_threshold < 0:
            raise ValueError("hamming_threshold must be >= 0")

        self.hash_size = hash_size
        self.hamming_threshold = hamming_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def deduplicate(self, frame_paths: list[str]) -> list[str]:
        """Return a subset of *frame_paths* with near-duplicates removed.

        Frames are processed in order.  The first frame is always accepted.
        Each subsequent frame is compared against every accepted frame; if
        its Hamming distance to ANY accepted frame is below the threshold,
        it is discarded as a duplicate.

        Args:
            frame_paths: Ordered list of paths to candidate frame images.

        Returns:
            List of paths to the unique (non-duplicate) frames, preserving
            the original ordering.
        """
        if not frame_paths:
            return []

        logger.info(
            "Starting perceptual-hash deduplication "
            "input_frames=%s hash_size=%s hamming_threshold=%s",
            len(frame_paths),
            self.hash_size,
            self.hamming_threshold,
        )

        accepted_hashes: list[imagehash.ImageHash] = []
        accepted_paths: list[str] = []

        for idx, frame_path in enumerate(frame_paths, start=1):
            frame_hash = self._compute_hash(frame_path)
            if frame_hash is None:
                logger.warning(
                    "Frame %s/%s skipped (unreadable) path=%s",
                    idx, len(frame_paths), frame_path,
                )
                continue

            if self._is_duplicate(frame_hash, accepted_hashes):
                logger.info(
                    "Frame %s/%s rejected as duplicate path=%s",
                    idx, len(frame_paths), frame_path,
                )
            else:
                accepted_hashes.append(frame_hash)
                accepted_paths.append(str(Path(frame_path)))
                logger.info(
                    "Frame %s/%s accepted (unique) path=%s",
                    idx, len(frame_paths), frame_path,
                )

        logger.info(
            "Perceptual-hash deduplication complete "
            "input=%s accepted=%s removed=%s",
            len(frame_paths),
            len(accepted_paths),
            len(frame_paths) - len(accepted_paths),
        )
        return accepted_paths

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_hash(self, frame_path: str) -> imagehash.ImageHash | None:
        """Compute DCT-based perceptual hash for a single frame."""
        try:
            with Image.open(frame_path) as img:
                return imagehash.phash(img, hash_size=self.hash_size)
        except Exception:
            logger.exception("Failed to compute pHash for %s", frame_path)
            return None

    def _is_duplicate(
        self,
        candidate: imagehash.ImageHash,
        accepted: list[imagehash.ImageHash],
    ) -> bool:
        """Return True if *candidate* is too similar to any accepted hash."""
        for existing in accepted:
            distance = candidate - existing  # Hamming distance via __sub__
            if distance < self.hamming_threshold:
                return True
        return False
