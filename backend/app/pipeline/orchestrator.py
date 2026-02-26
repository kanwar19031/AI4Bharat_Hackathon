from app.pipeline.deduplicator import deduplicate_products
from app.pipeline.frame_extractor import extract_frames
from app.pipeline.frame_filter import filter_frames
from app.pipeline.image_generator import generate_studio_images
from app.pipeline.ondc_formatter import format_ondc_catalog
from app.pipeline.product_detector import detect_products
from app.repo.catalogs_repo import CatalogsRepository
from app.repo.jobs_repo import JobsRepository
from app.services.bedrock_service import BedrockService


class PipelineOrchestrator:
    def __init__(
        self,
        jobs_repo: JobsRepository,
        catalogs_repo: CatalogsRepository,
        bedrock_service: BedrockService,
    ) -> None:
        self.jobs_repo = jobs_repo
        self.catalogs_repo = catalogs_repo
        self.bedrock_service = bedrock_service

    def run(self, video_id: str, job_id: str) -> None:
        try:
            self.jobs_repo.update_status(job_id, "EXTRACTING")
            frames = extract_frames(video_id)

            self.jobs_repo.update_status(job_id, "FILTERING")
            filtered_frames = filter_frames(frames)

            self.jobs_repo.update_status(job_id, "DETECTING")
            products = detect_products(filtered_frames, self.bedrock_service)

            self.jobs_repo.update_status(job_id, "DEDUPLICATING")
            unique_products = deduplicate_products(products)

            self.jobs_repo.update_status(job_id, "GENERATING")
            generated_products = generate_studio_images(unique_products, video_id, self.bedrock_service)

            self.jobs_repo.update_status(job_id, "FORMATTING")
            ondc_catalog = format_ondc_catalog(video_id, generated_products)

            catalog = self.catalogs_repo.create_catalog(
                job_id,
                products=generated_products,
                ondc_catalog=ondc_catalog,
            )
            self.jobs_repo.update_status(
                job_id,
                "COMPLETED",
                product_count=len(generated_products),
                catalog_id=catalog["catalog_id"],
            )
        except Exception as exc:
            self.jobs_repo.update_status(job_id, "FAILED", error_message=str(exc))

