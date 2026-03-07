import logging
from pathlib import Path

from app.config.settings import get_settings
from app.pipeline.background_remover import remove_backgrounds
from app.pipeline.detail_fuser import fuse_product_details
from app.pipeline.frame_deduplicator import FrameDeduplicator
from app.pipeline.frame_extractor import extract_frames
from app.pipeline.frame_filter import filter_frames
from app.pipeline.text_extractor import extract_all_frames_text
from app.repo.interfaces import CatalogsRepo, JobsRepo
from app.services.bedrock_service import BedrockService
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(
        self,
        jobs_repo: JobsRepo,
        catalogs_repo: CatalogsRepo,
        bedrock_service: BedrockService,
        s3_service: S3Service | None = None,
    ) -> None:
        self.jobs_repo = jobs_repo
        self.catalogs_repo = catalogs_repo
        self.bedrock_service = bedrock_service
        self.s3_service = s3_service

    def _ensure_local_video(self, video_id: str) -> None:
        """Download video from S3 to local disk if it doesn't exist locally."""
        settings = get_settings()
        local_dir = Path(settings.resolved_local_videos_dir)
        local_path = local_dir / f"{video_id}.mp4"

        if local_path.is_file():
            logger.info("Video already exists locally: %s", local_path)
            return

        if self.s3_service is None:
            logger.warning("No S3 service available and video not found locally.")
            return

        s3_key = self.s3_service.build_video_key(video_id)
        logger.info("Downloading video from S3 s3://%s/%s -> %s",
                     settings.s3_bucket, s3_key, local_path)
        local_dir.mkdir(parents=True, exist_ok=True)
        data = self.s3_service.download_bytes(settings.s3_bucket, s3_key)
        local_path.write_bytes(data)
        logger.info("Downloaded %d bytes to %s", len(data), local_path)

    def run(self, video_id: str, job_id: str) -> None:
        """Single-product pipeline:
        1. Extract frames from video (FFmpeg)
        2. Filter blurry frames (OpenCV)
        3. Deduplicate near-identical frames (pHash)
        4. OCR each frame — extract visible text (Nova Pro)
        5. Fuse all frames + OCR into one product profile (Nova Pro multi-image)
        6. Remove background from each frame (Nova Canvas)
        7. Save product + images as catalog
        """
        try:
            # --- Step 1: Extract frames ---
            self.jobs_repo.update_status(job_id, "EXTRACTING")
            self._ensure_local_video(video_id)
            frames = extract_frames(video_id)

            # --- Step 2: Filter blurry frames ---
            self.jobs_repo.update_status(job_id, "FILTERING")
            settings = get_settings()
            filtered_frames = filter_frames(
                frames,
                blur_threshold=settings.frame_blur_threshold,
                max_frames=settings.frame_max_frames,
            )

            # --- Step 3: Deduplicate frames ---
            self.jobs_repo.update_status(job_id, "DEDUPLICATING_FRAMES")
            deduplicator = FrameDeduplicator(
                hash_size=settings.frame_hash_size,
                hamming_threshold=settings.frame_hamming_threshold,
            )
            unique_frames = deduplicator.deduplicate(filtered_frames)

            # --- Step 4: OCR each frame ---
            self.jobs_repo.update_status(job_id, "READING_TEXT")
            frames_with_ocr = extract_all_frames_text(
                unique_frames, self.bedrock_service,
            )

            # --- Step 5: Multi-frame fusion ---
            self.jobs_repo.update_status(job_id, "EXTRACTING_DETAILS")
            product = fuse_product_details(frames_with_ocr, self.bedrock_service)

            # --- Step 6: Background removal ---
            self.jobs_repo.update_status(job_id, "GENERATING_IMAGES")
            images = remove_backgrounds(
                frames_with_ocr, video_id,
                self.bedrock_service, self.s3_service,
            )

            # Attach images to product
            product["images"] = images
            # Set primary image_url to the first successful image
            for img in images:
                if img["image_url"] != img.get("original_frame"):
                    product["image_url"] = img["image_url"]
                    break
            else:
                product["image_url"] = images[0]["image_url"] if images else None

            # --- Step 7: Save catalog ---
            self.jobs_repo.update_status(job_id, "FORMATTING")

            # Wrap in products list for backward compatibility
            products = [product]

            ondc_catalog = {
                "context": {
                    "domain": "ONDC:RET10",
                    "transaction_id": video_id,
                },
                "message": {
                    "catalog": {
                        "providers": [{"items": products}]
                    }
                },
            }

            catalog = self.catalogs_repo.create_catalog(
                job_id,
                products=products,
                ondc_catalog=ondc_catalog,
            )
            self.jobs_repo.update_status(
                job_id,
                "COMPLETED",
                product_count=1,
                catalog_id=catalog["catalog_id"],
            )

            logger.info("Pipeline complete for video_id=%s — product: %s %s",
                        video_id, product.get("brand"), product.get("product_name"))

        except Exception as exc:
            logger.exception("Pipeline failed for video_id=%s", video_id)
            self.jobs_repo.update_status(job_id, "FAILED", error_message=str(exc))
