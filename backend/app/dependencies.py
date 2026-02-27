from app.config.settings import get_settings
from app.pipeline.orchestrator import PipelineOrchestrator
from app.repo.catalogs_repo import CatalogsRepository
from app.repo.jobs_repo import JobsRepository
from app.services.bedrock_service import BedrockService
from app.services.dynamo_service import DynamoService
from app.services.s3_service import S3Service

settings = get_settings()

jobs_repo = JobsRepository()
catalogs_repo = CatalogsRepository()

s3_service = S3Service(settings)
dynamo_service = DynamoService(settings)
bedrock_service = BedrockService(settings)

pipeline_orchestrator = PipelineOrchestrator(jobs_repo, catalogs_repo, bedrock_service)


def get_jobs_repo() -> JobsRepository:
    return jobs_repo


def get_catalogs_repo() -> CatalogsRepository:
    return catalogs_repo


def get_s3_service() -> S3Service:
    return s3_service


def get_dynamo_service() -> DynamoService:
    return dynamo_service


def get_bedrock_service() -> BedrockService:
    return bedrock_service


def get_pipeline_orchestrator() -> PipelineOrchestrator:
    return pipeline_orchestrator

