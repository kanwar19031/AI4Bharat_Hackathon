from app.config.settings import get_settings
from app.pipeline.deduplicator import deduplicate_products
from app.pipeline.frame_extractor import extract_frames
from app.pipeline.frame_filter import filter_frames
from app.pipeline.image_generator import generate_studio_images
from app.pipeline.ondc_formatter import format_ondc_catalog
from app.pipeline.product_normalizer import normalize_catalog_products
from app.pipeline.product_detector import detect_products
from app.repo.interfaces import CatalogsRepo, JobsRepo
from app.services.bedrock_service import BedrockService
from app.services.s3_service import S3Service


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

    def run(self, video_id: str, job_id: str) -> None:
        try:
            self.jobs_repo.update_status(job_id, "EXTRACTING")
            frames = extract_frames(video_id)

            self.jobs_repo.update_status(job_id, "FILTERING")
            settings = get_settings()
            filtered_frames = filter_frames(
                frames,
                blur_threshold=settings.frame_blur_threshold,
                ssim_threshold=settings.frame_ssim_threshold,
                max_frames=settings.frame_max_frames,
            )

            self.jobs_repo.update_status(job_id, "DETECTING")
            products = detect_products(filtered_frames, self.bedrock_service, self.s3_service)

            self.jobs_repo.update_status(job_id, "DEDUPLICATING")
            unique_products = deduplicate_products(products)

            self.jobs_repo.update_status(job_id, "GENERATING")
            generated_products = generate_studio_images(unique_products, video_id, self.bedrock_service, self.s3_service)

            self.jobs_repo.update_status(job_id, "FORMATTING")
            normalized_products = normalize_catalog_products(generated_products)
            ondc_catalog = format_ondc_catalog(video_id, normalized_products)

            catalog = self.catalogs_repo.create_catalog(
                job_id,
                products=normalized_products,
                ondc_catalog=ondc_catalog,
            )
            self.jobs_repo.update_status(
                job_id,
                "COMPLETED",
                product_count=len(normalized_products),
                catalog_id=catalog["catalog_id"],
            )
        except Exception as exc:
            self.jobs_repo.update_status(job_id, "FAILED", error_message=str(exc))

