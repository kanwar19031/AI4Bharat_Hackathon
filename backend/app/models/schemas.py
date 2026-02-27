from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PresignedUrlRequest(BaseModel):
    content_type: str = "video/mp4"
    file_size: int = Field(..., ge=1)


class PresignedUrlResponse(BaseModel):
    video_id: str
    job_id: str
    upload_url: str
    expires_in: int


class UseSampleResponse(BaseModel):
    """Response for use-sample: use a video from sample_video without upload."""

    video_id: str
    job_id: str
    message: str = "No upload needed. Call POST /jobs/{video_id}/process to run the pipeline."


class ProcessJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    video_id: str
    status: str
    product_count: int = 0
    error_message: str | None = None
    catalog_id: str | None = None
    updated_at: datetime


class CatalogProduct(BaseModel):
    product_id: str
    brand: str
    product_name: str
    net_weight: str | None = None
    variant: str | None = None
    price: float | None = None
    image_url: str | None = None


class CatalogResponse(BaseModel):
    catalog_id: str
    job_id: str
    status: str
    products: list[CatalogProduct]
    ondc_catalog: dict[str, Any]
    created_at: datetime


class UpdateCatalogRequest(BaseModel):
    products: list[CatalogProduct]


class UpdateCatalogResponse(BaseModel):
    status: str
    catalog_id: str

