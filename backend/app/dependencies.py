# app/dependencies.py
from __future__ import annotations

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

bedrock_service = BedrockService(settings)

# NOTE: do NOT create AWS clients unless enabled
_s3_service: S3Service | None = None
_dynamo_service: DynamoService | None = None
_pipeline_orchestrator: PipelineOrchestrator | None = None


def get_jobs_repo() -> JobsRepository:
    return jobs_repo


def get_catalogs_repo() -> CatalogsRepository:
    return catalogs_repo


def get_bedrock_service() -> BedrockService:
    return bedrock_service


def get_s3_service() -> S3Service | None:
    global _s3_service
    if not settings.use_aws_storage:
        return None
    if _s3_service is None:
        _s3_service = S3Service(settings)
    return _s3_service


def get_dynamo_service() -> DynamoService | None:
    global _dynamo_service
    if not settings.use_aws_db:
        return None
    if _dynamo_service is None:
        _dynamo_service = DynamoService(settings)
    return _dynamo_service


def get_pipeline_orchestrator() -> PipelineOrchestrator:
    global _pipeline_orchestrator
    if _pipeline_orchestrator is None:
        _pipeline_orchestrator = PipelineOrchestrator(
            jobs_repo=jobs_repo,
            catalogs_repo=catalogs_repo,
            bedrock_service=bedrock_service,
            s3_service=get_s3_service(),   # None in local mode
        )
    return _pipeline_orchestrator